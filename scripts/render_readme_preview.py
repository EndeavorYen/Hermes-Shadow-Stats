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
    117: "#87d7ff",
    141: "#87d7ff",
    153: "#afd7ff",
    177: "#87afd7",
    183: "#afd7ff",
    189: "#d7ebff",
    203: "#ff6b6b",
    221: "#ffd75f",
    245: "#8a8a8a",
    250: "#bcbcbc",
}

BASE_STYLE = {"fg": "#e7eaf6", "bold": False, "dim": False}

PIXEL_FONT = {
    "H": [
        "1100011",
        "1100011",
        "1100011",
        "1111111",
        "1111111",
        "1100011",
        "1100011",
    ],
    "E": [
        "1111111",
        "1100000",
        "1100000",
        "1111110",
        "1111110",
        "1100000",
        "1111111",
    ],
    "R": [
        "1111110",
        "1100011",
        "1100011",
        "1111110",
        "1111000",
        "1101100",
        "1100110",
    ],
    "M": [
        "1100011",
        "1110111",
        "1111111",
        "1101011",
        "1100011",
        "1100011",
        "1100011",
    ],
    "S": [
        "0111110",
        "1100000",
        "1111100",
        "0111110",
        "0001111",
        "0000011",
        "1111110",
    ],
}


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


def draw_pixel_word(draw: ImageDraw.ImageDraw, word: str, center_x: int, top_y: int, scale: int = 12) -> tuple[int, int, int, int]:
    spacing = scale
    glyph_cols = len(PIXEL_FONT[word[0]][0])
    glyph_rows = len(PIXEL_FONT[word[0]])
    glyph_w = glyph_cols * scale
    glyph_h = glyph_rows * scale
    total_width = len(word) * glyph_w + (len(word) - 1) * spacing
    start_x = center_x - total_width // 2
    colors = {
        "fill_top": "#d7ebff",
        "fill_mid": "#8fd4ff",
        "fill_low": "#5b87ff",
        "edge": "#27448d",
        "shadow": "#0b1633",
        "echo_a": "#3f6ed6",
        "echo_b": "#203a77",
    }

    for index, ch in enumerate(word):
        glyph = PIXEL_FONT[ch]
        glyph_x = start_x + index * (glyph_w + spacing)
        for row_idx, row in enumerate(glyph):
            for col_idx, bit in enumerate(row):
                if bit != "1":
                    continue
                x = glyph_x + col_idx * scale
                y = top_y + row_idx * scale
                for dx, dy, color in ((14, 14, colors["echo_b"]), (8, 8, colors["echo_a"]), (3, 3, colors["shadow"])):
                    draw.rectangle((x + dx, y + dy, x + scale + dx, y + scale + dy), fill=color)
                draw.rectangle((x, y, x + scale, y + scale), fill=colors["edge"])
                fill_color = colors["fill_top"] if row_idx <= 1 else colors["fill_mid"] if row_idx < glyph_rows - 2 else colors["fill_low"]
                draw.rectangle((x + 2, y + 2, x + scale - 2, y + scale - 2), fill=fill_color)

    return start_x, top_y, start_x + total_width, top_y + glyph_h


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

    raw_lines = result.stdout.splitlines()
    lines = raw_lines[4:36]
    width = 1540
    title_font = load_font(26, bold=True)
    body_font = load_font(25, bold=False)
    body_font_bold = load_font(25, bold=True)

    x0 = 72
    y = 392
    line_height = 33
    height = max(1360, y + line_height * len(lines) + 90)
    img = Image.new("RGB", (width, height), "#060814")
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((24, 24, width - 24, height - 24), radius=18, fill="#070a17")
    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=12, fill="#0b1020", outline="#4f73d9", width=2)
    draw.rounded_rectangle((40, 40, width - 40, 118), radius=12, fill="#11172b")
    draw.line((72, 118, width - 72, 118), fill="#253968", width=1)

    draw.text((72, 66), "Hermes Shadow Stats // ANSI Preview", fill="#afd7ff", font=title_font)

    draw.rectangle((110, 126, width - 110, 306), fill="#081121", outline="#223a77", width=0)
    draw.line((124, 300, width - 124, 300), fill="#20396f", width=1)
    draw_pixel_word(draw, "HERMES", width // 2, 132, scale=24)
    draw.text((width // 2 - 228, 314), "HERMES SHADOW PROFILE // STATUS WINDOW", fill="#87d7ff", font=title_font)

    char_width = draw.textbbox((0, 0), "M", font=body_font)[2]

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

    img.save(output_path)
    return output_path


if __name__ == "__main__":
    print(render_preview(DEFAULT_OUT))
