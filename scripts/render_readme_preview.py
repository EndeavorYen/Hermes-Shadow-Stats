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
    99: "#875fff",
    103: "#8787af",
    111: "#87afff",
    117: "#87d7ff",
    141: "#af87ff",
    153: "#afd7ff",
    177: "#d787ff",
    183: "#d7afff",
    189: "#d7d7ff",
    203: "#ff5f5f",
    221: "#ffd75f",
    245: "#8a8a8a",
    250: "#bcbcbc",
}

BASE_STYLE = {"fg": "#e7eaf6", "bold": False, "dim": False}


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

    lines = result.stdout.splitlines()[:24]
    width = 1540
    height = 1080
    img = Image.new("RGB", (width, height), "#070916")
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((28, 28, width - 28, height - 28), radius=34, fill="#080b18")
    draw.rounded_rectangle((44, 44, width - 44, height - 44), radius=28, fill="#0d1020", outline="#5f87ff", width=2)
    draw.rounded_rectangle((44, 44, width - 44, 118), radius=28, fill="#12152a")
    draw.line((72, 118, width - 72, 118), fill="#2c3d73", width=1)

    title_font = load_font(26, bold=True)
    body_font = load_font(25, bold=False)
    body_font_bold = load_font(25, bold=True)

    draw.text((72, 66), "HERMES SHADOW STATS", fill="#d7afff", font=title_font)
    draw.text((860, 66), "README PREVIEW // ANSI-FIRST", fill="#87d7ff", font=title_font)

    x0 = 72
    y = 158
    char_width = draw.textbbox((0, 0), "M", font=body_font)[2]
    line_height = 33

    for line in lines:
        segments = ansi_to_segments(line)
        x = x0
        for text, style in segments:
            if not text:
                continue
            font = body_font_bold if style.get("bold") else body_font
            fill = style_fill(style)
            draw.text((x, y), text, fill=fill, font=font)
            x += char_width * len(text)
        y += line_height

    footer = "A status window for watching your agent awaken, adapt, and level up."
    draw.text((72, height - 98), footer, fill="#d7afff", font=title_font)

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    print(render_preview(DEFAULT_OUT))
