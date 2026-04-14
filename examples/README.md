# Examples

This directory contains the public-facing demo material for Hermes Shadow Stats.

## Included

- `demo-hermes-home/` — a stable synthetic Hermes home used for README/demo generation
- `generated/` — reproducible example outputs generated from the synthetic demo profile

## Generate stable examples

```bash
./scripts/generate_example_outputs.sh
```

This will produce:

- `generated/shadow-panel.ansi`
- `generated/shadow-panel.md`
- `generated/shadow-panel.json`
- `../assets/ansi-preview.png`

The goal is to keep public examples stable and screenshot-friendly without depending on your private real `~/.hermes` profile.
