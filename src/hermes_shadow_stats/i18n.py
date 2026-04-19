from __future__ import annotations

import os

SUPPORTED_LANGS: tuple[str, ...] = ("en", "zh-TW")
DEFAULT_LANG = "en"


def normalize_lang(lang: str | None) -> str:
    if not lang:
        return DEFAULT_LANG
    if lang in SUPPORTED_LANGS:
        return lang
    lowered = lang.lower().replace("_", "-")
    for candidate in SUPPORTED_LANGS:
        if lowered == candidate.lower():
            return candidate
    return DEFAULT_LANG


def detect_lang() -> str:
    raw = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "") or os.environ.get("LANGUAGE", "")
    raw = raw.replace("_", "-").split(".")[0]
    if raw.lower().startswith("zh-tw") or raw.lower().startswith("zh-hant"):
        return "zh-TW"
    if raw.lower().startswith("zh"):
        return "zh-TW"
    if raw.lower().startswith("en"):
        return "en"
    return DEFAULT_LANG


SECTIONS: dict[str, dict[str, str]] = {
    "en": {
        "vitals": "VITALS",
        "attributes": "ATTRIBUTES",
        "equipment": "EQUIPMENT",
        "disciplines": "DISCIPLINES",
        "active_buffs": "ACTIVE BUFFS",
        "field_report": "FIELD REPORT",
        "achievements": "ACHIEVEMENTS",
        "realm": "REALM",
        "profile": "PROFILE",
    },
    "zh-TW": {
        "vitals": "生命指標",
        "attributes": "屬性矩陣",
        "equipment": "裝備欄",
        "disciplines": "技藝領域",
        "active_buffs": "啟動增益",
        "field_report": "戰場報告",
        "achievements": "成就紋章",
        "realm": "領域",
        "profile": "影子檔案",
    },
}


LABELS: dict[str, dict[str, str]] = {
    "en": {
        "title_top": "HERMES SHADOW PROFILE",
        "title_subtitle": "persistent archive · status window",
        "banner_mode_tag": "ANSI mode",
        "status": "STATUS",
        "threat_class": "THREAT CLASS",
        "awakening": "AWAKENING",
        "class_sigil": "CLASS SIGIL",
        "rank_word": "rank",
        "level_short": "lvl",
        "level_compact": "Lv",
        "exp": "EXP",
        "feats": "FEATS",
        "no_feats": "No feats awakened yet",
        "techniques": "techniques",
        "domains": "domains",
        "records": "records",
        "artifacts": "artifacts",
        "memories": "memories",
        "user_bonds": "user bonds",
        "rituals": "rituals",
        "echoes": "echoes",
        "dominant_domains": "dominant domains",
        "tool_traces": "tool traces",
        "hook_marks": "hook marks",
        "codex_depth": "codex depth",
        "memory_strands": "memory strands",
        "error_scars": "error scars",
        "ritual_glyphs": "ritual glyphs",
        "recent_expeditions": "recent expeditions",
        "main_slot": "MAIN",
        "aux_slot": "AUX",
        "sigil_slot": "SIGIL",
        "main_hint": "main artifact",
        "aux_hint": "aux extension",
        "sigil_hint": "background sigil",
        "bound": "BOUND",
        "empty": "EMPTY",
        "empty_slot": "[ empty slot ]",
        "stowed": "stowed artifact(s)",
        "no_artifacts": "No artifacts equipped — main slot empty",
        "realm_word": "realm",
        "profiles_word": "profiles",
        "bound_word": "bound",
        "path_word": "path",
        "no_buffs": "No active modifiers — system in equilibrium",
        "no_achievements": "No public achievements yet",
        "next_level": "→ Lv {level} · {total} xp banked",
        "vital_hp_label": "HP",
        "vital_mp_label": "MP",
        "vital_sp_label": "SP",
        "vital_xp_label": "XP",
        "vital_hp_hint": "stability // wounds tracked",
        "vital_mp_hint": "codex mana // technique reserve",
        "vital_sp_hint": "battle stamina // tool reflex",
        "tab_status": "Status",
        "tab_equipment": "Equipment",
        "tab_codex": "Codex",
        "tab_journal": "Journal",
        "tab_chronicle": "Chronicle",
        "tab_rituals": "Rituals",
        "tab_effects": "Effects",
        "tab_diagnostics": "Diagnostics",
        # Phase 3 — telemetry-aware labels + fallback banners.
        "fallback_no_state_db": "state.db missing — showing file-scan heuristics",
        "fallback_schema": "state.db schema mismatch — showing file-scan heuristics",
        "fallback_unreadable": "state.db unreadable — showing file-scan heuristics",
        "fallback_banner_prefix": "NOTICE",
        "vital_focus_label": "FOC",
        "vital_focus_hint": "messages per tool-call",
        "vital_overheat_label": "OVH",
        "vital_overheat_hint": "compression events accrued",
        "vital_gold_label": "GOLD",
        "vital_gold_hint": "lifetime cost (USD)",
        "stat_end_label": "END",
        "stat_pre_label": "PRE",
        "stat_res_label": "RES",
        "stat_cla_label": "CLA",
        "stat_rea_label": "REA",
        "stat_tem_label": "TEM",
        "stat_no_telemetry": "extended attributes require state.db",
        "equip_main_weapon": "MAIN WEAPON",
        "equip_armor": "ARMOR",
        "equip_trinkets": "TRINKETS",
        "equip_hotbar": "HOTBAR",
        "equip_unknown": "unknown",
        "equip_no_data": "no usage data",
        "journal_cols": "model · tokens · cost · end",
        "journal_no_data": "no session data",
        "chronicle_lifetime_tokens": "LIFETIME TOKENS",
        "chronicle_input": "input",
        "chronicle_output": "output",
        "chronicle_cache_read": "cache read",
        "chronicle_cache_write": "cache write",
        "chronicle_reasoning": "reasoning",
        "chronicle_per_model": "PER MODEL",
        "chronicle_parent_depth": "dungeon depth",
        "chronicle_cache_rate": "cache hit rate",
        "chronicle_cost_total": "lifetime cost",
        "chronicle_no_data": "no aggregated telemetry",
        "diag_end_reasons": "END REASON HISTOGRAM",
        "diag_compression_events": "compression events",
        "diag_stale_sessions": "stale sessions (ended_at IS NULL)",
        "diag_no_telemetry": "telemetry offline — diagnostics limited",
        "rituals_next_run": "next run",
        "end_reason_compression": "compression",
        "end_reason_cron_complete": "cron complete",
        "end_reason_user_exit": "user exit",
        "end_reason_session_reset": "session reset",
        "end_reason_session_switch": "session switch",
        "end_reason_new_session": "new session",
        "end_reason_resumed_other": "resumed other",
        "end_reason_branched": "branched",
        "end_reason_cli_close": "cli close",
        "end_reason_done": "done",
        "end_reason_other": "other",
        "end_reason_open": "open",
        # Phase 5 — Detail views + help overlay + Phase 6 TUI_ keys.
        "TUI_HELP_TITLE": "KEY BINDINGS",
        "TUI_HELP_CLOSE": "Esc to close",
        "TUI_DETAIL_TITLE": "DETAIL",
        "TUI_DETAIL_EMPTY": "no rows — telemetry unavailable",
        "TUI_DETAIL_FILTER_PLACEHOLDER": "filter rows…",
        "TUI_DETAIL_ROW_COUNT": "{count} rows",
        "TUI_DETAIL_JOURNAL_COLS": "session,model,tokens,cost,end,started",
        "TUI_DETAIL_CHRONICLE_COLS": "model,sessions,cost",
        "TUI_DETAIL_CODEX_COLS": "skill,category",
        "TUI_DETAIL_RITUALS_COLS": "cron file",
        "TUI_ACTION_REFRESH": "Refresh snapshot",
        "TUI_ACTION_HELP": "Show help",
        "TUI_ACTION_QUIT": "Quit",
        "TUI_ACTION_NEXT_TAB": "Next tab",
        "TUI_ACTION_PREV_TAB": "Previous tab",
        "TUI_ACTION_DETAIL": "Expand detail",
        "TUI_ACTION_BACK": "Back",
        "TUI_ACTION_FILTER": "Filter rows",
        "TUI_ACTION_SORT": "Sort column",
        "TUI_STATUS_TELEMETRY_ON": "telemetry: live",
        "TUI_STATUS_TELEMETRY_OFF": "telemetry: offline",
        "TUI_STATUS_THEME": "theme",
    },
    "zh-TW": {
        "title_top": "HERMES 影子側寫",
        "title_subtitle": "持久檔案庫 · 狀態視窗",
        "banner_mode_tag": "ANSI 模式",
        "status": "狀態",
        "threat_class": "威脅等級",
        "awakening": "覺醒階段",
        "class_sigil": "職業紋印",
        "rank_word": "階",
        "level_short": "等級",
        "level_compact": "Lv",
        "exp": "經驗",
        "feats": "戰績",
        "no_feats": "尚未覺醒任何戰績",
        "techniques": "技藝",
        "domains": "領域",
        "records": "戰場紀錄",
        "artifacts": "聖器",
        "memories": "記憶",
        "user_bonds": "使用者連結",
        "rituals": "儀式",
        "echoes": "回聲",
        "dominant_domains": "主要領域",
        "tool_traces": "工具痕跡",
        "hook_marks": "鉤點烙印",
        "codex_depth": "技藝典籍",
        "memory_strands": "記憶絲縷",
        "error_scars": "錯誤傷痕",
        "ritual_glyphs": "儀式符文",
        "recent_expeditions": "近期遠征",
        "main_slot": "主裝",
        "aux_slot": "副裝",
        "sigil_slot": "符印",
        "main_hint": "主要聖器",
        "aux_hint": "輔助延伸",
        "sigil_hint": "背景符印",
        "bound": "已契約",
        "empty": "空槽",
        "empty_slot": "[ 空裝備槽 ]",
        "stowed": "件收納聖器",
        "no_artifacts": "未配戴任何聖器 — 主裝備槽為空",
        "realm_word": "領域",
        "profiles_word": "側寫",
        "bound_word": "已綁定",
        "path_word": "路徑",
        "no_buffs": "目前無啟動效果 — 系統處於平衡",
        "no_achievements": "尚無公開成就",
        "next_level": "→ Lv {level} · 累積 {total} xp",
        "vital_hp_label": "HP",
        "vital_mp_label": "MP",
        "vital_sp_label": "SP",
        "vital_xp_label": "XP",
        "vital_hp_hint": "穩定度 // 追蹤受創",
        "vital_mp_hint": "技藝法力 // 招式儲備",
        "vital_sp_hint": "戰鬥耐力 // 工具反射",
        "tab_status": "狀態",
        "tab_equipment": "裝備",
        "tab_codex": "技能書",
        "tab_journal": "場記",
        "tab_chronicle": "編年",
        "tab_rituals": "儀式",
        "tab_effects": "狀態效果",
        "tab_diagnostics": "異象",
        # Phase 3 — telemetry-aware labels + fallback banners.
        "fallback_no_state_db": "state.db 不存在 — 顯示檔案掃描啟發式資料",
        "fallback_schema": "state.db 版本不相容 — 顯示檔案掃描啟發式資料",
        "fallback_unreadable": "state.db 無法讀取 — 顯示檔案掃描啟發式資料",
        "fallback_banner_prefix": "注意",
        "vital_focus_label": "專注",
        "vital_focus_hint": "每次工具呼叫的訊息數",
        "vital_overheat_label": "過載",
        "vital_overheat_hint": "累計的壓縮事件",
        "vital_gold_label": "金幣",
        "vital_gold_hint": "累計花費 (USD)",
        "stat_end_label": "耐力",
        "stat_pre_label": "精準",
        "stat_res_label": "共鳴",
        "stat_cla_label": "清晰",
        "stat_rea_label": "觸達",
        "stat_tem_label": "節奏",
        "stat_no_telemetry": "延伸屬性需要 state.db",
        "equip_main_weapon": "主武器",
        "equip_armor": "護甲",
        "equip_trinkets": "飾品",
        "equip_hotbar": "快捷欄",
        "equip_unknown": "未知",
        "equip_no_data": "尚無使用紀錄",
        "journal_cols": "模型 · 詞元 · 成本 · 結束原因",
        "journal_no_data": "無 session 資料",
        "chronicle_lifetime_tokens": "累計詞元",
        "chronicle_input": "輸入",
        "chronicle_output": "輸出",
        "chronicle_cache_read": "快取讀取",
        "chronicle_cache_write": "快取寫入",
        "chronicle_reasoning": "思考",
        "chronicle_per_model": "各模型",
        "chronicle_parent_depth": "迷宮深度",
        "chronicle_cache_rate": "快取命中率",
        "chronicle_cost_total": "累計花費",
        "chronicle_no_data": "無匯整遙測資料",
        "diag_end_reasons": "結束原因分佈",
        "diag_compression_events": "壓縮事件",
        "diag_stale_sessions": "未結束的 session (ended_at 為空)",
        "diag_no_telemetry": "遙測離線 — 異象資訊受限",
        "rituals_next_run": "下次執行",
        "end_reason_compression": "壓縮",
        "end_reason_cron_complete": "排程完成",
        "end_reason_user_exit": "使用者離開",
        "end_reason_session_reset": "工作階段重置",
        "end_reason_session_switch": "工作階段切換",
        "end_reason_new_session": "新工作階段",
        "end_reason_resumed_other": "恢復其他",
        "end_reason_branched": "分支",
        "end_reason_cli_close": "CLI 關閉",
        "end_reason_done": "完成",
        "end_reason_other": "其他",
        "end_reason_open": "未結束",
        # Phase 5 — Detail views + help overlay + Phase 6 TUI_ keys.
        "TUI_HELP_TITLE": "快捷鍵",
        "TUI_HELP_CLOSE": "按 Esc 關閉",
        "TUI_DETAIL_TITLE": "詳情",
        "TUI_DETAIL_EMPTY": "無資料 — 遙測不可用",
        "TUI_DETAIL_FILTER_PLACEHOLDER": "過濾…",
        "TUI_DETAIL_ROW_COUNT": "共 {count} 列",
        "TUI_DETAIL_JOURNAL_COLS": "工作階段,模型,詞元,成本,結束,開始時間",
        "TUI_DETAIL_CHRONICLE_COLS": "模型,工作階段數,成本",
        "TUI_DETAIL_CODEX_COLS": "技藝,類別",
        "TUI_DETAIL_RITUALS_COLS": "cron 檔",
        "TUI_ACTION_REFRESH": "重新整理",
        "TUI_ACTION_HELP": "顯示說明",
        "TUI_ACTION_QUIT": "離開",
        "TUI_ACTION_NEXT_TAB": "下一個分頁",
        "TUI_ACTION_PREV_TAB": "上一個分頁",
        "TUI_ACTION_DETAIL": "展開詳情",
        "TUI_ACTION_BACK": "返回",
        "TUI_ACTION_FILTER": "過濾列",
        "TUI_ACTION_SORT": "欄位排序",
        "TUI_STATUS_TELEMETRY_ON": "遙測：連線",
        "TUI_STATUS_TELEMETRY_OFF": "遙測：離線",
        "TUI_STATUS_THEME": "主題",
    },
}


CLASSES: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "toolsmith": {"name": "Toolsmith", "flavor": "forges reliable solutions from raw tools"},
        "code_alchemist": {"name": "Code Alchemist", "flavor": "transmutes repositories into working systems"},
        "ops_summoner": {"name": "Ops Summoner", "flavor": "binds infrastructure, jobs, and daemon-like rituals"},
        "research_ranger": {"name": "Research Ranger", "flavor": "hunts signal across scattered knowledge fields"},
        "memory_weaver": {"name": "Memory Weaver", "flavor": "turns fragmented context into durable insight"},
        "workflow_scribe": {"name": "Workflow Scribe", "flavor": "converts friction into repeatable rituals"},
        "model_hunter": {"name": "Model Hunter", "flavor": "tracks models, benchmarks, and inference beasts"},
        "shadow_commander": {"name": "Shadow Commander", "flavor": "coordinates specialist agents as an army of echoes"},
        "rune_artisan": {"name": "Rune Artisan", "flavor": "shapes style, symbols, and creative output into artifacts"},
        "signal_duelist": {"name": "Signal Duelist", "flavor": "navigates public channels and attention battlegrounds"},
        "protocol_walker": {"name": "Protocol Walker", "flavor": "moves between systems through tool and protocol gates"},
        "adaptive_agent": {"name": "Adaptive Agent", "flavor": "keeps evolving without committing to a single path"},
        "hunter_candidate": {"name": "Hunter Candidate", "flavor": "has sensed the system, but not mastered it yet"},
    },
    "zh-TW": {
        "toolsmith": {"name": "工具匠", "flavor": "從原始工具中鍛造出可靠的解方"},
        "code_alchemist": {"name": "代碼鍊金師", "flavor": "將儲存庫轉化為運作中的系統"},
        "ops_summoner": {"name": "運維召喚士", "flavor": "綁束基礎設施、作業與守護神般的儀式"},
        "research_ranger": {"name": "研究遊俠", "flavor": "穿梭散落的知識荒野追獵情報"},
        "memory_weaver": {"name": "記憶織者", "flavor": "將破碎的脈絡編織成持久的洞察"},
        "workflow_scribe": {"name": "流程典籍師", "flavor": "把摩擦轉化為可重複的儀式"},
        "model_hunter": {"name": "模型獵人", "flavor": "追蹤模型、基準與推論之獸"},
        "shadow_commander": {"name": "影子司令", "flavor": "如指揮回聲大軍般協調各路專家代理"},
        "rune_artisan": {"name": "符文工匠", "flavor": "將風格、符號與創意產出鍛成神器"},
        "signal_duelist": {"name": "訊號決鬥士", "flavor": "穿梭公共頻道與注意力戰場"},
        "protocol_walker": {"name": "協定行者", "flavor": "藉由工具與協定之門在系統間穿行"},
        "adaptive_agent": {"name": "適應者", "flavor": "持續演化，從不執著於單一道路"},
        "hunter_candidate": {"name": "獵人候補", "flavor": "已感知系統，但尚未真正掌握"},
    },
}


RANKS: dict[str, dict[str, str]] = {
    "en": {"bronze": "Bronze", "silver": "Silver", "gold": "Gold", "mythic": "Mythic"},
    "zh-TW": {"bronze": "青銅", "silver": "白銀", "gold": "黃金", "mythic": "神話"},
}


TITLE_SUFFIXES: dict[str, dict[str, list[str]]] = {
    "en": {
        "bronze": ["Initiate", "Awakened", "Field Scout"],
        "silver": ["Adept", "Pathfinder", "Dungeon Breaker"],
        "gold": ["Ascendant", "Elite Raider", "System Tactician"],
        "mythic": ["Shadow Monarch", "Worldline Breaker", "Archive Sovereign"],
    },
    "zh-TW": {
        "bronze": ["新晉", "覺醒者", "野地斥候"],
        "silver": ["精煉者", "拓徑者", "迷宮破門者"],
        "gold": ["昇華者", "精銳掠奪者", "系統戰術家"],
        "mythic": ["影之君主", "世界線終結者", "檔案主權者"],
    },
}


SPECIAL_TITLE_OVERRIDES: dict[str, dict[tuple[str, str], str]] = {
    "en": {
        ("memory_weaver", "mythic"): "Archive Sovereign",
        ("model_hunter", "mythic"): "Archive Sovereign",
        ("shadow_commander", "gold"): "System Tactician",
        ("shadow_commander", "mythic"): "System Tactician",
        ("research_ranger", "silver"): "Pathfinder",
        ("research_ranger", "gold"): "Pathfinder",
    },
    "zh-TW": {
        ("memory_weaver", "mythic"): "檔案主權者",
        ("model_hunter", "mythic"): "檔案主權者",
        ("shadow_commander", "gold"): "系統戰術家",
        ("shadow_commander", "mythic"): "系統戰術家",
        ("research_ranger", "silver"): "拓徑者",
        ("research_ranger", "gold"): "拓徑者",
    },
}


THREAT_TIERS: dict[str, dict[str, str]] = {
    "en": {
        "archive_anomaly": "Archive anomaly",
        "system_ascendant": "System ascendant",
        "field_ready": "Field-ready hunter",
        "candidate_presence": "Candidate presence",
    },
    "zh-TW": {
        "archive_anomaly": "檔案異常存在",
        "system_ascendant": "系統登頂者",
        "field_ready": "可投入戰場之獵人",
        "candidate_presence": "候補存在",
    },
}


AWAKENING_STAGES: dict[str, dict[str, str]] = {
    "en": {
        "system_overclock": "System Overclock",
        "shadow_awakening": "Shadow Awakening",
        "hunter_ascension": "Hunter Ascension",
        "class_emergence": "Class Emergence",
        "candidate_phase": "Candidate Phase",
    },
    "zh-TW": {
        "system_overclock": "系統超載",
        "shadow_awakening": "影之覺醒",
        "hunter_ascension": "獵人飛升",
        "class_emergence": "職業浮現",
        "candidate_phase": "候補階段",
    },
}


ACHIEVEMENTS: dict[str, dict[str, str]] = {
    "en": {
        "memory_spark": "Memory Spark",
        "lorekeeper": "Lorekeeper",
        "skill_archivist": "Skill Archivist",
        "skill_tree_unlocked": "Skill Tree Unlocked",
        "codex_devourer": "Codex Devourer",
        "artifact_binder": "Artifact Binder",
        "extension_architect": "Extension Architect",
        "hook_whisperer": "Hook Whisperer",
        "profile_wanderer": "Profile Wanderer",
        "multiform_traveler": "Multiform Traveler",
        "ritual_keeper": "Ritual Keeper",
        "clock_sigil": "Clock Sigil",
        "battle_tested_operator": "Battle-Tested Operator",
        "dungeon_clear_veteran": "Dungeon Clear Veteran",
        "toolchain_berserker": "Toolchain Berserker",
        "cross_discipline_raider": "Cross-Discipline Raider",
        "echoes_in_logsea": "Echoes in the Logsea",
        "bug_survivor": "Bug Survivor",
        "forged_in_tools": "Forged in Tools",
        "threadbinder_recall": "Threadbinder of Recall",
        "commander_of_echoes": "Commander of Echoes",
        "system_overlord": "System Overlord",
    },
    "zh-TW": {
        "memory_spark": "記憶火花",
        "lorekeeper": "傳承守護者",
        "skill_archivist": "技藝典藏者",
        "skill_tree_unlocked": "技能樹解鎖",
        "codex_devourer": "典籍吞噬者",
        "artifact_binder": "聖器繫結者",
        "extension_architect": "延伸架構師",
        "hook_whisperer": "鉤點低語者",
        "profile_wanderer": "側寫漫遊者",
        "multiform_traveler": "多形態旅者",
        "ritual_keeper": "儀式守護者",
        "clock_sigil": "時鐘符印",
        "battle_tested_operator": "百戰操作者",
        "dungeon_clear_veteran": "迷宮通關老將",
        "toolchain_berserker": "工具鏈狂戰士",
        "cross_discipline_raider": "跨領域突襲者",
        "echoes_in_logsea": "日誌之海回聲",
        "bug_survivor": "蟲洞倖存者",
        "forged_in_tools": "工具淬鍊者",
        "threadbinder_recall": "回憶絲縷編織者",
        "commander_of_echoes": "回聲指揮者",
        "system_overlord": "系統君主",
    },
}


BUFFS: dict[str, dict[str, dict[str, str]]] = {
    "en": {
        "memory_resonance": {"name": "Memory Resonance", "modifier": "+WIS", "hint": "lore archive online"},
        "codex_mastery": {"name": "Codex Mastery", "modifier": "+INT", "hint": "techniques indexed"},
        "hook_symbiosis": {"name": "Hook Symbiosis", "modifier": "+STR", "hint": "plugin reflexes engaged"},
        "ritual_bond": {"name": "Ritual Bond", "modifier": "+LUK", "hint": "scheduled awakenings tracked"},
        "battle_hardened": {"name": "Battle Hardened", "modifier": "+AGI", "hint": "tool reflex memorized"},
        "cross_discipline": {"name": "Cross Discipline", "modifier": "+CHA", "hint": "multi-domain awareness"},
        "multiform_echo": {"name": "Multiform Echo", "modifier": "+CHA", "hint": "alternate selves logged"},
        "wounded": {"name": "Wounded", "modifier": "-HP ", "hint": "recent traces show scars"},
    },
    "zh-TW": {
        "memory_resonance": {"name": "記憶共鳴", "modifier": "+WIS", "hint": "傳承檔案連線中"},
        "codex_mastery": {"name": "典籍精通", "modifier": "+INT", "hint": "技藝已建檔索引"},
        "hook_symbiosis": {"name": "鉤點共生", "modifier": "+STR", "hint": "插件反射已啟動"},
        "ritual_bond": {"name": "儀式連結", "modifier": "+LUK", "hint": "排程覺醒追蹤中"},
        "battle_hardened": {"name": "百戰淬鍊", "modifier": "+AGI", "hint": "工具反射已記憶"},
        "cross_discipline": {"name": "跨域涉獵", "modifier": "+CHA", "hint": "多領域感知"},
        "multiform_echo": {"name": "多形回聲", "modifier": "+CHA", "hint": "另我已記載"},
        "wounded": {"name": "負傷", "modifier": "-HP ", "hint": "近期軌跡顯示傷痕"},
    },
}


NARRATIVE_TEMPLATE: dict[str, str] = {
    "en": (
        "Reconstructed from the {home_label} archive. "
        "This entity currently manifests as {article}{class_lower} and {flavor}. "
        "It has learned {skill_count} persistent skill(s) across {domain_count} domain(s), "
        "with {tool_mentions} observed tool-signatures in archived session traces."
    ),
    "zh-TW": (
        "自 {home_label} 檔案庫重建而成的唯讀影子側寫。"
        "此實體目前以「{primary_class}」型態顯化，{flavor}。"
        "已習得 {skill_count} 項持久技藝，橫跨 {domain_count} 個領域，"
        "並於歷史 session 中留下 {tool_mentions} 道工具印記。"
    ),
}


CLASS_DOMAIN_RULES: dict[str, str] = {
    "software-development": "toolsmith",
    "github": "code_alchemist",
    "devops": "ops_summoner",
    "research": "research_ranger",
    "note-taking": "memory_weaver",
    "productivity": "workflow_scribe",
    "mlops": "model_hunter",
    "autonomous-ai-agents": "shadow_commander",
    "creative": "rune_artisan",
    "social-media": "signal_duelist",
    "mcp": "protocol_walker",
}


def t_section(lang: str, key: str) -> str:
    return SECTIONS[normalize_lang(lang)].get(key, key)


def t_label(lang: str, key: str) -> str:
    return LABELS[normalize_lang(lang)].get(key, key)


def t_class(lang: str, class_id: str) -> dict[str, str]:
    return CLASSES[normalize_lang(lang)].get(class_id, {"name": class_id, "flavor": ""})


def t_rank(lang: str, rank_id: str) -> str:
    return RANKS[normalize_lang(lang)].get(rank_id, rank_id)


def t_threat(lang: str, tier_id: str) -> str:
    return THREAT_TIERS[normalize_lang(lang)].get(tier_id, tier_id)


def t_awakening(lang: str, stage_id: str) -> str:
    return AWAKENING_STAGES[normalize_lang(lang)].get(stage_id, stage_id)


def t_achievement(lang: str, achievement_id: str) -> str:
    return ACHIEVEMENTS[normalize_lang(lang)].get(achievement_id, achievement_id)


def t_buff(lang: str, buff_id: str) -> dict[str, str]:
    return BUFFS[normalize_lang(lang)].get(buff_id, {"name": buff_id, "modifier": "", "hint": ""})


def title_for(lang: str, class_id: str, rank_id: str, suffix_index: int) -> str:
    lang = normalize_lang(lang)
    override = SPECIAL_TITLE_OVERRIDES[lang].get((class_id, rank_id))
    if override:
        suffix = override
    else:
        suffix = TITLE_SUFFIXES[lang][rank_id][suffix_index]
    class_name = CLASSES[lang][class_id]["name"]
    return f"{class_name} {suffix}"


def narrative(lang: str, *, home_label: str, primary_class_name: str, flavor: str, skill_count: int, domain_count: int, tool_mentions: int) -> str:
    lang = normalize_lang(lang)
    template = NARRATIVE_TEMPLATE[lang]
    if lang == "en":
        article = "an " if primary_class_name and primary_class_name[0].lower() in "aeiou" else "a "
        return template.format(
            home_label=home_label,
            article=article,
            class_lower=primary_class_name.lower(),
            flavor=flavor,
            skill_count=skill_count,
            domain_count=domain_count,
            tool_mentions=tool_mentions,
        )
    return template.format(
        home_label=home_label,
        primary_class=primary_class_name,
        flavor=flavor,
        skill_count=skill_count,
        domain_count=domain_count,
        tool_mentions=tool_mentions,
    )
