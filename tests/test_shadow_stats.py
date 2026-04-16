from __future__ import annotations

from pathlib import Path

from hermes_shadow_stats import i18n
from hermes_shadow_stats.renderer import render_ansi_panel, render_markdown, render_svg_card
from hermes_shadow_stats.scanner import scan_hermes_home
from hermes_shadow_stats.stats import build_character_profile


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _seed_home(tmp_path: Path) -> Path:
    home = tmp_path / ".hermes"
    write(home / "memories" / "MEMORY.md", "- learned github auth\n§\n- fixed plugin wiring\n")
    write(home / "memories" / "USER.md", "- prefers concise writing\n")
    write(home / "skills" / "github" / "repo-management" / "SKILL.md", "# skill\nregister_hook post_tool_call\n")
    write(home / "skills" / "research" / "blogwatcher" / "SKILL.md", "# skill\n")
    write(home / "sessions" / "2026-04-14.json", '{"tool":"terminal","status":"error"}')
    write(home / "profiles" / "coder" / "config.yaml", "model: x\n")
    write(home / "plugins" / "shadow" / "plugin.yaml", "name: shadow\n")
    write(home / "plugins" / "shadow" / "__init__.py", "def register_hook():\n    pass\n")
    write(home / "cron" / "jobs.json", '{"schedule":"0 9 * * *","repeat":1}')
    return home


def test_scan_and_render_english(tmp_path: Path) -> None:
    home = _seed_home(tmp_path)

    scan = scan_hermes_home(home)
    profile = build_character_profile(scan, name="Hermes", lang="en")
    md = render_markdown(profile)
    ansi_panel = render_ansi_panel(profile)
    compact = render_ansi_panel(profile, banner_mode="compact", width=62)
    minimal = render_ansi_panel(profile, banner_mode="minimal", width=56)
    svg = render_svg_card(profile)

    assert scan.memory_entries == 3
    assert scan.user_entries == 1
    assert scan.skill_count == 2
    assert scan.activity.session_tool_mentions >= 1
    assert scan.activity.session_error_mentions >= 1
    assert scan.activity.plugin_manifest_count == 1
    assert scan.activity.plugin_hook_mentions >= 1
    assert scan.activity.cron_schedule_mentions >= 1
    assert scan.plugin_names == ["shadow"]

    assert profile.lang == "en"
    assert profile.primary_class_id
    assert profile.rank_id in {"bronze", "silver", "gold", "mythic"}

    assert "# HERMES SHADOW PROFILE" in md
    assert "## VITALS" in md
    assert "**STR**" in md
    assert "## EQUIPMENT" in md
    assert "## ACTIVE BUFFS" in md
    assert profile.primary_class in md
    assert profile.title in md

    assert "HERMES SHADOW PROFILE" in ansi_panel
    assert "persistent archive" in ansi_panel
    assert "\x1b[" in ansi_panel
    assert "VITALS" in ansi_panel
    assert "ATTRIBUTES" in ansi_panel
    assert "EQUIPMENT" in ansi_panel
    assert "DISCIPLINES" in ansi_panel
    assert "ACTIVE BUFFS" in ansi_panel
    assert "FIELD REPORT" in ansi_panel
    assert "ACHIEVEMENTS" in ansi_panel
    assert "REALM" in ansi_panel
    assert "PROFILE" in ansi_panel
    assert "██" not in ansi_panel  # pixel logo retired

    assert profile.primary_class in compact
    assert profile.primary_class in minimal

    assert svg.startswith("<svg")
    assert profile.title in svg


def test_render_zh_tw(tmp_path: Path) -> None:
    home = _seed_home(tmp_path)
    scan = scan_hermes_home(home)
    profile = build_character_profile(scan, name="影之 Hermes", lang="zh-TW")

    ansi_panel = render_ansi_panel(profile)
    md = render_markdown(profile)

    assert profile.lang == "zh-TW"
    assert "影子側寫" in ansi_panel
    assert "生命指標" in ansi_panel
    assert "屬性矩陣" in ansi_panel
    assert "裝備欄" in ansi_panel
    assert "啟動增益" in ansi_panel
    assert "戰場報告" in ansi_panel
    assert "成就紋章" in ansi_panel
    assert "領域" in ansi_panel
    assert "影子檔案" in ansi_panel

    assert "影子側寫" in md
    assert profile.primary_class in md
    assert profile.title in md
    assert "技藝" in md or "領域" in md


def test_lang_normalization() -> None:
    assert i18n.normalize_lang("en") == "en"
    assert i18n.normalize_lang("zh-TW") == "zh-TW"
    assert i18n.normalize_lang("zh_TW") == "zh-TW"
    assert i18n.normalize_lang(None) == "en"
    assert i18n.normalize_lang("xx-YY") == "en"
