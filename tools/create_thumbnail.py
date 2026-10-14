"""Create the final 9:16 Moodstay cover from the rendered reel's first frame.

The project must contain output/final_reel.mp4 and thumbnail.json with:
  {"selected_copy": "첫 줄\\n둘째 줄"}

Usage:
  python tools/create_thumbnail.py projects/my-reel
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH, HEIGHT = 1080, 1920


def find_font() -> Path:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\\Windows")) / "Fonts" / "malgunbd.ttf",
        Path(os.environ.get("WINDIR", r"C:\\Windows")) / "Fonts" / "malgunsl.ttf",
        Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc"),
        Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    ]
    for font in candidates:
        if font.is_file():
            return font
    raise FileNotFoundError("No supported Korean bold font was found. Install Malgun Gothic or Noto Sans CJK.")


def selected_copy(project: Path) -> str:
    choice = project / "thumbnail.json"
    if not choice.is_file():
        raise FileNotFoundError("Missing thumbnail.json. Record the user's selected cover copy first.")
    value = json.loads(choice.read_text(encoding="utf-8")).get("selected_copy")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("thumbnail.json must contain a non-empty selected_copy string.")
    return value.strip()


def extract_first_frame(ffmpeg: str, video: Path, frame: Path) -> None:
    subprocess.run(
        [ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", str(video), "-frames:v", "1", str(frame)],
        check=True,
    )


def fit_font(draw: ImageDraw.ImageDraw, text: str, font_path: Path) -> ImageFont.FreeTypeFont:
    for size in range(154, 60, -2):
        font = ImageFont.truetype(str(font_path), size=size)
        box = draw.multiline_textbbox((0, 0), text, font=font, spacing=8, align="center", stroke_width=8)
        if box[2] - box[0] <= 940 and box[3] - box[1] <= 720:
            return font
    return ImageFont.truetype(str(font_path), size=60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--force", action="store_true", help="Replace an existing output/thumbnail.png")
    args = parser.parse_args()
    project = args.project.resolve()
    output = project / "output"
    video = output / "final_reel.mp4"
    target = output / "thumbnail.png"
    if not video.is_file():
        raise FileNotFoundError(f"Missing final reel: {video}")
    if target.exists() and not args.force:
        raise FileExistsError(f"Thumbnail already exists: {target}. Review it, then use --force to replace it.")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to extract the final reel's first frame.")

    with tempfile.TemporaryDirectory() as temp:
        frame = Path(temp) / "first-frame.png"
        extract_first_frame(ffmpeg, video, frame)
        image = Image.open(frame).convert("RGB")
        image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(image)
        copy = selected_copy(project)
        font = fit_font(draw, copy, find_font())
        draw.multiline_text(
            (WIDTH / 2, HEIGHT / 2), copy, font=font, fill="white", anchor="mm",
            align="center", spacing=8, stroke_width=12, stroke_fill="black",
        )
        ad_font = ImageFont.truetype(str(find_font()), size=34)
        draw.text((WIDTH - 50, 46), "[광고]", font=ad_font, fill="white", anchor="ra", stroke_width=2, stroke_fill="black")
        output.mkdir(parents=True, exist_ok=True)
        image.save(target, quality=95)
    print(f"DONE: {target}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
