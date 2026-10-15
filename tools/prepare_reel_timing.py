"""Generate and lock one continuous Typecast take before motion editing."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from render_reel import (
    align_caption_segments,
    frame_boundaries,
    generate_typecast_audio,
    load_config,
    probe_duration,
    read_narration,
    read_script,
    require_tool,
    save_alignment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--force", action="store_true", help="Replace an existing locked timing pass")
    args = parser.parse_args()
    folder = args.project.resolve()
    captions = read_script(folder / "script.txt")
    narration = read_narration(folder, captions)
    config = load_config(folder)
    output = folder / "output"
    output.mkdir(parents=True, exist_ok=True)
    audio = output / "narration.wav"
    timing = output / "typecast_timestamps.json"
    plan = output / "timing_plan.json"
    if not args.force and (audio.exists() or timing.exists() or plan.exists()):
        raise FileExistsError("A timing pass already exists; review it or pass --force after changing the approved script")

    print("Generating and locking one continuous Typecast narration...")
    response = generate_typecast_audio(narration, audio, config["typecast"])
    characters = list(response.characters or [])
    if not characters:
        raise RuntimeError("Typecast returned no character timestamps")
    duration = probe_duration(require_tool("ffprobe"), audio)
    save_alignment(timing, narration, duration, characters)
    segments = align_caption_segments(captions, characters, duration)
    first_speech, frames = frame_boundaries(segments, duration, int(config["video"]["fps"]))
    fps = int(config["video"]["fps"])
    payload = {
        "audio_duration": duration,
        "first_speech": first_speech,
        "fps": fps,
        "boundary_frames": frames,
        "cuts": [
            {
                "cut": index + 1,
                "caption": caption,
                "start_frame": frames[index],
                "end_frame": frames[index + 1],
                "duration": (frames[index + 1] - frames[index]) / fps,
            }
            for index, caption in enumerate(captions)
        ],
    }
    plan.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"LOCKED: {audio}\nTiming: {timing}\nPlan: {plan}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
