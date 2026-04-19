"""Read-only telemetry reader for ``~/.hermes/state.db``.

Provides ``StateDBReader`` — a minimal, defensive wrapper around hermes-agent's
SQLite state store (schema v6). All queries enumerate whitelisted columns; any
error falls back to sentinel values so the renderer can degrade gracefully.

**Schema contract (Appendix A of ralplan-hermes-shadow-stats-tui-20260417.md):**

- Schema version lives in the ``schema_version`` table, NOT ``PRAGMA user_version``.
  Source: ``hermes-agent/hermes_state.py:34`` (``SCHEMA_VERSION = 6``) and
  ``hermes_state.py:259`` (``SELECT version FROM schema_version LIMIT 1``).
- Connection URI uses ``?mode=ro`` only; ``immutable=1`` is intentionally
  omitted because hermes-agent writes concurrently under WAL mode — marking
  the file immutable would enable SQLite's aggressive caching and cause
  ``SQLITE_CORRUPT`` or stale reads.

**end_reason vocabulary** (Appendix B): the ``"compression"`` literal is the
compression-event marker (``run_agent.py:7177``). No universal ``"error"``
value exists; error-adjacent diagnostics use ``ended_at IS NULL`` proxies.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from contextlib import AbstractContextManager
from pathlib import Path
from types import TracebackType

from .models import (
    CostSummary,
    SessionStats,
    TelemetrySnapshot,
    TokenUsage,
    ToolUsage,
)


_log = logging.getLogger(__name__)

# ``hermes-agent/hermes_state.py:34`` pins this; bump when hermes-agent ships
# a breaking schema migration.
MIN_SCHEMA_VERSION: int = 6

# Whitelisted sessions columns (Appendix A).
_SESSION_COLUMNS: tuple[str, ...] = (
    "id",
    "source",
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "reasoning_tokens",
    "message_count",
    "tool_call_count",
    "estimated_cost_usd",
    "started_at",
    "ended_at",
    "end_reason",
    "parent_session_id",
    "title",
)
_SESSION_SELECT = ", ".join(_SESSION_COLUMNS)

# The ``"compression"`` literal is the verified end_reason marker for
# compression-triggered session splits (ref: Appendix B).
COMPRESSION_END_REASON: str = "compression"


class StateDBReader(AbstractContextManager["StateDBReader"]):
    """Minimal read-only accessor for ``~/.hermes/state.db``.

    Every ``read_*`` method catches SQLite / value errors and returns a
    sentinel (empty list / zero-valued dataclass) so the renderer can degrade
    gracefully when the DB is absent, corrupt, or schema-mismatched.
    """

    def __init__(self, hermes_home: str | Path) -> None:
        self._home = Path(hermes_home).expanduser().resolve()
        self._db_path = self._home / "state.db"
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------ lifecycle

    def __enter__(self) -> "StateDBReader":
        self._open_if_possible()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error as err:  # pragma: no cover - defensive
                _log.debug("state.db close failed: %r", err)
            finally:
                self._conn = None

    @property
    def db_path(self) -> Path:
        return self._db_path

    def exists(self) -> bool:
        return self._db_path.is_file()

    def _open_if_possible(self) -> sqlite3.Connection | None:
        if self._conn is not None:
            return self._conn
        if not self.exists():
            return None
        # NOTE: ``mode=ro`` only; do NOT add ``immutable=1`` — hermes-agent
        # writes via WAL and immutable-cache semantics would corrupt reads.
        uri = f"file:{self._db_path}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True, timeout=1.0)
            conn.row_factory = sqlite3.Row
            self._conn = conn
            return conn
        except sqlite3.Error as err:
            _log.debug("state.db open failed (%s): %r", self._db_path, err)
            return None

    # ------------------------------------------------------------------ schema

    def schema_ok(self) -> tuple[bool, int | None]:
        """Return ``(ok, detected_version)`` using the ``schema_version`` table."""
        conn = self._open_if_possible()
        if conn is None:
            return (False, None)
        try:
            cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
            row = cursor.fetchone()
        except sqlite3.Error as err:
            _log.debug("schema_version query failed: %r", err)
            return (False, None)
        if row is None:
            return (False, None)
        try:
            detected = int(row[0])
        except (TypeError, ValueError) as err:
            _log.debug("schema_version row malformed: %r", err)
            return (False, None)
        return (detected >= MIN_SCHEMA_VERSION, detected)

    # ------------------------------------------------------------------ reads

    def read_recent_sessions(self, limit: int = 50) -> list[SessionStats]:
        """Return ``limit`` newest sessions sorted by ``started_at`` descending."""
        conn = self._open_if_possible()
        if conn is None:
            return []
        sql = (
            f"SELECT {_SESSION_SELECT} FROM sessions "
            "ORDER BY started_at DESC LIMIT ?"
        )
        try:
            rows = conn.execute(sql, (int(limit),)).fetchall()
        except sqlite3.Error as err:
            _log.debug("read_recent_sessions failed: %r", err)
            return []
        out: list[SessionStats] = []
        for row in rows:
            try:
                out.append(
                    SessionStats(
                        session_id=str(row["id"]),
                        source=str(row["source"] or ""),
                        model=(row["model"] if row["model"] is not None else None),
                        input_tokens=int(row["input_tokens"] or 0),
                        output_tokens=int(row["output_tokens"] or 0),
                        cache_read_tokens=int(row["cache_read_tokens"] or 0),
                        cache_write_tokens=int(row["cache_write_tokens"] or 0),
                        reasoning_tokens=int(row["reasoning_tokens"] or 0),
                        message_count=int(row["message_count"] or 0),
                        tool_call_count=int(row["tool_call_count"] or 0),
                        estimated_cost_usd=(
                            float(row["estimated_cost_usd"])
                            if row["estimated_cost_usd"] is not None
                            else None
                        ),
                        started_at=float(row["started_at"] or 0.0),
                        ended_at=(
                            float(row["ended_at"])
                            if row["ended_at"] is not None
                            else None
                        ),
                        end_reason=row["end_reason"],
                        parent_session_id=row["parent_session_id"],
                        title=row["title"],
                    )
                )
            except (TypeError, ValueError) as err:  # pragma: no cover - defensive
                _log.debug("skip malformed session row: %r", err)
                continue
        return out

    def read_lifetime_tokens(self) -> TokenUsage:
        conn = self._open_if_possible()
        if conn is None:
            return TokenUsage()
        sql = (
            "SELECT "
            "  COALESCE(SUM(input_tokens), 0) AS input, "
            "  COALESCE(SUM(output_tokens), 0) AS output, "
            "  COALESCE(SUM(cache_read_tokens), 0) AS cache_read, "
            "  COALESCE(SUM(cache_write_tokens), 0) AS cache_write, "
            "  COALESCE(SUM(reasoning_tokens), 0) AS reasoning "
            "FROM sessions"
        )
        try:
            row = conn.execute(sql).fetchone()
        except sqlite3.Error as err:
            _log.debug("read_lifetime_tokens failed: %r", err)
            return TokenUsage()
        if row is None:
            return TokenUsage()
        try:
            return TokenUsage(
                input_tokens=int(row["input"] or 0),
                output_tokens=int(row["output"] or 0),
                cache_read_tokens=int(row["cache_read"] or 0),
                cache_write_tokens=int(row["cache_write"] or 0),
                reasoning_tokens=int(row["reasoning"] or 0),
            )
        except (TypeError, ValueError):
            return TokenUsage()

    def read_cost_summary(self) -> CostSummary:
        conn = self._open_if_possible()
        if conn is None:
            return CostSummary()
        try:
            total_row = conn.execute(
                "SELECT COALESCE(SUM(estimated_cost_usd), 0) AS total FROM sessions"
            ).fetchone()
            per_model_rows = conn.execute(
                "SELECT model, SUM(estimated_cost_usd) AS c "
                "FROM sessions "
                "WHERE model IS NOT NULL AND estimated_cost_usd IS NOT NULL "
                "GROUP BY model"
            ).fetchall()
        except sqlite3.Error as err:
            _log.debug("read_cost_summary failed: %r", err)
            return CostSummary()
        try:
            total = float(total_row["total"] or 0.0) if total_row else 0.0
        except (TypeError, ValueError):
            total = 0.0
        per_model: dict[str, float] = {}
        for row in per_model_rows:
            try:
                per_model[str(row["model"])] = float(row["c"] or 0.0)
            except (TypeError, ValueError):
                continue
        return CostSummary(total_usd=total, per_model_usd=per_model)

    def read_top_tool_usage(
        self, limit: int = 10, since_days: int | None = 30
    ) -> list[ToolUsage]:
        """Aggregate ``messages.tool_name`` counts; top-N most-used tools.

        ``since_days`` limits the window (default 30) to keep 10k-row scans
        within the Phase-2 W2.8 benchmark budget. ``None`` removes the window.
        """
        conn = self._open_if_possible()
        if conn is None:
            return []
        params: list[float | int]
        if since_days is None:
            sql = (
                "SELECT tool_name, COUNT(*) AS n, MAX(timestamp) AS last "
                "FROM messages WHERE tool_name IS NOT NULL "
                "GROUP BY tool_name ORDER BY n DESC LIMIT ?"
            )
            params = [int(limit)]
        else:
            cutoff = time.time() - (int(since_days) * 86400)
            sql = (
                "SELECT tool_name, COUNT(*) AS n, MAX(timestamp) AS last "
                "FROM messages "
                "WHERE tool_name IS NOT NULL AND timestamp > ? "
                "GROUP BY tool_name ORDER BY n DESC LIMIT ?"
            )
            params = [cutoff, int(limit)]
        try:
            rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error as err:
            _log.debug("read_top_tool_usage failed: %r", err)
            return []
        out: list[ToolUsage] = []
        for row in rows:
            try:
                out.append(
                    ToolUsage(
                        tool_name=str(row["tool_name"]),
                        invocation_count=int(row["n"] or 0),
                        last_used_at=(
                            float(row["last"]) if row["last"] is not None else None
                        ),
                    )
                )
            except (TypeError, ValueError):
                continue
        return out

    def read_model_usage(self) -> dict[str, int]:
        conn = self._open_if_possible()
        if conn is None:
            return {}
        try:
            rows = conn.execute(
                "SELECT model, COUNT(*) AS n FROM sessions "
                "WHERE model IS NOT NULL GROUP BY model ORDER BY n DESC"
            ).fetchall()
        except sqlite3.Error as err:
            _log.debug("read_model_usage failed: %r", err)
            return {}
        out: dict[str, int] = {}
        for row in rows:
            try:
                out[str(row["model"])] = int(row["n"] or 0)
            except (TypeError, ValueError):
                continue
        return out

    def read_max_parent_chain_depth(self) -> int:
        """Compute max depth of ``parent_session_id`` chains (recursive CTE)."""
        conn = self._open_if_possible()
        if conn is None:
            return 0
        sql = (
            "WITH RECURSIVE chain(id, depth) AS ( "
            "  SELECT id, 1 FROM sessions WHERE parent_session_id IS NULL "
            "  UNION ALL "
            "  SELECT s.id, c.depth + 1 FROM sessions s "
            "    JOIN chain c ON s.parent_session_id = c.id "
            ") SELECT COALESCE(MAX(depth), 0) AS d FROM chain"
        )
        try:
            row = conn.execute(sql).fetchone()
        except sqlite3.Error as err:
            _log.debug("read_max_parent_chain_depth failed: %r", err)
            return 0
        try:
            return int((row["d"] if row else 0) or 0)
        except (TypeError, ValueError):
            return 0

    def count_compression_events(self) -> int:
        conn = self._open_if_possible()
        if conn is None:
            return 0
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM sessions WHERE end_reason = ?",
                (COMPRESSION_END_REASON,),
            ).fetchone()
        except sqlite3.Error as err:
            _log.debug("count_compression_events failed: %r", err)
            return 0
        try:
            return int((row["n"] if row else 0) or 0)
        except (TypeError, ValueError):
            return 0

    def count_sessions(self) -> int:
        conn = self._open_if_possible()
        if conn is None:
            return 0
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()
        except sqlite3.Error as err:
            _log.debug("count_sessions failed: %r", err)
            return 0
        try:
            return int((row["n"] if row else 0) or 0)
        except (TypeError, ValueError):
            return 0

    # ------------------------------------------------------------------ snapshot

    def build_telemetry_snapshot(
        self,
        *,
        recent_limit: int = 50,
        top_tools_limit: int = 10,
        since_days: int | None = 30,
    ) -> TelemetrySnapshot:
        """One-shot aggregate used by the renderer. Single connection open."""
        # Prime connection so individual methods reuse it.
        self._open_if_possible()
        return TelemetrySnapshot(
            recent_sessions=self.read_recent_sessions(recent_limit),
            lifetime_tokens=self.read_lifetime_tokens(),
            lifetime_cost=self.read_cost_summary(),
            top_tools=self.read_top_tool_usage(top_tools_limit, since_days),
            model_usage=self.read_model_usage(),
            parent_chain_max_depth=self.read_max_parent_chain_depth(),
            compression_events=self.count_compression_events(),
            session_count=self.count_sessions(),
        )


def load_telemetry(
    hermes_home: str | Path,
) -> tuple[TelemetrySnapshot | None, str | None]:
    """High-level helper: returns ``(snapshot, fallback_reason)``.

    ``fallback_reason`` values (mirrors ``CharacterProfile.fallback_reason``):
      * ``None``          → state.db ok, telemetry populated.
      * ``"no-state-db"`` → file absent.
      * ``"schema-fallback"`` → schema version < MIN_SCHEMA_VERSION.
      * ``"state-db-unreadable"`` → open/query failure (permission, corrupt).
    """
    reader = StateDBReader(hermes_home)
    if not reader.exists():
        return (None, "no-state-db")
    try:
        with reader:
            conn = reader._open_if_possible()  # noqa: SLF001 — intentional probe
            if conn is None:
                return (None, "state-db-unreadable")
            ok, _version = reader.schema_ok()
            if not ok:
                return (None, "schema-fallback")
            try:
                return (reader.build_telemetry_snapshot(), None)
            except sqlite3.Error as err:
                _log.debug("build_telemetry_snapshot failed: %r", err)
                return (None, "state-db-unreadable")
    except sqlite3.Error as err:
        _log.debug("load_telemetry unexpected error: %r", err)
        return (None, "state-db-unreadable")
