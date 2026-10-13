"""Measure a local reference video; detected boundaries require visual review.

Usage: python tools/analyze_reference.py VIDEO --out OUTPUT_DIRECTORY
Dependencies: FFmpeg, ffprobe, Pillow. No network or account access.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
import subprocess
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True)


def frame(video: Path, seconds: float, width: int = 360) -> Image.Image:
    result = run([
        "ffmpeg", "-v", "error", "-ss", f"{seconds:.9f}", "-i", str(video),
        "-frames:v", "1", "-vf", f"scale={width}:-1", "-f", "image2pipe",
        "-vcodec", "png", "-",
    ])
    return Image.open(io.BytesIO(result.stdout)).convert("RGB")


def board(video: Path, samples: list[tuple[float, str]], target: Path,
          width: int = 360, columns: int = 4) -> None:
    if not samples:
        return
    first = frame(video, samples[0][0], width)
    height = first.height
    cell_w, cell_h = width + 12, height + 46
    sheet = Image.new("RGB", (columns * cell_w, math.ceil(len(samples) / columns) * cell_h), "#151922")
    draw = ImageDraw.Draw(sheet)
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    font = ImageFont.truetype(str(font_path), 19) if font_path.exists() else ImageFont.load_default()
    for index, (time, label) in enumerate(samples):
        shot = first if index == 0 else frame(video, time, width)
        x, y = (index % columns) * cell_w + 6, (index // columns) * cell_h + 6
        sheet.paste(shot, (x, y))
        draw.text((x, y + height + 8), label, fill="white", font=font)
    sheet.save(target)


def analyze(video: Path, out: Path, threshold: float) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    info = json.loads(run([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video),
    ]).stdout)
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    fps = Fraction(stream["avg_frame_rate"])
    duration = float(stream.get("duration", info["format"]["duration"]))
    frames = int(stream.get("nb_frames", round(duration * fps)))
    result = run([
        "ffmpeg", "-hide_banner", "-i", str(video), "-an", "-vf",
        f"select='gt(scene,{threshold})',showinfo", "-f", "null", "-",
    ])
    log = result.stderr.decode("utf-8", errors="replace")
    (out / "scene-detection.log").write_text(log, encoding="utf-8")
    candidates = [float(t) for t in re.findall(r"pts_time:([\d.]+)", log)]
    boundaries = sorted(set([0] + [round(t * fps) for t in candidates] + [frames]))
    shots = []
    for i, (start, end) in enumerate(zip(boundaries, boundaries[1:]), 1):
        shots.append({
            "shot": i, "start_frame": start, "end_frame_exclusive": end,
            "start_sec": round(float(start / fps), 6),
            "end_sec": round(float(end / fps), 6),
            "duration_sec": round(float((end - start) / fps), 6),
            "review_status": "machine_candidate_not_verified",
        })
    report = {
        "source": str(video.resolve()), "width": stream["width"], "height": stream["height"],
        "fps": str(fps), "video_frames": frames, "video_duration_sec": duration,
        "container_duration_sec": float(info["format"]["duration"]),
        "scene_threshold": threshold, "shots": shots,
        "warning": "Scene candidates are not semantic cuts; visually verify boundaries, transitions and subtitle changes.",
    }
    (out / "technical-analysis.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out / "candidate-cuts.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(shots[0]))
        writer.writeheader()
        writer.writerows(shots)
    seconds = [(float(t), f"{t:02d}s | frame {round(t * fps):03d}") for t in range(math.ceil(duration)) if t < duration]
    for start in range(0, len(seconds), 12):
        board(video, seconds[start:start + 12], out / f"seconds-{start:02d}-{min(start+11,len(seconds)-1):02d}.jpg")
    midpoints = [((s["start_sec"] + s["end_sec"]) / 2,
                  f"cut {s['shot']:02d} | {s['start_sec']:.3f}-{s['end_sec']:.3f}") for s in shots]
    for start in range(0, len(midpoints), 12):
        board(video, midpoints[start:start+12], out / f"candidate-shots-{start+1:02d}.jpg")
    edges = []
    for boundary in boundaries[1:-1]:
        edges.extend([
            (float((boundary - 1) / fps), f"{boundary-1:03d} | before {boundary:03d}"),
            (float(boundary / fps), f"{boundary:03d} | after {boundary:03d}"),
        ])
    for start in range(0, len(edges), 16):
        board(video, edges[start:start+16], out / f"boundaries-{start//16+1:02d}.jpg", width=270, columns=4)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.18)
    arguments = parser.parse_args()
    data = analyze(arguments.video, arguments.out, arguments.threshold)
    print(json.dumps({k: v for k, v in data.items() if k != "shots"}, ensure_ascii=False))
    print(f"Candidate shots: {len(data['shots'])}")
