# Hermes Shadow Stats — Design Notes

## Philosophy

Hermes Shadow Stats is an overlay, not a core rewrite.

The first version deliberately avoids tight coupling with Hermes internals. It reads persistent artifacts that already exist and reconstructs a game-like status panel from them.

This gives us:

- fast iteration
- no Hermes core patch requirement
- reasonable portability across profiles
- room to evolve later into hook-based telemetry

## Artifact model

The scanner currently treats a Hermes home directory as the source of truth.

### Read targets

- `memories/MEMORY.md`
- `memories/USER.md`
- `skills/**/SKILL.md`
- `sessions/`
- `profiles/`
- `plugins/`
- `logs/`
- `cron/`

### Why these files

They are durable and semantically meaningful:

- memories imply long-term learning and adaptation
- skills imply unlocked capabilities
- sessions imply battle history / operational mileage
- plugins imply extension and customization power
- cron implies autonomous behavior
- profiles imply multi-form or alternate loadout behavior

## Derived RPG fields

### Level / EXP

EXP is derived from weighted artifact counts plus lightweight content signals.

Current high-level signals:

- skills contribute heavily
- user memory and internal memory contribute to wisdom-like growth
- sessions contribute to battle experience
- plugin hooks and manifests contribute to extension/mastery flavor
- cron schedule traces contribute to autonomy flavor
- skill-domain variety gives extra bonus for range
- session error traces slightly reduce total EXP to reflect battle scars

This is intentionally heuristic.

### Deep signals

The scanner now derives extra content-based signals:

- `memory_lines`
- `skill_words`
- `session_tool_mentions`
- `session_error_mentions`
- `plugin_manifest_count`
- `plugin_hook_mentions`
- `cron_schedule_mentions`

These are used to improve title, achievement, threat, and stat derivation.

### Base attributes

- `STR`: execution pressure, automation, plugin + cron + profile footprint
- `INT`: skill count, domain spread, codex size
- `WIS`: persistent memory depth
- `AGI`: breadth plus session-driven operational tempo
- `CHA`: user-profile understanding, profile flexibility, plugin sociality
- `LUK`: a light synthetic stat influenced by variety, extension behavior, and scars survived

### Primary class

Primary class is inferred from dominant skill domains plus a few override rules.

Examples:

- `software-development` -> `Toolsmith`
- `github` -> `Code Alchemist`
- `devops` -> `Ops Summoner`
- `research` -> `Research Ranger`
- `note-taking` -> `Memory Weaver`
- `mlops` -> `Model Hunter`
- `autonomous-ai-agents` -> `Shadow Commander`

Fallbacks:

- plugin-heavy, skill-rich profile -> `Shadow Commander`
- high memory depth -> `Memory Weaver`
- wide domain spread -> `Adaptive Agent`
- otherwise -> `Hunter Candidate`

### Rank

Current tiers:

- Bronze
- Silver
- Gold
- Mythic

These are still level-based for now.

### Title

Title is generated from:

- primary class
- rank
- progression suffix
- some class-specific override rules

Examples:

- `Toolsmith Initiate`
- `Research Ranger Pathfinder`
- `Shadow Commander System Tactician`
- `Memory Weaver Archive Sovereign`

### Threat evaluation

This is pure flavor text. It compresses a few higher-order signals into a readable vibe string, such as:

- `Rookie presence`
- `High-tier hunter`
- `S-rank awakening`
- `Monarch-class anomaly`

### Achievements

Achievements are unlocked from thresholds and cross-signals.

Examples:

- `First Persistent Memory`
- `Skill Archivist`
- `Skill Tree Unlocked`
- `Hook Whisperer`
- `Toolchain Berserker`
- `Scheduler Pact`
- `System Overlord`

## Output modes

### Markdown

Primary output. Optimized for:

- Slack
- GitHub issues
- README pasting
- quick CLI inspection

### ASCII

Secondary output. Optimized for:

- terminal screenshots
- more game-console-like vibe
- quick status peeks

### JSON

Machine-friendly export for future:

- web UI
- SVG/image rendering
- dashboards
- plugin wrappers

## Plugin wrapper

This repo now includes a prototype Hermes plugin wrapper in `hermes_plugin/`.

Its current role is modest:

- expose a Hermes CLI command
- call the scanner / builder / renderer
- prove that plugin integration is viable without a Hermes core patch

## Future roadmap

### Phase 1.5

- add compact and badge modes
- tune rank and title progression
- parse more structured data from sessions and logs

### Phase 2

- optional Hermes plugin wrapper with better UX
- command integration
- hook-based growth journal
- incremental stat updates per session

### Phase 3

- visual card renderer
- emblem and portrait generation
- history / timeline view
- comparative panels across profiles

## Non-goals for now

- exact telemetry
- hard dependency on Hermes internals
- schema stability guarantees
- fully balanced RPG math

The goal is to be expressive, legible, and fun first.
