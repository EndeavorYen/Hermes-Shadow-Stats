# Project terminal output policy

This repo frequently produces medium-to-large terminal outputs from git, test runs, TUI rendering checks, and diagnostics.

Use `rtk` for high-output shell commands when it preserves task correctness, especially for:

- `git status`
- `git diff`
- test runners (`pytest`, `python -m pytest`, `npm test`, `pnpm test`, `cargo test`)
- directory listings (`ls`, `tree`)
- renderer or snapshot-style diagnostics where a condensed output is sufficient
- large file reads where compressed output is enough to reason correctly

Prefer raw commands instead of `rtk` when:

- the task requires exact, unfiltered output
- the command output is already small
- debugging depends on complete logs, stack traces, ANSI fidelity, or byte-for-byte output
- a parser, snapshot verifier, or script depends on raw stdout/stderr

Examples:

```bash
rtk git status
rtk git diff
rtk pytest -q
rtk ls .
```

Verification helpers:

```bash
rtk --version
rtk gain
which rtk
```
