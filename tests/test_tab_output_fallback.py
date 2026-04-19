"""Phase 3 W3.3/W3.4 — per-tab fallback golden snapshots (telemetry=None).

16 golden snapshots (8 tabs × 2 langs), generated with the scanner-only
profile. The Status tab is additionally asserted to display the fallback
banner for all three possible ``fallback_reason`` values.

Regenerate with::

    UPDATE_GOLDEN=1 .venv/bin/python -m pytest tests/test_tab_output_fallback.py
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hermes_shadow_stats import i18n
from hermes_shadow_stats.renderer import TAB_IDS, render_status_tab, render_tab

from tests._fixtures import make_fallback_profile, make_profile


GOLDEN_DIR = Path(__file__).parent / "fixtures" / "tab_output" / "fallback"


def _target(tab_id: str, lang: str) -> Path:
    lang_slug = lang.replace("-", "_")
    return GOLDEN_DIR / f"{tab_id}_{lang_slug}.ansi"


def _compare_or_update(path: Path, rendered: str, label: str) -> None:
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(f"Golden file missing: {path}\nRun with UPDATE_GOLDEN=1 to create it.")
    expected = path.read_text(encoding="utf-8")
    if rendered != expected:
        a = expected.splitlines()
        b = rendered.splitlines()
        head_diff: list[str] = []
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                head_diff.append(f"line {i}:\n  - {x!r}\n  + {y!r}")
                if len(head_diff) >= 3:
                    break
        if len(a) != len(b):
            head_diff.append(f"line count differs: expected={len(a)} got={len(b)}")
        pytest.fail(f"{label} fallback golden drift:\n" + "\n".join(head_diff))


@pytest.mark.parametrize("lang", ["en", "zh-TW"])
@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_tab_without_telemetry_matches_golden(tab_id: str, lang: str) -> None:
    """Fallback snapshot uses ``fallback_reason="no-state-db"`` so the Status
    banner is present in its golden; other tabs render as before."""
    profile = make_fallback_profile(lang=lang, fallback_reason="no-state-db")
    rendered = render_tab(tab_id, profile, width=78, lang=lang, telemetry=None)
    _compare_or_update(_target(tab_id, lang), rendered, f"tab:{tab_id}:{lang}")


@pytest.mark.parametrize(
    "reason,label_key",
    [
        ("no-state-db", "fallback_no_state_db"),
        ("schema-fallback", "fallback_schema"),
        ("state-db-unreadable", "fallback_unreadable"),
    ],
)
@pytest.mark.parametrize("lang", ["en", "zh-TW"])
def test_status_tab_shows_fallback_banner(reason: str, label_key: str, lang: str) -> None:
    """Critic orphan #2: fallback banner must surface in Status for every
    fallback_reason state, in every language."""
    profile = make_fallback_profile(lang=lang, fallback_reason=reason)
    out = render_status_tab(profile, width=78, lang=lang)
    assert i18n.t_label(lang, label_key) in out, (
        f"fallback banner for reason={reason!r} lang={lang!r} missing expected label"
    )
    assert i18n.t_label(lang, "fallback_banner_prefix") in out, (
        "fallback banner prefix tag missing"
    )


def test_absent_fallback_reason_omits_banner() -> None:
    """When ``fallback_reason is None`` (healthy path), no banner appears."""
    profile = make_profile(lang="en")
    # Sanity — base fixture has None fallback.
    assert profile.fallback_reason is None
    out = render_status_tab(profile, width=78, lang="en")
    for label_key in ("fallback_no_state_db", "fallback_schema", "fallback_unreadable"):
        assert i18n.t_label("en", label_key) not in out, (
            f"banner label {label_key} leaked into healthy status output"
        )
