"""Lock the Typecast audio and character timings before visual generation.

Usage:
  python tools/prepare_reel_timing.py projects/my-reel

The resulting output/narration.wav and output/typecast_timestamps.json are
the only audio/timing source used by render_reel.py.  Do this after the script
is approved, before generating Grok clips, so the visual cut map and final
render share the exact same clock.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from render_reel import (
    align_caption_segments,
    character_payload,
    generate_typecast_audio,
    read_script,
    write_srt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project folder with script.txt and optional narration.txt")
    parser.add_argument("--force", action="store_true", help="Replace an existing locked timing pass")
    args = parser.parse_args()

    folder = args.project.resolve()
    captions = read_script(folder / "script.txt")
    narration_path = folder / "narration.txt"
    narration = narration_path.read_text(encoding="utf-8-sig").strip() if narration_path.is_file() else " ".join(captions)
    output = folder / "output"
    output.mkdir(parents=True, exist_ok=True)
    audio_path = output / "narration.wav"
    timing_path = output / "typecast_timestamps.json"
    if not args.force and (audio_path.exists() or timing_path.exists()):
        raise FileExistsError("A timing pass already exists. Review it, or pass --force after changing the approved script.")

    print("Generating and locking Typecast narration timing...")
    response = generate_typecast_audio(narration, audio_path)
    characters = response.characters
    if not characters:
        raise RuntimeError("Typecast returned no character timestamps; cannot build a safe cut map.")
    duration = float(response.audio_duration)
    segments = align_caption_segments(captions, characters, duration)
    write_srt(output / "captions.srt", segments)
    timing_path.write_text(
        json.dumps(
            {
                "audio_duration": duration,
                "characters": character_payload(characters),
                "segments": [segment.__dict__ for segment in segments],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"LOCKED: {audio_path}\nTiming: {timing_path}\nCaptions: {output / 'captions.srt'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
