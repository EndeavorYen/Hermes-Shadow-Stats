from __future__ import annotations

from pathlib import Path

from .models import ActivitySignals, ScanSummary


def _read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _count_bullet_entries(path: Path) -> int:
    count = 0
    for line in _read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ", "§")):
            count += 1
    return count


def _categorize_skill(skill_path: Path, hermes_home: Path) -> str:
    relative = skill_path.relative_to(hermes_home / "skills")
    parts = relative.parts
    if len(parts) >= 2:
        return parts[0]
    return "uncategorized"


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for child in path.rglob("*") if child.is_file())


def _iter_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [child for child in path.rglob("*") if child.is_file()]


def _word_count(text: str) -> int:
    return len([word for word in text.replace("\n", " ").split(" ") if word.strip()])


def _scan_activity(home: Path) -> ActivitySignals:
    memories_dir = home / "memories"
    skills_dir = home / "skills"
    sessions_dir = home / "sessions"
    plugins_dir = home / "plugins"
    cron_dir = home / "cron"

    memory_text = _read_text(memories_dir / "MEMORY.md") + "\n" + _read_text(memories_dir / "USER.md")
    skill_words = 0
    for skill_file in skills_dir.rglob("SKILL.md") if skills_dir.exists() else []:
        skill_words += _word_count(_read_text(skill_file))

    session_tool_mentions = 0
    session_error_mentions = 0
    for session_file in _iter_files(sessions_dir)[:200]:
        text = _read_text(session_file).lower()
        session_tool_mentions += text.count('"tool"') + text.count("tool_call") + text.count("terminal")
        session_error_mentions += text.count("error") + text.count("exception") + text.count("fail")

    plugin_manifest_count = 0
    plugin_hook_mentions = 0
    for plugin_file in _iter_files(plugins_dir)[:200]:
        text = _read_text(plugin_file).lower()
        if plugin_file.name == "plugin.yaml":
            plugin_manifest_count += 1
        plugin_hook_mentions += (
            text.count("register_hook")
            + text.count("post_tool_call")
            + text.count("on_session")
            + text.count("pre_tool_call")
        )

    cron_schedule_mentions = 0
    for cron_file in _iter_files(cron_dir)[:100]:
        text = _read_text(cron_file).lower()
        cron_schedule_mentions += text.count("schedule") + text.count("cron") + text.count("repeat")

    return ActivitySignals(
        memory_lines=len([line for line in memory_text.splitlines() if line.strip()]),
        skill_words=skill_words,
        session_tool_mentions=session_tool_mentions,
        session_error_mentions=session_error_mentions,
        plugin_manifest_count=plugin_manifest_count,
        plugin_hook_mentions=plugin_hook_mentions,
        cron_schedule_mentions=cron_schedule_mentions,
    )


def scan_hermes_home(hermes_home: str | Path) -> ScanSummary:
    home = Path(hermes_home).expanduser().resolve()

    memories_dir = home / "memories"
    skills_dir = home / "skills"
    sessions_dir = home / "sessions"
    profiles_dir = home / "profiles"
    plugins_dir = home / "plugins"
    logs_dir = home / "logs"
    cron_dir = home / "cron"

    memory_entries = _count_bullet_entries(memories_dir / "MEMORY.md")
    user_entries = _count_bullet_entries(memories_dir / "USER.md")

    skill_categories: dict[str, int] = {}
    skill_count = 0
    if skills_dir.exists():
        for skill_file in skills_dir.rglob("SKILL.md"):
            skill_count += 1
            category = _categorize_skill(skill_file, home)
            skill_categories[category] = skill_categories.get(category, 0) + 1

    return ScanSummary(
        hermes_home=str(home),
        memory_entries=memory_entries,
        user_entries=user_entries,
        skill_count=skill_count,
        skill_categories=dict(sorted(skill_categories.items())),
        profile_count=sum(1 for child in profiles_dir.iterdir() if child.is_dir()) if profiles_dir.exists() else 0,
        session_file_count=_count_files(sessions_dir),
        plugin_count=sum(1 for child in plugins_dir.iterdir() if child.is_dir()) if plugins_dir.exists() else 0,
        log_file_count=_count_files(logs_dir),
        cron_file_count=_count_files(cron_dir),
        activity=_scan_activity(home),
    )
