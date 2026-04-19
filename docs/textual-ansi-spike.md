# Textual ANSI Rendering Spike (Phase 0)

Spike executed per `.omc/plans/ralplan-hermes-shadow-stats-tui-20260417.md` Phase 0.

## Decision

**ADOPT Primitive B: wrap per-tab ANSI strings via `Static(Text.from_ansi(s))`.**

## Compatibility Matrix

| Verdict | Primitive | Escapes | Styles | Box glyphs | CJK |
| --- | --- | --- | --- | --- | --- |
| FAIL | `Static(s, markup=False)` | literal | 62 | OK | OK |
| PASS | `Static(Text.from_ansi(s))` | consumed | 14 | OK | OK |

## Textual smoke test

A (raw str): mounted OK, widget=Static | B (Text.from_ansi): mounted OK, widget=Static

## Terminal environment

| Variable | Value |
| --- | --- |
| TERM | `unknown` |
| TERM_PROGRAM | `unknown` |
| TMUX active | `no` |
| COLORTERM | `unspec` |

## Implication for the plan

Primitive B (`Static(Text.from_ansi(s))`) is the chosen widget wrapper. Per-tab render functions continue returning `str` (ANSI strings) — the TUI layer wraps each string via `Text.from_ansi` before mounting it in a `Static` widget. This matches Option A of the plan's ADR with a minor refinement (Option B-bounded is not required because Primitive B works as the primary, not a fallback).

Primitive A is rejected: Rich's `Text` constructor emits ANSI escapes as literal characters in the output, so styling, box glyphs, and CJK width break unless explicitly pre-parsed.

## Primitive A raw sample (first 160 rendered chars)

```
[1;38;5;69m╔════ HEADER ════╗[0m / [38;5;221m*[0m plain  [1;38;5;203mBOLD-RED[0m  [2;38;5;245mdim-gray[0m / [38;5;117m影狩人・等級[0m / [38;5;111m╞══ section ═══
```

## Primitive B raw sample (first 160 rendered chars)

```
╔════ HEADER ════╗ / * plain  BOLD-RED  dim-gray / 影狩人・等級 / ╞══ section ═══╡ / ╰─────────────╯
```
