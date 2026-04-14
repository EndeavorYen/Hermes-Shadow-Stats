#!/usr/bin/env bash
set -euo pipefail

# Export an SVG shadow card, then try to generate a PNG preview.
# macOS path: qlmanage
# Linux path: rsvg-convert or inkscape if available

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

SVG_OUT="${1:-artifacts/shadow-card.svg}"
PNG_OUT="${2:-artifacts/shadow-card.png}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
NAME="${NAME:-Hermes}"

mkdir -p "$(dirname "$SVG_OUT")"
mkdir -p "$(dirname "$PNG_OUT")"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -e . >/dev/null

hermes-shadow-stats --hermes-home "$HERMES_HOME" --name "$NAME" --format svg --output "$SVG_OUT" >/dev/null

echo "SVG written to: $SVG_OUT"

if command -v qlmanage >/dev/null 2>&1; then
  TMP_DIR="$(mktemp -d)"
  qlmanage -t -s 1600 -o "$TMP_DIR" "$SVG_OUT" >/dev/null 2>&1 || true
  GENERATED_PNG="$TMP_DIR/$(basename "$SVG_OUT").png"
  if [ -f "$GENERATED_PNG" ]; then
    cp "$GENERATED_PNG" "$PNG_OUT"
    echo "PNG written to: $PNG_OUT"
    exit 0
  fi
fi

if command -v rsvg-convert >/dev/null 2>&1; then
  rsvg-convert "$SVG_OUT" -o "$PNG_OUT"
  echo "PNG written to: $PNG_OUT"
  exit 0
fi

if command -v inkscape >/dev/null 2>&1; then
  inkscape "$SVG_OUT" --export-type=png --export-filename="$PNG_OUT" >/dev/null 2>&1
  echo "PNG written to: $PNG_OUT"
  exit 0
fi

echo "No PNG renderer found. SVG is ready at: $SVG_OUT"
