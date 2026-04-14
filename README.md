# Hermes Shadow Stats

> **Turn a Hermes profile into a living hunter card.**
>
> Hermes Shadow Stats scans persistent Hermes artifacts — memory, skills, sessions, plugins, cron traces — and reconstructs them as an ANSI-first RPG status window with pixel-terminal energy and Solo Leveling mood.

<p align="center">
  <strong>ANSI-first</strong> • <strong>CLI-native</strong> • <strong>read-only</strong> • <strong>artifact-driven</strong>
</p>

Hermes Shadow Stats is built for one very specific fantasy:

**What if your agent felt like a protagonist with levels, titles, battle scars, and unlocked abilities?**

Instead of patching Hermes core, this project reads the artifacts Hermes already leaves behind and turns them into a dramatic status interface you can drop directly into a terminal workflow.

That makes it:

- fast to iterate on
- easy to integrate with CLI tools
- fun to share in screenshots
- low-coupling with Hermes internals

---

## Why this is interesting

Most agent dashboards feel like telemetry.

Hermes Shadow Stats is trying to feel like **presence**.

It maps:

- persistent memory → lore / adaptation
- skills → unlocked techniques
- sessions → battle history
- plugins → extensions / artifacts
- cron → autonomy / summons / rituals

into a terminal-native panel that feels closer to:

- Hermes Agent's pixel-ish CLI charm
- a dungeon system prompt
- a hunter status window from *Solo Leveling*

---

## Current vibe

- ANSI is the **main product**, not a side export
- purple / cyan / gold terminal palette
- blocky pixel-ish frame language
- hunter-rank / system-window tone
- markdown + JSON are still available as utility outputs
- SVG exists, but the current design direction is **ANSI first**

---

## Feature set

### Core
- ANSI status window renderer
- markdown renderer
- JSON export
- optional SVG renderer for side experiments

### Character derivation
- Level / EXP
- STR / INT / WIS / AGI / CHA / LUK
- rank, title, and primary class
- threat evaluation
- achievements / unlocked titles
- narrative summary

### Artifact signals
- memory depth
- skill codex size
- session tool-signatures
- session error scars
- plugin manifest / hook traces
- cron schedule glyphs

### Integration direction
- Hermes plugin prototype wrapper
- CLI-friendly output
- read-only scanning approach

---

## Quickstart

```bash
git clone https://github.com/EndeavorYen/Hermes-Shadow-Stats.git
cd Hermes-Shadow-Stats
python -m venv .venv
source .venv/bin/activate
pip install -e .
hermes-shadow-stats
```

If you already have Hermes installed locally, this will scan `~/.hermes` by default.

---

## Example outputs

### ANSI mode (primary)

```bash
hermes-shadow-stats
# or
hermes-shadow-stats --format ansi
```

### Markdown mode

```bash
hermes-shadow-stats --format markdown
```

### JSON mode

```bash
hermes-shadow-stats --format json
```

### Custom Hermes home / custom display name

```bash
hermes-shadow-stats --hermes-home ~/.hermes --name "Hermes of Ashes"
```

---

## Why ANSI first?

Because this project wants to live **inside the CLI**, not beside it.

ANSI gives us:

- direct fusion with terminal workflows
- immediate compatibility with Hermes-style interfaces
- shareable screenshots without needing a browser
- a tighter aesthetic loop between data and atmosphere

For now, the design priority is:

1. make the terminal panel feel great
2. make the terminal panel feel iconic
3. only then care about richer graphical outputs

So yes: SVG/PNG exist, but they are **not the hero path right now**.

---

## Design principles

- **Read-only first** — no Hermes core surgery required
- **Flavor over fake precision** — numbers are derived, not pretending to be authoritative telemetry
- **CLI-native** — terminal experience is the main target
- **Low coupling** — the scanner should survive Hermes evolution better than a deep integration would
- **Fun matters** — this should feel cool, not just correct

---

## How it works

Hermes Shadow Stats scans:

- `memories/MEMORY.md`
- `memories/USER.md`
- `skills/**/SKILL.md`
- `sessions/`
- `profiles/`
- `plugins/`
- `logs/`
- `cron/`

Then it derives:

- stats
- classes
- titles
- achievements
- threat level flavor
- summary text

without modifying Hermes itself.

---

## Hermes plugin prototype

A lightweight plugin prototype is included under:

- `hermes_plugin/`

See:
- `docs/plugin-prototype.md`

This is intentionally conservative for now. The current bet is:

**ship the ANSI interface first, then deepen integration later.**

---

## Documentation

- `docs/design.md` — system design and derivation logic
- `docs/plugin-prototype.md` — plugin wrapper notes
- `docs/release-checklist.md` — release polish checklist
- `examples/README.md` — sample output guidance
- `CHANGELOG.md` — project changes

---

## Roadmap

### Near-term
- make the ANSI panel more iconic
- add stronger pixel motifs / badge language / class emblems
- tune class/title progression
- add stable synthetic demo profiles for public examples

### Mid-term
- parse session structures more deeply instead of using only heuristics
- add growth journal / progression history
- improve plugin-mode UX

### Later
- portraits
- richer card variants
- comparative panels across profiles
- hook-based live progression

---

## Contributing / experimenting

If you like agent UX, terminal aesthetics, RPG systems, or weirdly emotional tooling, this repo is very open to experimentation.

Good contribution directions:

- better ANSI layout ideas
- stronger rank / class naming
- better achievement logic
- synthetic demo datasets
- plugin integration ideas
- terminal screenshot-worthy polish

---

## License

MIT — see `LICENSE`.
