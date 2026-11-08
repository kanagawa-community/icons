# Contributing to Kanagawa icons

Thanks for helping. This port follows the
[Kanagawa community contributing guide](https://github.com/kanagawa-community/.github/blob/main/.github/CONTRIBUTING.md),
which explains conventional commits, the checks every pull request runs, and how
changes are reviewed. This page covers only what is specific to this port.

## Where to report what

- Problems with the icons, such as wrong colors, poor
  contrast, or a missing variant, belong in this repository's
  [issue tracker](https://github.com/kanagawa-community/icons/issues).
- Problems with the icon shapes themselves, or missing icons, belong with Kora.
  Start from the [project's page](https://github.com/bikass/kora).
- Changes to the colors themselves belong in the
  [shared palette](https://github.com/kanagawa-community/.github/blob/main/docs/PALETTE.md),
  not in this port. Open an issue in the
  [.github repository](https://github.com/kanagawa-community/.github/issues)
  so every port stays in step.

## Colors

Take colors from the shared [palette](https://github.com/kanagawa-community/.github/blob/main/docs/PALETTE.md)
and follow the [style guide](https://github.com/kanagawa-community/.github/blob/main/docs/STYLE-GUIDE.md).
Do not sample colors from screenshots or add new ones. Every change must work in
Wave, Dragon, and Lotus.

To read the colors from a script, use the machine-readable
[palette.json](https://raw.githubusercontent.com/kanagawa-community/.github/main/palette.json).

## Working on this port

`src/` is a copy of the `kora/` theme folder of the Kora icon theme from commit
[`e63a9e1`](https://github.com/bikass/kora/tree/e63a9e1b4f3b1f647b4cf9c64c1ece58ce45f75a).
Leave it unchanged so it can be updated from upstream: replace it with the new upstream
folder and regenerate.

`themes/` is generated. Do not edit it by hand. `scripts/generate.py` reads the shared
`palette.json` from a sibling checkout of the
[.github repository](https://github.com/kanagawa-community/.github) (or from a path given
as its first argument) and swaps every color in the SVGs outside `apps/` for a palette
role. Colors are sorted into hue families (`FAMILIES`, `GREYS`) and their lightness picks
the role. KDE's `ColorScheme-*` stylesheet colors use `SCHEME`. The script stops on any
color syntax it does not handle. After changing the rules, regenerate and commit the
result:

```sh
python3 scripts/generate.py
```

A pull request also runs the **Generated** check (`.github/workflows/generated.yml`). It
regenerates the files from the current shared palette and fails if anything differs, so
commit the regenerated files with your change. When the palette itself changes, the check
fails until someone regenerates.

To try a change, copy `themes/Kanagawa-Kora-Wave` to `~/.local/share/icons/` and pick it
in your icon settings. Restart applications that do not pick up the new icons.

The images in `assets/screenshots/` follow Kora's own preview: a row of apps, then
folders, file types, devices and status icons from `themes/`, on the variant's `ui.bg`.
Make one per variant, then
build the showcase and social preview with `scripts/finish-previews.sh` from the .github
repository. See the
[preview standard](https://github.com/kanagawa-community/.github/blob/main/docs/PREVIEWS.md).

## Pull requests

- Keep each pull request to one change, and include a screenshot of each variant
  it affects.
- Update the README when installation or usage changes.
