"""Phase 4 W4.6 — data-acquisition perf budget.

Assertions separated from TUI paint so CI timing stays stable:
  * state.db path: ≤ 1.5 s at 1k sessions + 10k messages
  * file-scanner fallback: ≤ 500 ms on a typical-sized ~/.hermes

The benchmark harness reuses the synthetic seeder from
``tests/test_state_db_perf.py`` to avoid duplicating SQL.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from hermes_shadow_stats.tui.app import load_profile

from tests.test_state_db_perf import _seed_large


@pytest.mark.benchmark
def test_load_profile_with_state_db_under_budget(tmp_path: Path) -> None:
    home = tmp_path / "bench_home"
    home.mkdir()
    _seed_large(home / "state.db")
    # Touch a tiny skills dir so the scanner exercises its traversal paths.
    (home / "skills").mkdir()

    start = time.perf_counter()
    profile = load_profile(home, lang="en", use_state_db=True)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert profile.telemetry is not None, "state.db should populate telemetry"
    assert profile.fallback_reason is None
    assert elapsed_ms <= 1500.0, (
        f"load_profile(state_db=on) took {elapsed_ms:.1f}ms (budget 1500ms)."
    )


@pytest.mark.benchmark
def test_load_profile_fallback_under_budget(tmp_path: Path) -> None:
    home = tmp_path / "scan_home"
    home.mkdir()
    # Minimal scaffolding so the scanner touches all branches.
    (home / "memories").mkdir()
    (home / "skills").mkdir()
    (home / "sessions").mkdir()

    start = time.perf_counter()
    profile = load_profile(home, lang="en", use_state_db=False)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert profile.telemetry is None
    assert profile.fallback_reason == "no-state-db"
    assert elapsed_ms <= 500.0, (
        f"load_profile(state_db=off) took {elapsed_ms:.1f}ms (budget 500ms)."
    )
