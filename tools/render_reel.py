"""Render a variable-shot vertical Reel with Typecast narration and aligned captions.

Input folder contract:
  clips/01.mp4 ... clips/NN.mp4
  script.txt (one non-empty caption/narration fragment per shot)

Timing is prepared before clips are generated with tools/prepare_reel_timing.py.
The final render reuses that exact narration WAV and character timestamps;
it never synthesizes a second, potentially different voice track.

FFmpeg and FFprobe must be available on PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


FPS = 30
WIDTH = 1080
HEIGHT = 1920


@dataclass(frozen=True)
class Segment:
    text: str
    start: float
    end: float


def read_script(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise ValueError("script.txt must contain at least one non-empty line")
    return lines


def find_clips(folder: Path, shot_count: int) -> list[Path]:
    clips_dir = folder / "clips"
    clips: list[Path] = []
    for index in range(1, shot_count + 1):
        stem = f"{index:02d}"
        matches = [clips_dir / f"{stem}{ext}" for ext in (".mp4", ".mov", ".m4v")]
        present = [path for path in matches if path.is_file()]
        if len(present) != 1:
            found = ", ".join(path.name for path in present) or "none"
            raise FileNotFoundError(f"Expected exactly one clip named {stem}.mp4/.mov/.m4v in {clips_dir}; found: {found}")
        clips.append(present[0])
    valid = {f"{index:02d}" for index in range(1, shot_count + 1)}
    extra = [p.name for p in clips_dir.iterdir() if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".m4v"} and p.stem not in valid]
    if extra:
        raise ValueError("Unexpected video filenames in clips/: " + ", ".join(sorted(extra)))
    return clips


def align_caption_segments(captions: Sequence[str], aligned_characters: Sequence[object], audio_duration: float) -> list[Segment]:
    """Map exact caption text to Typecast character-level timestamps."""
    def significant(char: str) -> bool:
        return not char.isspace() and not unicodedata.category(char).startswith("P")

    aligned_text = "".join(str(item.text) for item in aligned_characters)
    transcript = " ".join(captions)
    if aligned_text != transcript:
        # Some services omit whitespace alignment. Support that without guessing timings.
        compact_aligned = "".join(ch for ch in aligned_text if significant(ch))
        compact_transcript = "".join(ch for ch in transcript if significant(ch))
        if compact_aligned != compact_transcript:
            raise ValueError("Typecast character alignment does not match script.txt; refusing to burn unsynchronized captions.")

    # Expand grouped fragments into character timing entries, preserving each fragment's interval.
    timed_chars: list[tuple[str, float, float]] = []
    for item in aligned_characters:
        fragment = str(item.text)
        if not fragment:
            continue
        start, end = float(item.start), float(item.end)
        span = max(0.0, end - start)
        for i, char in enumerate(fragment):
            timed_chars.append((char, start + span * i / len(fragment), start + span * (i + 1) / len(fragment)))

    # Compare non-space characters and retain indices back to the timed array.
    nonspace = [(char, i) for i, (char, _, _) in enumerate(timed_chars) if significant(char)]
    wanted = [(char, i) for i, char in enumerate(transcript) if significant(char)]
    if len(nonspace) != len(wanted) or any(a[0] != b[0] for a, b in zip(nonspace, wanted)):
        raise ValueError("Typecast character alignment could not be mapped to script.txt.")

    segments: list[Segment] = []
    cursor = 0
    for caption in captions:
        count = sum(significant(char) for char in caption)
        picked = nonspace[cursor : cursor + count]
        if not picked:
            raise ValueError(f"No speech timing found for caption: {caption}")
        first_index, last_index = picked[0][1], picked[-1][1]
        start = timed_chars[first_index][1]
        end = timed_chars[last_index][2]
        if end <= start:
            raise ValueError(f"Invalid speech timing for caption: {caption}")
        segments.append(Segment(caption, start, min(end, audio_duration)))
        cursor += count
    return segments


def srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(path: Path, segments: Sequence[Segment]) -> None:
    cues = []
    for index, segment in enumerate(segments, start=1):
        cues.extend((str(index), f"{srt_timestamp(segment.start)} --> {srt_timestamp(segment.end)}", segment.text, ""))
    path.write_text("\n".join(cues), encoding="utf-8-sig")


def character_payload(characters: Sequence[object]) -> list[dict[str, float | str]]:
    """Persist the minimal Typecast character timing contract as JSON."""
    return [
        {"text": str(item.text), "start": float(item.start), "end": float(item.end)}
        for item in characters
    ]


def load_timing(path: Path) -> tuple[float, list[object]]:
    """Load the locked preflight timing without depending on Typecast classes."""
    from types import SimpleNamespace

    data = json.loads(path.read_text(encoding="utf-8"))
    duration = float(data["audio_duration"])
    characters = [
        SimpleNamespace(text=item["text"], start=float(item["start"]), end=float(item["end"]))
        for item in data["characters"]
    ]
    if duration <= 0 or not characters:
        raise ValueError(f"Invalid or empty Typecast timing file: {path}")
    return duration, characters


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} is required and must be available on PATH.")
    return path


def generate_typecast_audio(text: str, out_path: Path):
    api_key = os.environ.get("TYPECAST_API_KEY")
    voice_id = os.environ.get("TYPECAST_VOICE_ID")
    if not api_key or not voice_id:
        raise RuntimeError("Set TYPECAST_API_KEY and TYPECAST_VOICE_ID before rendering. Do not put API keys in job files or commit them.")
    try:
        from typecast import Typecast
        from typecast.models import Output, SmartPrompt, TTSModel, TTSRequestWithTimestamps
    except ImportError as exc:
        raise RuntimeError("Typecast SDK missing. Install with: python -m pip install -r requirements.txt") from exc

    client = Typecast(api_key=api_key)
    request = TTSRequestWithTimestamps(
        text=text,
        voice_id=voice_id,
        model=TTSModel.SSFM_V30,
        language="kor",
        prompt=SmartPrompt(emotion_type="smart"),
        output=Output(volume=None, target_lufs=-16.0, audio_format="wav"),
    )
    response = client.text_to_speech_with_timestamps(request, granularity="char")
    response.save_audio(str(out_path))
    return response


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def ffmpeg_filter_path(path: Path) -> str:
    # Keep the SRT path relative to the project working directory to avoid drive-letter escaping.
    return path.name.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def render_video(ffmpeg: str, clips: Sequence[Path], audio: Path, srt: Path, segments: Sequence[Segment], output: Path, workdir: Path, audio_duration: float | None = None, speed: float = 1.0, ad_label: str = "[광고]") -> None:
    boundaries = [0.0] + [segment.start for segment in segments[1:]]
    # Preserve the real end of the voice file. Cutting at the last spoken Korean
    # character can chop its trailing punctuation, breath, or natural release.
    total = audio_duration if audio_duration is not None else segments[-1].end
    if total < segments[-1].end:
        raise ValueError("Audio duration cannot end before the final caption.")
    boundaries.append(total)
    durations = [max(0.05, boundaries[i + 1] - boundaries[i]) for i in range(len(clips))]

    inputs: list[str] = []
    for clip in clips:
        inputs.extend(("-i", str(clip)))
    audio_index = len(clips)
    inputs.extend(("-i", str(audio)))

    filters = []
    video_labels = []
    for index, duration in enumerate(durations):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS},setpts=(PTS-STARTPTS)/{speed:.6f},"
            f"trim=duration={duration:.6f},tpad=stop_mode=clone:stop_duration={duration:.6f},"
            f"trim=duration={duration:.6f},setpts=PTS-STARTPTS[{label}]"
        )
        video_labels.append(f"[{label}]")
    filters.append(f"{''.join(video_labels)}concat=n={len(clips)}:v=1:a=0[vbase]")
    srt_filter_path = ffmpeg_filter_path(srt)
    filters.append(
        f"[vbase]subtitles=filename='{srt_filter_path}':force_style="
        "'FontName=Noto Serif KR,FontSize=72,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "BorderStyle=1,Outline=2,Shadow=6,Alignment=5,MarginL=80,MarginR=80,MarginV=0'[vcaption]"
    )
    escaped_ad = ad_label.replace("'", r"\'").replace(":", r"\:")
    filters.append(
        "[vcaption]drawtext=text='" + escaped_ad + "':font='Noto Serif KR':fontsize=30:"
        "fontcolor=white:borderw=1:bordercolor=black@0.8:x=w-text_w-42:y=42[vout]"
    )
    filter_complex = ";".join(filters)
    command = [
        ffmpeg, "-hide_banner", "-y", *inputs,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", f"{audio_index}:a:0",
        "-t", f"{total:.6f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-af", "loudnorm=I=-14:TP=-1.0:LRA=7",
        "-movflags", "+faststart", str(output),
    ]
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        detail = result.stderr.strip().splitlines()
        causes = [line for line in detail if any(word in line.casefold() for word in ("error", "invalid", "failed"))]
        raise RuntimeError("FFmpeg render failed: " + " | ".join(causes[-8:] or detail[-8:]))


def main() -> int:
    # Windows PowerShell may use a legacy console code page; paths and help include Korean.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Reel project folder with script.txt and consecutively numbered clips")
    parser.add_argument("--dry-run", action="store_true", help="Validate files and print the render plan without calling Typecast")
    parser.add_argument("--force", action="store_true", help="Allow replacing generated files in the project's output/ folder")
    parser.add_argument("--speed", type=float, default=1.0, help="Visual playback speed inside each cut (for example 1.2)")
    parser.add_argument("--ad-label", default="[광고]", help="Small disclosure label shown in the top-right")
    args = parser.parse_args()

    folder = args.project.resolve()
    script_path = folder / "script.txt"
    if not script_path.is_file():
        raise FileNotFoundError(f"Missing {script_path}")
    captions = read_script(script_path)
    clips = find_clips(folder, len(captions))
    ffmpeg = require_tool("ffmpeg")
    ffprobe = require_tool("ffprobe")
    output_dir = folder / "output"
    output_video = output_dir / "final_reel.mp4"

    if args.dry_run:
        print(f"VALID: {len(clips)} clips and {len(captions)} caption lines")
        for i, (clip, caption) in enumerate(zip(clips, captions), start=1):
            print(f"{i:02d}  {clip.name}  |  {caption}")
        print("Locked Typecast timing -> aligned cuts -> burned-in subtitles -> H.264/AAC 1080x1920 @ 30fps")
        return 0

    if output_video.exists() and not args.force:
        raise FileExistsError(f"{output_video} already exists. Review it, then pass --force to replace it.")
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / "narration.wav"
    srt_path = output_dir / "captions.srt"
    timestamps_path = output_dir / "typecast_timestamps.json"

    if not audio_path.is_file() or not timestamps_path.is_file():
        raise FileNotFoundError(
            "Missing locked Typecast preflight. Run: python tools/prepare_reel_timing.py <project>"
        )
    print("Loading locked Typecast narration and character timings...")
    duration, characters = load_timing(timestamps_path)
    segments = align_caption_segments(captions, characters, duration)
    write_srt(srt_path, segments)

    # Verify every input can supply its assigned interval; short videos are safely extended with a held final frame.
    print("Checking clip durations...")
    for clip, segment in zip(clips, segments):
        available = probe_duration(ffprobe, clip)
        if available < 0.15:
            raise ValueError(f"Clip is too short or invalid: {clip}")
        if available + 0.02 < segment.end - segment.start:
            print(f"  {clip.name}: {available:.2f}s -> will hold final frame to cover {segment.end - segment.start:.2f}s")

    print("Rendering vertical video...")
    render_video(ffmpeg, clips, audio_path, srt_path, segments, output_video, output_dir, audio_duration=duration, speed=args.speed, ad_label=args.ad_label)
    print(f"DONE: {output_video}")
    print(f"Audio: {audio_path}\nCaptions: {srt_path}\nTiming: {timestamps_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
