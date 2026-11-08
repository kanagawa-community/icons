#!/usr/bin/env bash
# Install the Kanagawa themes for icons: every variant, or only the ones named.
# ./uninstall.sh takes the same arguments and removes them again.
#
# Usage: ./install.sh [all|wave|dragon|lotus ...]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
data="${XDG_DATA_HOME:-$HOME/.local/share}"
cap() { case "$1" in wave) echo Wave ;; dragon) echo Dragon ;; lotus) echo Lotus ;; esac; }
# Print "<file in this repository>\t<folder it goes in>" for one variant.
items() { printf "themes/Kanagawa-Kora-%s\t%s\n" "$(cap "$1")" "$data/icons"; }
# GTK loads icons faster with a cache; skip it quietly when the tool is missing.
after() {
  [[ "$uninstall" == false ]] && command -v gtk-update-icon-cache >/dev/null || return 0
  for v in $selected; do gtk-update-icon-cache -qf "$data/icons/Kanagawa-Kora-$(cap "$v")" || true; done
}

uninstall=false
if [[ "${1:-}" == --uninstall ]]; then
  uninstall=true
  shift
fi
selected=""
add() { case " $selected " in *" $1 "*) ;; *) selected="$selected $1" ;; esac; }
for arg in "${@:-all}"; do
  case "$arg" in
    all) add wave; add dragon; add lotus ;;
    wave | dragon | lotus) add "$arg" ;;
    *) echo "usage: $0 [all|wave|dragon|lotus ...]" >&2; exit 2 ;;
  esac
done

for v in $selected; do
  # Remove first, so a reinstall drops files the repository no longer has.
  while IFS=$'\t' read -r src dir; do
    rm -rf "${dir:?}/$(basename "$src")"
    if [[ "$uninstall" == false ]]; then
      mkdir -p "$dir"
      cp -R "$src" "$dir/"
    fi
  done < <(items "$v")
  [[ "$v" == shared ]] && continue
  if [[ "$uninstall" == true ]]; then echo "Removed kanagawa-$v"; else echo "Installed kanagawa-$v"; fi
done
after
