"""Security tests: malicious state.db cannot smuggle ANSI sequences (Phase 4
validation SEV:MED).

A crafted ``sessions.model`` / ``messages.tool_name`` containing OSC, CSI
non-SGR, or cursor-movement escapes must be neutralised before it lands in
``--format ansi`` or ``--format tabs`` output. SGR colour codes are the only
escape sequence the renderer itself emits; everything else is attacker-owned
and must be stripped.
"""

from __future__ import annotations

import re

from hermes_shadow_stats.models import (
    CostSummary,
    Equipment,
    SessionStats,
    TelemetrySnapshot,
    TokenUsage,
    ToolUsage,
)
from hermes_shadow_stats.renderer import (
    _safe_text,
    render_chronicle_tab,
    render_equipment_tab,
    render_journal_tab,
)
from hermes_shadow_stats.stats import build_character_profile

from tests._fixtures import make_scan


# All these payloads should be 100% stripped by ``_safe_text``.
MALICIOUS_PAYLOADS = [
    "\x1b[?1049h",          # alternate-screen switch
    "\x1b]0;hijacked\x07",  # OSC set-window-title (BEL terminator)
    "\x1b]0;x\x1b\\",        # OSC set-window-title (ST terminator)
    "\x1b[2J\x1b[H",         # clear screen + home cursor
    "\x1b[6n",               # query cursor position
    "\x07\x07\x07",          # bell spam
    "safe\x1b[?25lhidden",  # cursor-hide in middle
]

# SGR colour sequences are deliberately PRESERVED (the renderer emits them).
ALLOWED_SGR = ["\x1b[0m", "\x1b[1;38;5;221m", "\x1b[38;5;69m\x1b[0m"]


def test_safe_text_strips_all_known_malicious_payloads() -> None:
    for payload in MALICIOUS_PAYLOADS:
        cleaned = _safe_text(payload)
        assert "\x1b" not in cleaned, (
            f"escape leaked through for payload={payload!r} → cleaned={cleaned!r}"
        )
        assert "\x07" not in cleaned
        assert "\x1b[" not in cleaned


def test_safe_text_preserves_benign_ascii() -> None:
    assert _safe_text("opus-4-7") == "opus-4-7"
    assert _safe_text("claude-sonnet-4-6") == "claude-sonnet-4-6"
    assert _safe_text("") == ""
    assert _safe_text(None) == "—"
    assert _safe_text(None, fallback="unknown") == "unknown"


def test_safe_text_preserves_cjk() -> None:
    # CJK characters must survive (Phase 0 spike verified CJK rendering).
    assert _safe_text("影子側寫") == "影子側寫"


def _malicious_telemetry() -> TelemetrySnapshot:
    bad_model = "\x1b]0;HACKED\x07opus-4-7"
    bad_tool = "\x1b[2JEdit"
    return TelemetrySnapshot(
        recent_sessions=[
            SessionStats(
                session_id="s0\x1b[?1049h",
                source="cli",
                model=bad_model,
                input_tokens=100,
                output_tokens=50,
                cache_read_tokens=10,
                cache_write_tokens=5,
                reasoning_tokens=0,
                message_count=3,
                tool_call_count=1,
                estimated_cost_usd=0.01,
                started_at=1_776_614_400.0,
                ended_at=1_776_614_460.0,
                end_reason="user_exit",
                parent_session_id=None,
                title=None,
            )
        ],
        lifetime_tokens=TokenUsage(
            input_tokens=100, output_tokens=50, cache_read_tokens=10
        ),
        lifetime_cost=CostSummary(
            total_usd=0.01, per_model_usd={bad_model: 0.01}
        ),
        top_tools=[
            ToolUsage(tool_name=bad_tool, invocation_count=5, last_used_at=None)
        ],
        model_usage={bad_model: 1},
        parent_chain_max_depth=1,
        compression_events=0,
        session_count=1,
    )


def _assert_no_malicious_escapes(rendered: str) -> None:
    # Every ESC byte in the output must be the start of an SGR colour code.
    for match in re.finditer(r"\x1b(.?)", rendered):
        nxt = match.group(1)
        # Only ``\x1b[`` starting a CSI m is allowed. We verify the whole CSI
        # ends with ``m`` by requiring every ``\x1b[...`` in the output matches
        # the SGR regex.
        assert nxt == "[", (
            f"non-CSI escape leaked: {match.group(0)!r} in output"
        )
    # All CSI sequences must be SGR (end in 'm').
    for csi in re.finditer(r"\x1b\[([^a-zA-Z]*)([a-zA-Z])", rendered):
        final_byte = csi.group(2)
        assert final_byte == "m", (
            f"non-SGR CSI sequence leaked: \\x1b[{csi.group(1)}{final_byte}"
        )
    # OSC / BEL / cursor-hide patterns must not appear.
    assert "\x07" not in rendered
    assert "\x1b]" not in rendered


def test_malicious_state_db_strings_do_not_reach_journal_output() -> None:
    telemetry = _malicious_telemetry()
    profile = build_character_profile(
        scan=make_scan(),
        name="Hermes",
        lang="en",
        telemetry=telemetry,
        fallback_reason=None,
    )
    out = render_journal_tab(profile, width=78, lang="en", telemetry=telemetry)
    _assert_no_malicious_escapes(out)
    # Sanity — benign portion of the model string survives.
    assert "opus-4-7" in out
    assert "HACKED" not in out.replace("hacked", "")  # OSC payload purged


def test_malicious_equipment_strings_do_not_reach_output() -> None:
    telemetry = _malicious_telemetry()
    equipment = Equipment(
        main_weapon=telemetry.recent_sessions[0].model,
        armor_slots=["\x1b[2Jplugin-a", "plugin-b"],
        trinkets=["\x07bellbeep"],
        hotbar=telemetry.top_tools,
    )
    profile = build_character_profile(
        scan=make_scan(),
        name="Hermes",
        lang="en",
        telemetry=telemetry,
        fallback_reason=None,
    )
    # Override equipment with a malicious one.
    from dataclasses import replace

    bad_profile = replace(profile, equipment=equipment)
    out = render_equipment_tab(bad_profile, width=78, lang="en", telemetry=telemetry)
    _assert_no_malicious_escapes(out)


def test_malicious_model_usage_does_not_reach_chronicle() -> None:
    telemetry = _malicious_telemetry()
    profile = build_character_profile(
        scan=make_scan(),
        name="Hermes",
        lang="en",
        telemetry=telemetry,
        fallback_reason=None,
    )
    out = render_chronicle_tab(profile, width=78, lang="en", telemetry=telemetry)
    _assert_no_malicious_escapes(out)


def test_safe_text_allows_sgr_passthrough_when_already_cleaned() -> None:
    """_safe_text is conservative — it strips anything escape-like including
    SGR. If a value was already rendered with SGR codes we should not be
    re-sanitising it. This test documents the invariant."""
    for sgr in ALLOWED_SGR:
        # SGR codes ARE stripped too — the helper is for untrusted strings
        # BEFORE they enter the ANSI pipeline. Callers that already hold
        # pre-styled strings must not re-apply _safe_text.
        assert "\x1b" not in _safe_text(sgr), (
            "_safe_text should strip SGR from pre-sanitisation inputs too"
        )
