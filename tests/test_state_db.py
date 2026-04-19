"""Fixture-based tests for ``StateDBReader`` (plan W2.7).

Five scenarios verified:
  1. Schema v6 OK                   → reads succeed, correct aggregates
  2. Schema v5 mismatch             → fallback + sentinels
  3. Missing state.db               → fallback + sentinels
  4. Corrupt state.db               → no crash, sentinels
  5. Schema v6 + extra column       → reads ignore the extra column

Plus required by plan Appendix A + Critic audit:
  * Read-only enforcement (INSERT attempt raises OperationalError)
  * Tool usage GROUP BY on ``messages.tool_name`` correctness
  * ``end_reason == "compression"`` counting (Appendix B vocabulary)
  * ``parent_session_id`` chain depth (recursive CTE)
  * ``load_telemetry`` returns correct fallback_reason per scenario
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

import pytest

from hermes_shadow_stats.state_db import (
    COMPRESSION_END_REASON,
    MIN_SCHEMA_VERSION,
    StateDBReader,
    load_telemetry,
)


# hermes-agent schema DDL (whitelisted columns only, subset is fine as long as
# v6 is advertised and columns we read exist).
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
"""


def _build_db(
    home: Path,
    *,
    schema_version: int = 6,
    extra_column: bool = False,
    corrupt: bool = False,
) -> Path:
    """Create a synthetic state.db under ``home``; return its path."""
    home.mkdir(parents=True, exist_ok=True)
    db_path = home / "state.db"
    if corrupt:
        db_path.write_bytes(b"this is not a sqlite file" * 20)
        return db_path
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_SCHEMA_SQL)
        if extra_column:
            conn.execute("ALTER TABLE sessions ADD COLUMN future_field TEXT DEFAULT ''")
        conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)", (schema_version,)
        )
        _seed_sample_data(conn)
        conn.commit()
    finally:
        conn.close()
    return db_path


def _seed_sample_data(conn: sqlite3.Connection) -> None:
    """Seed realistic data: 3 sessions chained, various end_reasons, 3 tools."""
    now = time.time()
    sessions = [
        # (id, source, model, parent, started, ended, end_reason,
        #  msgs, tools, in, out, cache_r, cache_w, reason, cost, title)
        ("s1", "cli", "opus-4-7", None, now - 3600, now - 3500, "user_exit",
         10, 4, 1000, 500, 200, 100, 50, 0.12, "session 1"),
        ("s2", "cli", "opus-4-7", "s1", now - 3000, now - 2800, COMPRESSION_END_REASON,
         8, 3, 800, 400, 800, 50, 20, 0.08, "compressed child"),
        ("s3", "cli", "sonnet-4-6", "s2", now - 2000, now - 1500, "cli_close",
         5, 2, 400, 200, 0, 0, 0, 0.02, "grandchild"),
    ]
    for s in sessions:
        conn.execute(
            "INSERT INTO sessions (id, source, model, parent_session_id, "
            "started_at, ended_at, end_reason, message_count, tool_call_count, "
            "input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, "
            "reasoning_tokens, estimated_cost_usd, title) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            s,
        )
    # Tool calls: Read x5, Edit x3, Bash x2 (total 10 matches tool_call_count sums).
    messages = []
    for _ in range(5):
        messages.append(("s1", "tool", "Read", now - 3550))
    for _ in range(3):
        messages.append(("s2", "tool", "Edit", now - 2900))
    for _ in range(2):
        messages.append(("s3", "tool", "Bash", now - 1750))
    # A message without a tool_name (should be ignored by GROUP BY).
    messages.append(("s1", "user", None, now - 3600))
    for m in messages:
        conn.execute(
            "INSERT INTO messages (session_id, role, tool_name, timestamp) "
            "VALUES (?, ?, ?, ?)",
            m,
        )


# --------------------------------------------------------------------------- fixtures


@pytest.fixture
def home_v6_ok(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_ok"
    _build_db(home, schema_version=6)
    return home


@pytest.fixture
def home_v5_mismatch(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_old"
    _build_db(home, schema_version=5)
    return home


@pytest.fixture
def home_missing(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_empty"
    home.mkdir(parents=True)
    # No state.db file.
    return home


@pytest.fixture
def home_corrupt(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_corrupt"
    _build_db(home, corrupt=True)
    return home


@pytest.fixture
def home_extra_col(tmp_path: Path) -> Path:
    home = tmp_path / "hermes_future"
    _build_db(home, schema_version=6, extra_column=True)
    return home


# --------------------------------------------------------------------------- schema


def test_schema_v6_ok(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        ok, ver = reader.schema_ok()
    assert ok is True
    assert ver == MIN_SCHEMA_VERSION


def test_schema_v5_fallback(home_v5_mismatch: Path) -> None:
    with StateDBReader(home_v5_mismatch) as reader:
        ok, ver = reader.schema_ok()
    assert ok is False
    assert ver == 5


def test_missing_db_returns_sentinels(home_missing: Path) -> None:
    reader = StateDBReader(home_missing)
    assert reader.exists() is False
    ok, ver = reader.schema_ok()
    assert (ok, ver) == (False, None)
    assert reader.read_recent_sessions() == []
    assert reader.build_telemetry_snapshot().session_count == 0


def test_corrupt_db_no_crash(home_corrupt: Path) -> None:
    reader = StateDBReader(home_corrupt)
    ok, _ver = reader.schema_ok()
    assert ok is False
    # Every read path must degrade to sentinels without raising.
    assert reader.read_recent_sessions() == []
    assert reader.read_lifetime_tokens().total == 0
    assert reader.read_cost_summary().total_usd == 0.0
    assert reader.read_top_tool_usage() == []


def test_extra_column_ignored(home_extra_col: Path) -> None:
    """An unknown sessions column must not break our whitelist-driven reads."""
    with StateDBReader(home_extra_col) as reader:
        ok, ver = reader.schema_ok()
        sessions = reader.read_recent_sessions()
    assert (ok, ver) == (True, 6)
    assert len(sessions) == 3  # seed data still readable


# --------------------------------------------------------------------------- reads


def test_recent_sessions_ordering(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        sessions = reader.read_recent_sessions(limit=10)
    assert [s.session_id for s in sessions] == ["s3", "s2", "s1"]  # newest first


def test_lifetime_tokens_aggregation(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        tokens = reader.read_lifetime_tokens()
    # Seed sums: input=1000+800+400, output=500+400+200, cache_r=200+800,
    # cache_w=100+50, reasoning=50+20.
    assert tokens.input_tokens == 2200
    assert tokens.output_tokens == 1100
    assert tokens.cache_read_tokens == 1000
    assert tokens.cache_write_tokens == 150
    assert tokens.reasoning_tokens == 70
    # cache_hit_rate = 1000 / (1000 + 2200) = 0.3125
    assert abs(tokens.cache_hit_rate - 0.3125) < 1e-6


def test_cost_summary_per_model(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        cost = reader.read_cost_summary()
    assert abs(cost.total_usd - 0.22) < 1e-6
    assert set(cost.per_model_usd) == {"opus-4-7", "sonnet-4-6"}
    assert abs(cost.per_model_usd["opus-4-7"] - 0.20) < 1e-6
    assert abs(cost.per_model_usd["sonnet-4-6"] - 0.02) < 1e-6


def test_top_tool_usage_group_by(home_v6_ok: Path) -> None:
    """Verify ``GROUP BY messages.tool_name`` correctness (plan orphan #3, #5)."""
    with StateDBReader(home_v6_ok) as reader:
        tools = reader.read_top_tool_usage(limit=10, since_days=None)
    assert [t.tool_name for t in tools] == ["Read", "Edit", "Bash"]
    assert [t.invocation_count for t in tools] == [5, 3, 2]
    # NULL tool_name rows must be excluded.
    assert all(t.tool_name is not None for t in tools)


def test_top_tool_usage_window(home_v6_ok: Path) -> None:
    """``since_days=0`` must drop all rows (timestamps older than cutoff)."""
    with StateDBReader(home_v6_ok) as reader:
        tools = reader.read_top_tool_usage(limit=10, since_days=0)
    assert tools == []


def test_model_usage_counts(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        usage = reader.read_model_usage()
    assert usage == {"opus-4-7": 2, "sonnet-4-6": 1}


def test_parent_chain_depth(home_v6_ok: Path) -> None:
    """s1 → s2 → s3 chain has depth 3."""
    with StateDBReader(home_v6_ok) as reader:
        depth = reader.read_max_parent_chain_depth()
    assert depth == 3


def test_compression_events_vocabulary(home_v6_ok: Path) -> None:
    """Appendix B: compression sessions have ``end_reason = 'compression'``."""
    with StateDBReader(home_v6_ok) as reader:
        count = reader.count_compression_events()
    assert count == 1  # s2 is the only compression event


def test_build_telemetry_snapshot(home_v6_ok: Path) -> None:
    with StateDBReader(home_v6_ok) as reader:
        snap = reader.build_telemetry_snapshot()
    assert snap.session_count == 3
    assert snap.parent_chain_max_depth == 3
    assert snap.compression_events == 1
    assert len(snap.top_tools) == 3
    assert len(snap.recent_sessions) == 3


# --------------------------------------------------------------------------- read-only


def test_read_only_enforcement(home_v6_ok: Path) -> None:
    """Appendix enforcement: INSERT through the reader's connection MUST fail.

    This exists so a future regression that accidentally grants write access
    is caught immediately.
    """
    reader = StateDBReader(home_v6_ok)
    conn = reader._open_if_possible()  # noqa: SLF001 — test probes private path
    assert conn is not None
    with pytest.raises(sqlite3.OperationalError):
        conn.execute(
            "INSERT INTO sessions (id, source, started_at) VALUES (?, ?, ?)",
            ("naughty", "test", 0.0),
        )
    reader.close()


# --------------------------------------------------------------------------- load_telemetry


def test_load_telemetry_success(home_v6_ok: Path) -> None:
    snap, reason = load_telemetry(home_v6_ok)
    assert reason is None
    assert snap is not None
    assert snap.session_count == 3


def test_load_telemetry_no_state_db(home_missing: Path) -> None:
    snap, reason = load_telemetry(home_missing)
    assert snap is None
    assert reason == "no-state-db"


def test_load_telemetry_schema_fallback(home_v5_mismatch: Path) -> None:
    snap, reason = load_telemetry(home_v5_mismatch)
    assert snap is None
    assert reason == "schema-fallback"


def test_load_telemetry_corrupt(home_corrupt: Path) -> None:
    snap, reason = load_telemetry(home_corrupt)
    assert snap is None
    # Either schema-fallback (can't read schema_version) or state-db-unreadable
    # is acceptable for a corrupt file; both mean "don't trust this".
    assert reason in {"schema-fallback", "state-db-unreadable"}
