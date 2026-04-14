#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

DEMO_HOME="$ROOT_DIR/examples/demo-hermes-home"
OUT_DIR="$ROOT_DIR/examples/generated"
mkdir -p "$OUT_DIR"

# shellcheck disable=SC1091
source .venv/bin/activate

hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format ansi > "$OUT_DIR/shadow-panel.ansi"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format markdown > "$OUT_DIR/shadow-panel.md"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format json > "$OUT_DIR/shadow-panel.json"
python "$ROOT_DIR/scripts/render_readme_preview.py"

echo "Generated example outputs in: $OUT_DIR"
