#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "assets" / "ansi-preview.png"
DEMO_HOME = ROOT / "examples" / "demo-hermes-home"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_preview(output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(ROOT / ".venv" / "bin" / "hermes-shadow-stats"),
            "--format",
            "ansi",
            "--hermes-home",
            str(DEMO_HOME),
            "--name",
            "Demo Hermes",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    text = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout)
    lines = text.splitlines()[:30]

    width = 1600
    height = 980
    img = Image.new("RGB", (width, height), "#09090f")
    draw = ImageDraw.Draw(img)

    for i, color in enumerate(["#17112b", "#10182a", "#09090f"]):
        draw.rounded_rectangle((30 + i * 8, 30 + i * 8, width - 30 - i * 8, height - 30 - i * 8), radius=28, fill=color)

    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=24, outline="#8b5cf6", width=3)
    draw.rounded_rectangle((40, 40, width - 40, 120), radius=24, fill="#11131a")

    title_font = load_font(24, bold=True)
    terminal_font = load_font(24, bold=False)
    terminal_font_bold = load_font(24, bold=True)

    draw.text((70, 66), "HERMES SHADOW STATS", fill="#d8c4ff", font=title_font)
    draw.text((1080, 66), "ANSI-FIRST HUNTER INTERFACE", fill="#7dd3fc", font=title_font)

    palette = {
        "default": "#e5e7eb",
        "accent": "#c4b5fd",
        "cyan": "#7dd3fc",
        "gold": "#fcd34d",
    }

    y = 155
    for idx, line in enumerate(lines):
        color = palette["default"]
        font_used = terminal_font
        stripped = line.strip()
        if idx < 6:
            color = palette["accent"] if idx in {0, 2, 4, 5} else palette["cyan"]
            font_used = terminal_font_bold
        elif "[ SYSTEM ]" in line:
            color = palette["cyan"]
            font_used = terminal_font_bold
        elif any(key in line for key in ["BASE ATTRIBUTES", "GROWTH ECHOES", "DEEP SIGNALS", "ACHIEVEMENTS", "NARRATIVE SUMMARY"]):
            color = palette["gold"]
            font_used = terminal_font_bold
        elif any(key in line for key in ["NAME", "TITLE", "CLASS", "LEVEL", "EXP"]):
            color = palette["accent"]
            font_used = terminal_font_bold
        elif "THREAT" in line or "Mythic" in line:
            color = palette["accent"]
        elif stripped == "":
            y += 10
            continue
        draw.text((70, y), line, fill=color, font=font_used)
        y += 28

    footer = "A status window for watching your agent awaken, adapt, and level up."
    draw.text((70, height - 78), footer, fill="#d8c4ff", font=title_font)

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    print(render_preview(DEFAULT_OUT))
