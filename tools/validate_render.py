"""Validate final Reel media and contiguous caption events."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

from render_reel import load_config, read_script


TIME = re.compile(r"(?P<h>\d+):(?P<m>\d+):(?P<s>\d+)\.(?P<cs>\d+)")


def seconds(value: str) -> float:
    match = TIME.fullmatch(value)
    if not match:
        raise ValueError(f"Invalid ASS timestamp: {value}")
    parts = {key: int(number) for key, number in match.groupdict().items()}
    return parts["h"] * 3600 + parts["m"] * 60 + parts["s"] + parts["cs"] / 100


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required")
    video = project / "output" / "final_reel.mp4"
    ass = project / "output" / "captions.ass"
    captions = read_script(project / "script.txt")
    config = load_config(project)
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-count_frames", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_frames:format=duration", "-of", "json", str(video)],
        check=True, capture_output=True, text=True,
    )
    media = json.loads(probe.stdout)
    streams = media["streams"]
    visual = next((stream for stream in streams if stream["codec_type"] == "video"), None)
    audio = next((stream for stream in streams if stream["codec_type"] == "audio"), None)
    if not visual or visual.get("codec_name") != "h264":
        raise ValueError("Final video must contain H.264 video")
    if not audio or audio.get("codec_name") != "aac":
        raise ValueError("Final video must contain AAC audio")
    expected_size = (int(config["video"]["width"]), int(config["video"]["height"]))
    if (int(visual["width"]), int(visual["height"])) != expected_size:
        raise ValueError(f"Wrong dimensions: expected {expected_size}, got {(visual['width'], visual['height'])}")
    events = []
    for line in ass.read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("Dialogue: 0,"):
            fields = line.split(",", 9)
            events.append((seconds(fields[1]), seconds(fields[2]), fields[9]))
    if len(events) != len(captions):
        raise ValueError(f"Expected {len(captions)} caption events, got {len(events)}")
    if any(event[2].split("}")[-1] != caption for event, caption in zip(events, captions)):
        raise ValueError("ASS caption text/order differs from script.txt")
    max_gap = max(abs(events[index][1] - events[index + 1][0]) for index in range(len(events) - 1)) if len(events) > 1 else 0.0
    if max_gap > 0.011:
        raise ValueError(f"Caption events are not contiguous; max gap {max_gap:.3f}s")
    duration = float(media["format"]["duration"])
    if abs(events[-1][1] - duration) > 0.011:
        raise ValueError(f"Caption/video end mismatch: {events[-1][1]:.3f}s vs {duration:.3f}s")
    print(f"PASS: H.264/AAC {visual['width']}x{visual['height']} {visual['r_frame_rate']}, {len(events)} contiguous captions, {duration:.3f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
