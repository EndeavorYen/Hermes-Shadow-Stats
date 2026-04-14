# Hermes Shadow Stats

A lightweight RPG-style overlay for Hermes Agent.

Hermes Shadow Stats treats a Hermes home/profile as a persistent character save file: memories, skills, profiles, sessions, plugins, and automations are scanned and converted into a readable status panel with Solo Leveling flavor.

## What this is

- read-only
- artifact-driven
- low-coupling with Hermes core
- intentionally game-like instead of pretending to be exact telemetry

## Current feature set

- markdown status-window rendering
- ASCII panel mode
- JSON export
- richer growth heuristics from artifact content, not just file counts
- Hermes plugin prototype wrapper

## MVP goals

- Read Hermes persistent artifacts without modifying Hermes core
- Derive RPG-style stats from real files
- Render a markdown character sheet with status-window flavor
- Support custom Hermes home/profile paths
- Keep JSON export available for future UI work

## Current scanned sources

- `memories/MEMORY.md`
- `memories/USER.md`
- `skills/**/SKILL.md`
- `sessions/`
- `profiles/`
- `plugins/`
- `logs/`
- `cron/`

## Current derived outputs

- Level / EXP
- STR / INT / WIS / AGI / CHA / LUK
- rank, title, and primary class guess
- threat evaluation flavor text
- achievements / titles unlocked
- deep signals from session traces, plugin hooks, and codex size
- markdown panel
- ASCII panel
- JSON export

## Install

```bash
cd ~/Code/Hermes-Shadow-Stats
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

Default Hermes home (`~/.hermes`):

```bash
hermes-shadow-stats
```

ASCII mode:

```bash
hermes-shadow-stats --format ascii
```

JSON mode:

```bash
hermes-shadow-stats --format json
```

Custom Hermes home:

```bash
hermes-shadow-stats --hermes-home ~/.hermes
```

Custom name:

```bash
hermes-shadow-stats --name "Hermes of Ashes"
```

## Example

```md
# Hermes Shadow Stats

> The system has acknowledged this entity.

## 🟪 Status Window
- **Name**: Hermes
- **Title**: Model Hunter Archive Sovereign
- **Class**: Model Hunter
- **Rank**: Mythic
- **Threat Evaluation**: Monarch-class anomaly
- **Level**: 44
- **EXP Gauge**: `█████░░░░░░░░░░░` 17/50 _(total: 2167)_

## Base Attributes
- **STR** 20  `■■■■■■■■■■`
- **INT** 20  `■■■■■■■■■■`
- **WIS** 11  `■■■■■■□□□□`
- **AGI** 20  `■■■■■■■■■■`
- **CHA** 11  `■■■■■■□□□□`
- **LUK** 15  `■■■■■■■■□□`
```

## Hermes plugin prototype

A prototype wrapper is included in `hermes_plugin/`.

See:
- `docs/plugin-prototype.md`

## Design notes

This project prefers flavor over fake precision.

- numbers are derived estimates, not telemetry truth
- classes and ranks are intended to feel like lore
- the scanner is artifact-driven and read-only
- output should be fun enough to share in chat or paste into issues

## Documentation

- `docs/design.md` — field design, derivation logic, and future direction
- `docs/plugin-prototype.md` — Hermes plugin wrapper sketch

## Suggested next steps

- parse session structures more deeply instead of keyword heuristics
- add themed badges / emblem mode / SVG card output
- add live hook-based progression journal
- package plugin installation flow more cleanly
