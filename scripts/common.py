"""Shared configuration and safe, dependency-free SVG helpers."""
import json
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BG = "#0d1117"
LINE = "#30363d"
FG = "#e6edf3"
MUTED = "#919ba8"
GREEN = "#7ee787"
AMBER = "#d2ac7a"
FONT = "'DejaVu Sans Mono','Liberation Mono',Consolas,monospace"


def config():
    return json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))


def text(x, y, value, size=14, fill=FG, extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {extra}>{escape(str(value))}</text>'


def svg_start(width, height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        f'<style>text{{font-family:{FONT}}}.appear{{opacity:1}}'
        '@keyframes reveal{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}'
        '@keyframes type{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}'
        '@media(prefers-reduced-motion:reduce){.appear,.ascii-row{animation:none!important;clip-path:none!important}}'
        '</style>',
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="14" fill="{BG}" stroke="{LINE}"/>',
    ]


def chrome(width, label):
    return [
        '<circle cx="22" cy="22" r="4" fill="#f78166"/>',
        '<circle cx="37" cy="22" r="4" fill="#d2ac7a"/>',
        '<circle cx="52" cy="22" r="4" fill="#7ee787"/>',
        text(70, 26, label, 11, MUTED),
        f'<path d="M1 44H{width-1}" stroke="{LINE}"/>',
    ]


def appear(content, delay):
    if os.getenv("STATIC") == "1":
        return content
    return f'<g class="appear" style="animation:reveal .45s ease {delay:.2f}s both">{content}</g>'


def write_svg(path, parts):
    Path(path).write_text("\n".join(parts + ["</svg>"]) + "\n", encoding="utf-8")
