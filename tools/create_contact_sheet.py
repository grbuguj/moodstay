#!/usr/bin/env python3
"""Render labeled image previews into a compact contact sheet."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--columns", type=int, default=4)
    args = parser.parse_args()

    paths = sorted(args.input_dir.glob("V*.png"))
    thumb_w, thumb_h, label_h = 216, 384, 30
    rows = (len(paths) + args.columns - 1) // args.columns
    sheet = Image.new("RGB", (thumb_w * args.columns, (thumb_h + label_h) * rows), "#111111")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=20)

    for index, path in enumerate(paths):
        image = Image.open(path).convert("RGB").resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % args.columns) * thumb_w
        y = (index // args.columns) * (thumb_h + label_h)
        sheet.paste(image, (x, y))
        draw.text((x + 8, y + thumb_h + 3), path.stem, fill="white", font=font)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, quality=92)


if __name__ == "__main__":
    main()
