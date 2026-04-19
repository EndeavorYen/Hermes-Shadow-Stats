# Theme Port — Hermes Teal → TUI

Reference: [`hermes-agent/web/src/themes/presets.ts:11-44`](../../hermes-agent/web/src/themes/presets.ts).

## Mapping

| TUI field (`ThemePreset`) | Web preset field (`defaultTheme.colors.*`) | Notes |
|---|---|---|
| `background` | `background` | `#041C1C` |
| `foreground` | `foreground` | `#ffe6cb` |
| `accent` | `accent` | `#0c3838` |
| `success` | `success` | `#4ade80` |
| `warning` | `warning` | `#ffbd38` |
| `danger` | `destructive` | `#fb2c36` |
| `muted` | `muted-foreground` | `#8aaa9a` — port uses the foreground variant so low-contrast text stays legible in ANSI widgets |

## `color-mix(in srgb, ...)` quantisation

The web preset's `border`, `input`, and `ring` tokens use `color-mix(in srgb,
#ffe6cb 15%, transparent)`. Terminals don't compose colors against the
background the way CSS does, so the port drops alpha and falls back to the
underlying solid. The `ThemePreset` dataclass has no dedicated `border` field
in v0.2.0; borders use `accent` directly for contrast without extra tokens.

## Drift procedure

If the upstream preset changes and `tests/test_theme_parity.py` fails:

1. Diff the updated `presets.ts` against this document.
2. Update `EXPECTED_HEX` in the test.
3. Update `HERMES_TEAL` in `src/hermes_shadow_stats/tui/themes.py`.
4. Re-generate any affected golden snapshots via `UPDATE_GOLDEN=1 pytest`.
