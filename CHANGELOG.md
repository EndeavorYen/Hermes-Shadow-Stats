# Changelog

## Unreleased (v0.2.0)

### Added
- **Interactive Textual TUI** with 8 RPG-themed tabs (Status / Equipment / Codex /
  Journal / Chronicle / Rituals / Effects / Diagnostics) backed by
  `~/.hermes/state.db` (read-only, schema v6+).
- **Detail drill-in** (DataTable + filter + sort) for the 4 data-dense tabs
  (Journal / Chronicle / Codex / Rituals), plus a `?` help overlay.
- **`--format tabs`** static export: all 8 tabs concatenated for non-TTY use.
- **`--theme`**, **`--tui` / `--no-tui`**, and **`--no-state-db`** CLI flags.
- **Fallback banner** in the Status tab when state.db is absent, schema-mismatched,
  or unreadable (three explicit `fallback_reason` states).
- 6 telemetry-driven attributes (Endurance / Precision / Resonance / Clarity /
  Reach / Tempo) + Focus / Overheat / Gold Status-tab vitals.
- End-reason histogram in the Diagnostics tab using the verified hermes-agent
  vocabulary (compression / cron_complete / user_exit / …).
- 32 golden-file snapshots (8 tabs × 2 languages × 2 telemetry states) + Pilot
  smoke tests for tab navigation, Detail drill-in, sort/filter, refresh-preserving
  selection, unknown-theme rejection, and Ctrl+C clean exit.
- `docs/theme-port.md` documents the HERMES_TEAL → TUI color mapping.

### Changed
- `--format ansi` remains byte-identical to v0.1.x (parity tested).
- Extended `ScanSummary` with toolset enumeration and unbounded session/skill lists
  (renderer enforces display limits per tab).
- `CharacterProfile` gained optional `telemetry`, `equipment`, and `fallback_reason`
  fields so renderers can degrade gracefully.

### Requires
- Python ≥3.10, `textual>=0.80,<2.0`.

## Initial release (v0.1.x)

### Added
- initial Hermes Shadow Stats MVP
- markdown, ANSI/ASCII, JSON, and SVG renderers
- richer artifact-derived growth heuristics
- Hermes plugin prototype wrapper
- preview export script for SVG/PNG generation
- GitHub Actions test workflow
- release checklist documentation

### Changed
- ANSI is now the primary CLI experience
- terminal panel styling now leans harder into Hermes-style pixel energy with Solo Leveling-inspired purple/cyan mood
- README rewritten to emphasize the ANSI-first product story
