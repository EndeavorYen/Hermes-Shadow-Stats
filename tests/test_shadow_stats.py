from __future__ import annotations

from pathlib import Path

from hermes_shadow_stats.renderer import render_ansi_panel, render_markdown, render_svg_card
from hermes_shadow_stats.scanner import scan_hermes_home
from hermes_shadow_stats.stats import build_character_profile


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_scan_and_render(tmp_path: Path) -> None:
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

    scan = scan_hermes_home(home)
    profile = build_character_profile(scan, name="Hermes")
    panel = render_markdown(profile)
    ansi_panel = render_ansi_panel(profile)
    compact_panel = render_ansi_panel(profile, banner_mode="compact", width=62)
    minimal_panel = render_ansi_panel(profile, banner_mode="minimal", width=56)
    svg = render_svg_card(profile)

    assert scan.memory_entries == 3
    assert scan.user_entries == 1
    assert scan.skill_count == 2
    assert scan.activity.session_tool_mentions >= 1
    assert scan.activity.session_error_mentions >= 1
    assert scan.activity.plugin_manifest_count == 1
    assert scan.activity.plugin_hook_mentions >= 1
    assert scan.activity.cron_schedule_mentions >= 1
    assert "# Hermes Shadow Stats" in panel
    assert "## Deep Signals" in panel
    assert "The system has acknowledged this entity." in panel
    assert "**Threat Evaluation**:" in panel
    assert "**STR**" in panel
    assert "github, research" in panel
    assert profile.primary_class in panel
    assert profile.title in panel
    assert "HERMES SHADOW PROFILE" in ansi_panel
    assert "persistent archive // status window" in ansi_panel
    assert "\x1b[" in ansi_panel
    assert "ACHIEVEMENTS" in ansi_panel
    assert "ATTRIBUTES" in ansi_panel
    assert "DISCIPLINES" in ansi_panel
    assert "FIELD REPORT" in ansi_panel
    assert "██   ██" in ansi_panel
    assert "HERMES // SHADOW PROFILE // ANSI WINDOW" in compact_panel
    assert "HERMES // SHADOW PROFILE" in minimal_panel
    assert "status window // ansi mode" in minimal_panel
    assert svg.startswith("<svg")
    assert "Status Window" in svg
    assert profile.title in svg
