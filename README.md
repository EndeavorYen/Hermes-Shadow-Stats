# Hermes Shadow Stats

> **A status window for watching your agent awaken, adapt, and level up.**
>
> Hermes Shadow Stats scans persistent Hermes artifacts — memory, skills, sessions, plugins, cron traces — and reconstructs them as an ANSI-first hunter interface with pixel-terminal energy and Solo Leveling mood.

<p align="center">
  <a href="https://github.com/EndeavorYen/Hermes-Shadow-Stats/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/EndeavorYen/Hermes-Shadow-Stats/test.yml?style=for-the-badge&label=tests" alt="Tests"></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-MIT-7C3AED?style=for-the-badge" alt="License"></a>
  <img src="https://img.shields.io/badge/interface-ANSI%20first-06B6D4?style=for-the-badge" alt="ANSI first">
  <img src="https://img.shields.io/badge/vibe-leveling--up-8B5CF6?style=for-the-badge" alt="Leveling up vibe">
</p>

<p align="center">
  <strong>ANSI-first</strong> • <strong>CLI-native</strong> • <strong>read-only</strong> • <strong>artifact-driven</strong>
</p>

<p align="center">
  <img src="assets/ansi-preview.png" alt="Hermes Shadow Stats ANSI preview" width="100%">
</p>

Hermes Shadow Stats is built around one very specific fantasy:

**You are not just running an agent. You are watching it level up.**

Not as empty gamification, but as a visible growth loop:

- memories become adaptation
- skills become unlocked techniques
- sessions become battle history
- plugins become artifacts and summons
- cron becomes autonomous power

That slightly over-the-top, unapologetically cool feeling matters.

**The point is to make agent growth feel visible, dramatic, and a little bit chuunibyou — in the best possible way.**

Instead of patching Hermes core, this project reads the artifacts Hermes already leaves behind and turns them into a dramatic status interface you can drop directly into a terminal workflow.

That makes it:

- fast to iterate on
- easy to integrate with CLI tools
- fun to share in screenshots
- low-coupling with Hermes internals

---

## Hero demo

This preview is generated from the stable synthetic demo profile under `examples/demo-hermes-home/`.

```text
╭────────────────────────── HERMES SHADOW STATS ──────────────────────────╮
│                    status window // hunter interface                    │
╰──────────────────────────────────────────────────────────────────────────╯

▌ [ SYSTEM ] Gate resonance confirmed                                            ▌
▌ [ AWAKENING ] Candidate Phase           [ THREAT ] High-tier hunter            ▌
▌ NAME  Demo Hermes                       TITLE  Ops Summoner Initiate           ▌
▌ CLASS  Ops Summoner ☾                   RANK  Bronze ◈                         ▌
▌ LEVEL  5                                EXP  ▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱▱▱ 14/50        ▌
▌ TRAITS  First Persistent Memory, Plugin Tinkerer, Cron Tamer                   ▌
▌ ┤ ACHIEVEMENTS ├────────────────────────────────────────────────────────────   ▌
▌ ◆ First Persistent Memory                                                      ▌
▌ ◆ Plugin Tinkerer                                                              ▌
▌ ◆ Cron Tamer                                                                   ▌
```

This is the fantasy in one screen:

**your agent is not just running tasks — it is becoming stronger.**

---

## Why this is interesting

Most agent dashboards feel like telemetry.

Hermes Shadow Stats is trying to feel like **presence**.

Not just a monitor. Not just a parser. Not just a dashboard.

A status window.

It is also trying to capture a very specific Solo Leveling-adjacent feeling:

> the moment you realize the system is not static —
> your agent is learning, surviving, unlocking, and becoming something stronger.

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
- blue / deep-blue / gold terminal palette
- blocky pixel-ish frame language
- hunter-rank / system-window tone
- markdown + JSON are still available as utility outputs
- SVG exists, but the current design direction is **ANSI first**

---

## Why people might star this

### 1. It gives agents visible progression
- Level / EXP
- STR / INT / WIS / AGI / CHA / LUK
- rank, title, and primary class
- threat evaluation
- achievements / unlocked titles
- narrative summary

### 2. It turns real artifacts into fantasy signals
- memory depth
- skill codex size
- session tool-signatures
- session error scars
- plugin manifest / hook traces
- cron schedule glyphs

### 3. It is actually usable in a terminal
- ANSI status window renderer
- markdown renderer
- JSON export
- optional SVG renderer for side experiments
- CLI-friendly output
- read-only scanning approach

### 4. It can evolve into deeper Hermes integration
- Hermes plugin prototype wrapper
- future growth journal / progression history
- future profile comparisons / live overlays

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

In the best case, your first run should feel like this:

> "oh, this is not a metrics panel — this is my agent's awakening screen."

---

## Try it in 10 seconds

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

### Regenerate the README preview image

```bash
python scripts/render_readme_preview.py
```

### Generate stable example outputs from the synthetic demo profile

```bash
./scripts/generate_example_outputs.sh
```

---

## Why ANSI first?

Because this project wants to live **inside the CLI**, not beside it.

If the fantasy is "my agent is leveling up in front of me," then the terminal is the right stage.

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
- `scripts/render_readme_preview.py` — regenerate the social/README preview image

---

## Roadmap

### Near-term
- make the ANSI panel feel even more like a live leveling-up interface
- add stronger pixel motifs / badge language / class emblems
- tune class/title progression so growth feels more narratively satisfying
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
