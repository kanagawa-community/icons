#!/usr/bin/env python3
"""Build themes/Kanagawa-Kora-<Variant>/: the Kora icons (upstream/kora/) recolored by palette role.

Kora uses well over a thousand colors outside apps/, most of them gradient shades, so
colors are not listed one by one. Each is sorted into a hue family (or grey), and its
lightness picks one of that family's roles, ordered by how light they are in the variant.
KDE's ColorScheme-* stylesheet colors, which Plasma replaces at runtime anyway, get the
roles the Kanagawa color scheme gives those slots, so other desktops see the same colors.
apps/ (brand logos) is copied unchanged.

Usage: scripts/generate.py [path/to/palette.json]   (default: ../.github/palette.json)
"""
import json
import math
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "upstream" / "kora"
VARIANTS = ["wave", "dragon", "lotus"]
UNCHANGED = {"apps"}  # top-level folders copied as they are
SKIP = {"icon-theme.cache", "create-new-icon-theme.cache.sh"}  # the cache would be stale

# Same roles as kde/scripts/generate.py: ForegroundNormal, ForegroundActive and so on.
SCHEME = {
    "Text": "ui.fg",
    "Highlight": "syn.fun",
    "PositiveText": "diag.ok",
    "NeutralText": "diag.warning",
    "NegativeText": "diag.error",
}
# Hue families: (upper bound of the OKLCH hue in degrees, roles). Pink wraps round 0.
FAMILIES = [
    (15, ["syn.number"]),
    (45, ["vcs.removed", "diag.error", "syn.preproc", "syn.special3"]),
    (75, ["syn.constant", "diag.warning"]),
    (115, ["vcs.changed", "syn.operator", "syn.identifier"]),
    (165, ["vcs.added", "syn.string"]),
    (215, ["diag.hint", "syn.type"]),
    (280, ["ui.bg_search", "syn.fun", "term.bright_blue"]),  # in Dragon, its only clear blue
    (335, ["syn.statement", "ui.special", "syn.parameter"]),
    (360, ["syn.number"]),
]
# Per top-level folder, colors the families get wrong. Kora's folder back has the same
# lightness as the bottom of the front's gradient, so it would vanish into it.
EXACT = {"places": {"#0083d5": "diag.info"}}
# White labels on file types: whichever of these two roles stands out more from the icon's
# recolored body (its gradient stops), so they stay readable on light and dark accents.
# Flat symbols drawn in a shade of the body's own hue land on the body's color, so a flat
# fill within "near" lightness of the body gets the label role too.
LABEL = {"folders": {"mimetypes"}, "roles": ("ui.bg_m3", "ui.fg"), "near": 0.1}
# No ui.bg: in Lotus it is the lightest neutral, so white paper would match the window.
GREYS = ["ui.bg_m3", "ui.bg_p1", "ui.bg_p2", "ui.nontext", "syn.comment", "ui.fg_dim", "ui.fg"]
GREY_CHROMA = 0.04  # OKLCH chroma below this counts as grey
# Source lightness range spread over a family's roles; outside it clamps to the ends.
LIGHT = {"grey": (0.2, 0.95), "color": (0.45, 0.85)}

COLOR = re.compile(
    r"(\.ColorScheme-(\w+)\s*\{\s*color:\s*)#[0-9a-fA-F]{3,6}\b"
    r"|(?<!url\()(?<!href=\")#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b"  # not id references
    r"|rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)"
    r"|(?<=[:=\"])white\b"
)
# Anything left that looks like a color and is not one of the above stops the build.
UNKNOWN = re.compile(r"rgba\(|hsla?\(|#[0-9a-fA-F]{8}\b|(?:fill|stroke|stop-color|color)\s*[:=]\s*\"?(?!#|rgb\(|url\(|none|currentColor|inherit|transparent|white)[a-zA-Z]")


def oklch(hex_):
    """sRGB hex -> (L, C, hue in degrees), Björn Ottosson's OKLab."""
    rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720453 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def roles(variant):
    """Map each role to its hex; a role missing from the palette raises KeyError later."""
    return {role: color["hex"] for color in variant["colors"].values() for role in color["usage"]}


def role_for(hex_):
    L, C, h = oklch(hex_)
    if C < GREY_CHROMA:
        names, (lo, hi) = GREYS, LIGHT["grey"]
    else:
        names = next(r for bound, r in FAMILIES if h < bound)
        lo, hi = LIGHT["color"]
    i = round(min(max((L - lo) / (hi - lo), 0), 1) * (len(names) - 1))
    return names, i


class Recolor:
    def __init__(self, r):
        self.r = r
        self.palette = {h.lower() for h in r.values()}
        self.cache = {}

    def color(self, hex_, folder):
        if hex_ in EXACT.get(folder, {}):
            return self.r[EXACT[folder][hex_]]
        if hex_ not in self.cache:
            names, i = role_for(hex_)
            # order the family's roles by their lightness in this variant
            ordered = sorted({self.r[n] for n in names}, key=lambda x: oklch(x)[0])
            self.cache[hex_] = ordered[round(i * (len(ordered) - 1) / max(len(names) - 1, 1))]
        return self.cache[hex_]

    def __call__(self, text, path):
        folder = Path(path).parts[0]
        bad = UNKNOWN.search(text)
        if bad:
            raise SystemExit(f"{path}: unhandled color {bad[0]!r}; handle it in COLOR")

        def source(m):
            if m[0] == "white":
                return "#ffffff"
            if m[4]:
                return "#%02x%02x%02x" % (int(m[4]), int(m[5]), int(m[6]))
            h = m[3].lower()
            return "#" + (h if len(h) == 6 else "".join(c * 2 for c in h))

        def is_stop(m):
            return "stop-color" in text[max(m.start() - 12, 0):m.start()]

        label = avg = None
        if folder in LABEL["folders"]:
            found = [(source(m), is_stop(m)) for m in COLOR.finditer(text) if not m[2]]
            stops = [h for h, stop in found if stop]
            body = stops or [h for h, _ in found if h != "#ffffff"]
            if body:
                avg = sum(oklch(self.color(h, folder))[0] for h in body) / len(body)
                label = max((self.r[n] for n in LABEL["roles"]), key=lambda x: abs(oklch(x)[0] - avg))
            if not stops:
                avg = None  # no gradient body to tell symbols from

        def swap(m):
            if m[2]:
                return m[1] + self.r[SCHEME[m[2]]]
            h = source(m)
            if label and h == "#ffffff":
                return label
            c = self.color(h, folder)
            if avg is not None and not is_stop(m) and abs(oklch(c)[0] - avg) < LABEL["near"]:
                return label
            return c

        text = COLOR.sub(swap, text)
        stray = {h.lower() for h in re.findall(r"#[0-9a-fA-F]{6}\b", text)} - self.palette
        if stray:
            raise SystemExit(f"{path}: colors outside the palette: {sorted(stray)}")
        try:
            ET.fromstring(text.encode())
        except ET.ParseError as e:
            raise SystemExit(f"{path}: broken SVG after recoloring: {e}")
        return text


def build(name, recolor, out, dark):
    shutil.rmtree(out, ignore_errors=True)
    for path in sorted(SRC.rglob("*")):
        rel = path.relative_to(SRC)
        dest = out / rel
        if rel.name in SKIP:
            continue
        if path.is_symlink():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.symlink_to(path.readlink())
        elif path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        elif path.suffix == ".svg" and rel.parts[0] not in UNCHANGED:
            dest.write_text(recolor(path.read_text(), rel))
        else:
            shutil.copy2(path, dest)
    index = (SRC / "index.theme").read_text()
    index = re.sub(r"^Name=.*$", f"Name={name}", index, count=1, flags=re.M)
    index = re.sub(r"^Comment=.*$", "Comment=Kora icons in Kanagawa colors", index, count=1, flags=re.M)
    # Icons Kora lacks come from Breeze; GTK does not recolor them, so dark variants need Breeze Dark.
    index, n = re.subn(r"^Inherits=breeze,", f"Inherits={'breeze-dark' if dark else 'breeze'},", index, count=1, flags=re.M)
    if n != 1:
        raise SystemExit("upstream/kora/index.theme no longer inherits breeze first; update build()")
    (out / "index.theme").write_text(index)
    # The theme is installed on its own, so it carries the GPL text with it.
    shutil.copy(ROOT / "LICENSE", out / "LICENSE")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / ".github" / "palette.json"
    variants = json.loads(path.read_text())["variants"]
    for v in VARIANTS:
        out = ROOT / "themes" / f"Kanagawa-Kora-{v.capitalize()}"
        build(f"Kanagawa Kora {v.capitalize()}", Recolor(roles(variants[v])), out, variants[v]["appearance"] == "dark")
        print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
