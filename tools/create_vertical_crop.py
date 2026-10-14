#!/usr/bin/env python3
"""Create a clean 9:16 crop around a chosen horizontal focal point."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--focal-x", type=float, default=0.5)
    parser.add_argument("--focal-y", type=float, default=0.5)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    image = ImageOps.exif_transpose(Image.open(args.input)).convert("RGB")
    src_w, src_h = image.size
    target_ratio = args.width / args.height
    src_ratio = src_w / src_h

    focal_x = min(1.0, max(0.0, args.focal_x))
    focal_y = min(1.0, max(0.0, args.focal_y))

    if src_ratio > target_ratio:
        crop_h = src_h
        crop_w = round(crop_h * target_ratio)
        left = round(focal_x * src_w - crop_w / 2)
        left = min(src_w - crop_w, max(0, left))
        top = 0
    else:
        crop_w = src_w
        crop_h = round(crop_w / target_ratio)
        left = 0
        top = round(focal_y * src_h - crop_h / 2)
        top = min(src_h - crop_h, max(0, top))

    cropped = image.crop((left, top, left + crop_w, top + crop_h))
    rendered = cropped.resize((args.width, args.height), Image.Resampling.LANCZOS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rendered.save(args.output, quality=95, subsampling=0)


if __name__ == "__main__":
    main()
