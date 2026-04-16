#!/usr/bin/env python3
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "assets" / "ansi-preview.png"
DEMO_HOME = ROOT / "examples" / "demo-hermes-home"
ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")

ANSI_256 = {
    69: "#5f87ff",
    99: "#5f87ff",
    103: "#7f91bd",
    110: "#87afd7",
    111: "#87afff",
    115: "#87d7af",
    117: "#87d7ff",
    141: "#87d7ff",
    153: "#afd7ff",
    177: "#87afd7",
    183: "#afd7ff",
    189: "#d7ebff",
    203: "#ff6b6b",
    215: "#ffaf5f",
    221: "#ffd75f",
    245: "#8a8a8a",
    250: "#bcbcbc",
}

BASE_STYLE = {"fg": "#e7eaf6", "bold": False, "dim": False}


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    menlo_index = 1 if bold else 0
    candidates: list[tuple[str, int]] = [
        ("/System/Library/Fonts/Menlo.ttc", menlo_index),
        ("/System/Library/Fonts/Monaco.ttf", 0),
        (
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
            if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            0,
        ),
        (
            "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Courier New.ttf",
            0,
        ),
    ]
    for candidate, index in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size, index=index)
            except Exception:
                pass
    return ImageFont.load_default()


def load_cjk_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[tuple[str, int]] = [
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1 if bold else 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/STHeiti Light.ttc", 0),
        ("/System/Library/Fonts/Songti.ttc", 0),
    ]
    for candidate, index in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size, index=index)
            except Exception:
                continue
    return load_font(size, bold)


def ansi_to_segments(line: str) -> list[tuple[str, dict[str, object]]]:
    style = dict(BASE_STYLE)
    parts: list[tuple[str, dict[str, object]]] = []
    cursor = 0
    for match in ANSI_RE.finditer(line):
        if match.start() > cursor:
            parts.append((line[cursor:match.start()], dict(style)))
        codes = [int(x) for x in match.group(1).split(";") if x] or [0]
        i = 0
        while i < len(codes):
            code = codes[i]
            if code == 0:
                style = dict(BASE_STYLE)
            elif code == 1:
                style["bold"] = True
            elif code == 2:
                style["dim"] = True
            elif code == 97:
                style["fg"] = "#f8fbff"
            elif code == 38 and i + 2 < len(codes) and codes[i + 1] == 5:
                style["fg"] = ANSI_256.get(codes[i + 2], style["fg"])
                i += 2
            i += 1
        cursor = match.end()
    if cursor < len(line):
        parts.append((line[cursor:], dict(style)))
    return parts


def style_fill(style: dict[str, object]) -> str:
    fill = str(style["fg"])
    if style.get("dim"):
        return "#8e95b5" if fill == BASE_STYLE["fg"] else fill
    return fill


def render_preview(output_path: Path, lang: str = "en", display_name: str = "Demo Hermes") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(ROOT / ".venv" / "bin" / "hermes-shadow-stats"),
            "--format",
            "ansi",
            "--banner-mode",
            "wide",
            "--hermes-home",
            str(DEMO_HOME),
            "--name",
            display_name,
            "--lang",
            lang,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    raw_lines = result.stdout.splitlines()
    width = 1540
    chrome_font = load_font(20, bold=False)
    body_font = load_font(25, bold=False)
    body_font_bold = load_font(25, bold=True)
    cjk_font = load_cjk_font(23, bold=False)
    cjk_font_bold = load_cjk_font(23, bold=True)

    margin = 56
    chrome_height = 56
    line_height = 33
    height = max(800, chrome_height + 64 + line_height * len(raw_lines) + margin)
    img = Image.new("RGB", (width, height), "#060814")
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=18, fill="#070a17")
    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=12, fill="#0b1020", outline="#4f73d9", width=2)
    draw.rounded_rectangle((40, 40, width - 40, 40 + chrome_height), radius=12, fill="#11172b")
    draw.line((72, 40 + chrome_height, width - 72, 40 + chrome_height), fill="#253968", width=1)
    draw.text((72, 56), "Hermes Shadow Stats // ANSI Preview", fill="#afd7ff", font=chrome_font)

    char_width = draw.textbbox((0, 0), "M", font=body_font)[2]

    x0 = 72
    y = 40 + chrome_height + 24
    for line in raw_lines:
        segments = ansi_to_segments(line)
        x = x0
        for text, style in segments:
            if not text:
                continue
            bold = bool(style.get("bold"))
            mono = body_font_bold if bold else body_font
            cjk = cjk_font_bold if bold else cjk_font
            fill = style_fill(style)
            for ch in text:
                wide = _is_wide(ch)
                font = cjk if wide else mono
                draw.text((x, y + (3 if wide else 0)), ch, fill=fill, font=font)
                x += char_width * (2 if wide else 1)
        y += line_height

    img.save(output_path)
    return output_path


def _is_wide(ch: str) -> bool:
    cp = ord(ch)
    return (
        0x1100 <= cp <= 0x115F
        or 0x2E80 <= cp <= 0x303E
        or 0x3041 <= cp <= 0x33FF
        or 0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0xA000 <= cp <= 0xA4CF
        or 0xAC00 <= cp <= 0xD7A3
        or 0xF900 <= cp <= 0xFAFF
        or 0xFE30 <= cp <= 0xFE4F
        or 0xFF00 <= cp <= 0xFF60
        or 0xFFE0 <= cp <= 0xFFE6
    )


if __name__ == "__main__":
    print(render_preview(DEFAULT_OUT, lang="en"))
    print(render_preview(ROOT / "assets" / "ansi-preview.zh-TW.png", lang="zh-TW", display_name="影之 Hermes"))
