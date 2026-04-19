"""Golden-file parity tests for renderer outputs.

Purpose: freeze the current ``render_ansi_panel`` behaviour BEFORE the Phase 1
per-tab refactor so that any byte-level change is caught immediately.

Regenerate fixtures with::

    UPDATE_GOLDEN=1 .venv/bin/python -m pytest tests/test_renderer_parity.py

Run without the env var to assert parity.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hermes_shadow_stats.renderer import (
    render_ansi_panel,
    render_json,
    render_markdown,
    render_svg_card,
)

from tests._fixtures import make_profile


GOLDEN_DIR = Path(__file__).parent / "fixtures" / "renderer_parity"


# Config matrix — stable banner/width combos we guarantee for v0.2.0.
ANSI_CONFIGS: list[tuple[str, str, str, int]] = [
    # name, lang, banner_mode, width
    ("default_en", "en", "auto", 78),
    ("wide_en", "en", "wide", 78),
    ("compact_en", "en", "compact", 62),
    ("minimal_en", "en", "minimal", 56),
    ("default_zh", "zh-TW", "auto", 78),
]


def _ansi_target(name: str) -> Path:
    return GOLDEN_DIR / f"{name}.ansi"


def _simple_target(name: str, suffix: str) -> Path:
    return GOLDEN_DIR / f"{name}.{suffix}"


def _compare_or_update(path: Path, rendered: str, label: str) -> None:
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        return
    if not path.exists():
        pytest.fail(
            f"Golden file missing: {path}\n"
            f"Run with UPDATE_GOLDEN=1 to create it."
        )
    expected = path.read_text(encoding="utf-8")
    if rendered != expected:
        # Show a small diff on failure.
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
        pytest.fail(f"{label} parity drift:\n" + "\n".join(head_diff))


@pytest.mark.parametrize("name,lang,banner_mode,width", ANSI_CONFIGS)
def test_ansi_panel_matches_golden(
    name: str, lang: str, banner_mode: str, width: int
) -> None:
    profile = make_profile(lang=lang)
    rendered = render_ansi_panel(profile, banner_mode=banner_mode, width=width)
    _compare_or_update(_ansi_target(name), rendered, f"ansi:{name}")


def test_markdown_matches_golden() -> None:
    profile = make_profile(lang="en")
    rendered = render_markdown(profile)
    _compare_or_update(_simple_target("default_en", "md"), rendered, "markdown:en")


def test_json_matches_golden() -> None:
    profile = make_profile(lang="en")
    rendered = render_json(profile)
    _compare_or_update(_simple_target("default_en", "json"), rendered, "json:en")


def test_svg_matches_golden() -> None:
    profile = make_profile(lang="en")
    rendered = render_svg_card(profile)
    _compare_or_update(_simple_target("default_en", "svg"), rendered, "svg:en")
