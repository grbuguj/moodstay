"""Validate externally generated reel clips before the final render.

Usage:
  python tools/verify_clips.py projects/my-reel

Writes clip-check.json beside the project. Decode failures are errors; black,
frozen, unexpectedly short, and non-vertical clips are reported as warnings
for human review rather than silently passing into the final edit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from render_reel import find_clips, probe_duration, read_script, require_tool


def probe_video(ffprobe: str, clip: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries",
            "stream=codec_name,width,height,r_frame_rate:format=duration", "-of", "json", str(clip),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(result.stdout)
    stream = data.get("streams", [{}])[0]
    return {
        "codec": stream.get("codec_name"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "frame_rate": stream.get("r_frame_rate"),
        "duration": float(data.get("format", {}).get("duration", 0)),
    }


def inspect_filters(ffmpeg: str, clip: Path) -> list[str]:
    """Return conservative review warnings from FFmpeg's black/freeze detectors."""
    result = subprocess.run(
        [
            ffmpeg, "-hide_banner", "-nostats", "-i", str(clip), "-an",
            "-vf", "blackdetect=d=0.75:pix_th=0.10,freezedetect=n=0.003:d=1.25",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    lower = result.stderr.casefold()
    warnings: list[str] = []
    if "black_start:" in lower:
        warnings.append("black-frame segment detected; review before render")
    if "freeze_start:" in lower:
        warnings.append("frozen-frame segment detected; review before render")
    if result.returncode:
        warnings.append("FFmpeg could not fully decode this clip")
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    captions = read_script(project / "script.txt")
    clips = find_clips(project, len(captions))
    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")

    checks: list[dict[str, object]] = []
    errors: list[str] = []
    for index, clip in enumerate(clips, start=1):
        entry: dict[str, object] = {"index": index, "file": clip.name, "warnings": []}
        try:
            entry.update(probe_video(ffprobe, clip))
            duration = probe_duration(ffprobe, clip)
            if duration < 0.5:
                entry["warnings"].append("clip is under 0.5 seconds")
            if not isinstance(entry["width"], int) or not isinstance(entry["height"], int):
                errors.append(f"{clip.name}: no readable video stream")
            elif entry["height"] <= entry["width"]:
                entry["warnings"].append("not portrait; crop may be unattractive")
            entry["warnings"].extend(inspect_filters(ffmpeg, clip))
        except (subprocess.CalledProcessError, ValueError, OSError) as exc:
            entry["error"] = str(exc)
            errors.append(f"{clip.name}: decode/probe failed")
        checks.append(entry)

    report = {
        "expected_clip_count": len(captions),
        "checked_clip_count": len(checks),
        "errors": errors,
        "clips": checks,
    }
    out = project / "clip-check.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE: {out}")
    warning_count = sum(len(item.get("warnings", [])) for item in checks)
    print(f"Checked {len(checks)} clips: {len(errors)} error(s), {warning_count} warning(s)")
    return 2 if errors else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
