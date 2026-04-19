"""Phase 3 W3.3/W3.4 — golden snapshots for per-tab renderers WITH telemetry.

Matrix: 8 tabs × 2 langs = 16 snapshots under
``tests/fixtures/tab_output/telemetry/``.

Regenerate with::

    UPDATE_GOLDEN=1 .venv/bin/python -m pytest tests/test_tab_output_telemetry.py

Golden files are versioned and must move together with renderer changes.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hermes_shadow_stats.renderer import TAB_IDS, render_tab

from tests._fixtures import make_profile_with_telemetry


GOLDEN_DIR = Path(__file__).parent / "fixtures" / "tab_output" / "telemetry"


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
        pytest.fail(f"{label} telemetry golden drift:\n" + "\n".join(head_diff))


@pytest.mark.parametrize("lang", ["en", "zh-TW"])
@pytest.mark.parametrize("tab_id", TAB_IDS)
def test_tab_with_telemetry_matches_golden(tab_id: str, lang: str) -> None:
    profile = make_profile_with_telemetry(lang=lang)
    rendered = render_tab(tab_id, profile, width=78, lang=lang, telemetry=profile.telemetry)
    _compare_or_update(_target(tab_id, lang), rendered, f"tab:{tab_id}:{lang}")
