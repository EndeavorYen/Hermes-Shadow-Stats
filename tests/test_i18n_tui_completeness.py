"""Phase 6 W6.1 — i18n completeness for the TUI namespace.

Asserts that:
  * At least 20 ``TUI_``-prefixed keys exist (plan requirement)
  * Every ``TUI_`` key is defined in both ``en`` and ``zh-TW``
  * No value is blank (drift detection across translations)
"""

from __future__ import annotations

from hermes_shadow_stats import i18n


def _tui_keys(lang: str) -> set[str]:
    return {k for k in i18n.LABELS[lang] if k.startswith("TUI_")}


def test_tui_namespace_has_at_least_20_keys() -> None:
    en_keys = _tui_keys("en")
    assert len(en_keys) >= 20, (
        f"plan W6.1 requires ≥20 TUI_ keys; found {len(en_keys)}"
    )


def test_tui_keys_parity_en_zh_tw() -> None:
    en_keys = _tui_keys("en")
    zh_keys = _tui_keys("zh-TW")
    missing_in_zh = en_keys - zh_keys
    extra_in_zh = zh_keys - en_keys
    assert not missing_in_zh, f"zh-TW missing TUI_ keys: {sorted(missing_in_zh)}"
    assert not extra_in_zh, f"zh-TW has stray TUI_ keys not in en: {sorted(extra_in_zh)}"


def test_tui_translations_are_non_blank() -> None:
    for lang in ("en", "zh-TW"):
        for key in _tui_keys(lang):
            value = i18n.LABELS[lang][key]
            assert value and value.strip(), (
                f"empty translation: lang={lang} key={key}"
            )


def test_fallback_and_end_reason_keys_also_parity() -> None:
    """The Phase-3 vocabulary (fallback banners + end_reason labels) is also
    load-bearing. Keep en/zh-TW strictly aligned."""
    for family in ("fallback_", "end_reason_", "chronicle_", "diag_"):
        en_keys = {k for k in i18n.LABELS["en"] if k.startswith(family)}
        zh_keys = {k for k in i18n.LABELS["zh-TW"] if k.startswith(family)}
        assert en_keys == zh_keys, (
            f"{family}* parity broken: en-only={sorted(en_keys - zh_keys)} "
            f"zh-only={sorted(zh_keys - en_keys)}"
        )
