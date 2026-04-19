"""Benchmark: ``build_telemetry_snapshot`` under realistic scale (plan W2.8).

Opt-in test — run with ``pytest -m benchmark`` to include.

Target: ≤ 300 ms on CI-class hardware at 1k sessions + 10k messages. If this
test starts failing on a particular machine, first retune the ``since_days``
window in ``state_db.read_top_tool_usage`` before weakening the budget.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from hermes_shadow_stats.state_db import COMPRESSION_END_REASON, StateDBReader


_SCHEMA_SQL = """
CREATE TABLE schema_version (version INTEGER NOT NULL);
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    model TEXT,
    parent_session_id TEXT,
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    estimated_cost_usd REAL,
    title TEXT
);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER
);
-- Reflect hermes-agent indexes (helps ORDER BY + GROUP BY performance).
CREATE INDEX idx_sessions_started ON sessions(started_at DESC);
CREATE INDEX idx_sessions_parent ON sessions(parent_session_id);
CREATE INDEX idx_messages_session ON messages(session_id, timestamp);
"""


def _seed_large(
    db_path: Path, n_sessions: int = 1000, n_messages: int = 10000
) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_SCHEMA_SQL)
        conn.execute("INSERT INTO schema_version (version) VALUES (6)")
        now = time.time()
        tools = ["Read", "Edit", "Bash", "Grep", "Glob", "Write", "TodoWrite"]

        sessions = []
        for i in range(n_sessions):
            end_reason = COMPRESSION_END_REASON if (i % 50 == 0) else "user_exit"
            model = "opus-4-7" if (i % 2 == 0) else "sonnet-4-6"
            parent = f"s{i - 1}" if (i % 10 != 0 and i > 0) else None
            sessions.append(
                (
                    f"s{i}",
                    "cli",
                    model,
                    parent,
                    now - (n_sessions - i) * 60.0,
                    now - (n_sessions - i) * 60.0 + 55.0,
                    end_reason,
                    20,
                    5,
                    200,
                    100,
                    50,
                    10,
                    5,
                    0.02,
                    f"session {i}",
                )
            )
        conn.executemany(
            "INSERT INTO sessions (id, source, model, parent_session_id, "
            "started_at, ended_at, end_reason, message_count, tool_call_count, "
            "input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, "
            "reasoning_tokens, estimated_cost_usd, title) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            sessions,
        )

        messages = []
        for i in range(n_messages):
            sid = f"s{i % n_sessions}"
            tool = tools[i % len(tools)] if (i % 3 == 0) else None
            messages.append((sid, "tool" if tool else "user", tool, now - i * 1.0))
        conn.executemany(
            "INSERT INTO messages (session_id, role, tool_name, timestamp) "
            "VALUES (?, ?, ?, ?)",
            messages,
        )
        conn.commit()
    finally:
        conn.close()


@pytest.mark.benchmark
def test_build_telemetry_snapshot_under_budget(tmp_path: Path) -> None:
    """10k messages + 1k sessions ⇒ snapshot build ≤ 300 ms."""
    home = tmp_path / "bench_home"
    home.mkdir()
    _seed_large(home / "state.db")

    reader = StateDBReader(home)
    # Warm up the connection so the timed call measures query cost only.
    reader._open_if_possible()  # noqa: SLF001 — controlled bench warm-up

    start = time.perf_counter()
    snap = reader.build_telemetry_snapshot()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    reader.close()

    assert snap.session_count == 1000
    assert snap.compression_events == 20  # every 50th of 1000
    assert len(snap.top_tools) > 0
    assert elapsed_ms <= 300.0, (
        f"build_telemetry_snapshot took {elapsed_ms:.1f}ms (budget 300ms). "
        "If a later Phase 3 change added per-row Python work, reduce since_days "
        "or add a tool_name index."
    )
