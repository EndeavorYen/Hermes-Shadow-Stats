#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

DEMO_HOME="$ROOT_DIR/examples/demo-hermes-home"
OUT_DIR="$ROOT_DIR/examples/generated"
mkdir -p "$OUT_DIR"

# shellcheck disable=SC1091
source .venv/bin/activate

hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format ansi --lang en > "$OUT_DIR/shadow-panel.ansi"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format markdown --lang en > "$OUT_DIR/shadow-panel.md"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "Demo Hermes" --format json --lang en > "$OUT_DIR/shadow-panel.json"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "影之 Hermes" --format ansi --lang zh-TW > "$OUT_DIR/shadow-panel.zh-TW.ansi"
hermes-shadow-stats --hermes-home "$DEMO_HOME" --name "影之 Hermes" --format markdown --lang zh-TW > "$OUT_DIR/shadow-panel.zh-TW.md"
python "$ROOT_DIR/scripts/render_readme_preview.py"

echo "Generated example outputs in: $OUT_DIR"
