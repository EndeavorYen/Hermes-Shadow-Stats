"""Phase 6 W6.7 — refresh (`r` / F5) round-trip ≤ cold-start budget.

``action_refresh_snapshot`` re-runs the scanner + state.db pipeline and
re-renders all 8 tabs. The assertion is the same 1.5s state.db budget used
for cold start (see W4.6) — refresh should not regress further.

Gated behind ``@pytest.mark.benchmark`` so default CI runs stay fast.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest

from hermes_shadow_stats.tui import HERMES_TEAL, ShadowStatsApp
from hermes_shadow_stats.tui.app import load_profile

from tests.test_state_db_perf import _seed_large


def _run(coro):
    return asyncio.run(coro)


@pytest.mark.benchmark
def test_refresh_roundtrip_within_budget(tmp_path: Path) -> None:
    home = tmp_path / "refresh_home"
    home.mkdir()
    _seed_large(home / "state.db")

    profile = load_profile(home, lang="en", use_state_db=True)

    async def scenario() -> float:
        app = ShadowStatsApp(profile, lang="en", theme=HERMES_TEAL)
        async with app.run_test() as pilot:
            await pilot.pause()
            start = time.perf_counter()
            app.action_refresh_snapshot()
            await pilot.pause()
            return (time.perf_counter() - start) * 1000.0

    elapsed_ms = _run(scenario())
    assert elapsed_ms <= 1500.0, (
        f"refresh round-trip {elapsed_ms:.1f}ms exceeds 1500ms budget"
    )
