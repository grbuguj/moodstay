"""Render a Moodstay Reel with one continuous Typecast take and frame-exact cuts.

Project contract:
  script.txt      one caption per EDIT cut
  narration.txt   the same words as one naturally punctuated TTS paragraph
  clips/          unique generated clips
  render.json     optional settings and cut-to-clip mapping (callbacks supported)

Secrets are read only from TYPECAST_API_KEY and TYPECAST_VOICE_ID.
FFmpeg and FFprobe must be available on PATH.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence


DEFAULTS = {
    "video": {"width": 1080, "height": 1920, "fps": 30, "playback_speed": 1.0, "crf": 18},
    "typecast": {"model": "ssfm-v30", "emotion": "normal", "emotion_intensity": 1.0, "audio_tempo": 1.2, "target_lufs": -16.0},
    "subtitle": {"font_name": "Noto Serif KR", "font_size": 72, "outline": 2.7, "shadow": 7.5, "blur": 5.0},
    "ad": {"label": "[광고]", "font_name": "Noto Serif KR", "font_size": 30, "margin_right": 39, "margin_top": 39},
}


@dataclass(frozen=True)
class Segment:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Cut:
    clip: Path
    source_start: float = 0.35


def significant(char: str) -> bool:
    return not char.isspace() and not unicodedata.category(char).startswith("P")


def compact(text: str) -> str:
    return "".join(char for char in text if significant(char))


def read_script(path: Path) -> list[str]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        raise ValueError("script.txt must contain at least one non-empty line")
    return lines


def read_narration(folder: Path, captions: Sequence[str]) -> str:
    path = folder / "narration.txt"
    text = path.read_text(encoding="utf-8-sig").strip() if path.is_file() else " ".join(captions)
    if compact(text) != compact(" ".join(captions)):
        raise ValueError("narration.txt and script.txt must contain exactly the same spoken words; only spacing and punctuation may differ.")
    return text


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(folder: Path) -> dict:
    path = folder / "render.json"
    user = json.loads(path.read_text(encoding="utf-8-sig")) if path.is_file() else {}
    config = deep_merge(DEFAULTS, user)
    if config.get("schema_version", 1) not in (1, 2):
        raise ValueError("Unsupported render.json schema_version")
    if config.get("typecast", {}).get("remove_silence_ms") not in (None, 0):
        raise ValueError("Do not use Typecast remove_silence_ms: it can desynchronize returned timestamps from the compressed audio.")
    return config


def find_sequential_clips(folder: Path, count: int) -> list[Cut]:
    cuts: list[Cut] = []
    for index in range(1, count + 1):
        stem = f"{index:02d}"
        matches = [folder / "clips" / f"{stem}{ext}" for ext in (".mp4", ".mov", ".m4v")]
        present = [path for path in matches if path.is_file()]
        if len(present) != 1:
            found = ", ".join(path.name for path in present) or "none"
            raise FileNotFoundError(f"Expected exactly one clip for cut {stem}; found: {found}")
        cuts.append(Cut(present[0]))
    return cuts


def load_cuts(folder: Path, captions: Sequence[str], config: dict) -> list[Cut]:
    entries = config.get("cuts")
    if not entries:
        return find_sequential_clips(folder, len(captions))
    if len(entries) != len(captions):
        raise ValueError(f"render.json has {len(entries)} cuts but script.txt has {len(captions)} lines")
    clips_root = (folder / "clips").resolve()
    cuts: list[Cut] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or not entry.get("clip"):
            raise ValueError(f"render.json cut {index} must contain a clip filename")
        clip = (clips_root / str(entry["clip"])).resolve()
        if clips_root not in clip.parents:
            raise ValueError(f"render.json cut {index} points outside clips/: {entry['clip']}")
        if not clip.is_file():
            raise FileNotFoundError(f"Missing clip for cut {index}: {clip}")
        start = float(entry.get("source_start", 0.35))
        if start < 0:
            raise ValueError(f"source_start cannot be negative for cut {index}")
        cuts.append(Cut(clip, start))
    return cuts


def align_caption_segments(captions: Sequence[str], aligned_characters: Sequence[object], audio_duration: float) -> list[Segment]:
    timed_chars: list[tuple[str, float, float]] = []
    for item in aligned_characters:
        fragment = str(item.text)
        if not fragment:
            continue
        start, end = float(item.start), float(item.end)
        span = max(0.0, end - start)
        for i, char in enumerate(fragment):
            timed_chars.append((char, start + span * i / len(fragment), start + span * (i + 1) / len(fragment)))

    transcript = " ".join(captions)
    nonspace = [(char, i) for i, (char, _, _) in enumerate(timed_chars) if significant(char)]
    wanted = [char for char in transcript if significant(char)]
    if len(nonspace) != len(wanted) or any(actual[0] != expected for actual, expected in zip(nonspace, wanted)):
        raise ValueError("Typecast character alignment does not match script.txt; refusing to render unsynchronized captions.")

    segments: list[Segment] = []
    cursor = 0
    for caption in captions:
        count = len(compact(caption))
        picked = nonspace[cursor : cursor + count]
        if not picked:
            raise ValueError(f"No speech timing found for caption: {caption}")
        first, last = picked[0][1], picked[-1][1]
        segments.append(Segment(caption, timed_chars[first][1], min(timed_chars[last][2], audio_duration)))
        cursor += count
    return segments


def frame_boundaries(segments: Sequence[Segment], audio_duration: float, fps: int) -> tuple[float, list[int]]:
    first_speech = segments[0].start
    seconds = [0.0] + [max(0.0, segment.start - first_speech) for segment in segments[1:]] + [max(0.0, audio_duration - first_speech)]
    frames: list[int] = []
    for index, value in enumerate(seconds):
        frame = round(value * fps)
        if index:
            frame = max(frame, frames[-1] + 1)
        frames.append(frame)
    return first_speech, frames


def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_srt(path: Path, segments: Sequence[Segment]) -> None:
    cues: list[str] = []
    for index, segment in enumerate(segments, start=1):
        cues.extend((str(index), f"{srt_timestamp(segment.start)} --> {srt_timestamp(segment.end)}", segment.text, ""))
    path.write_text("\n".join(cues), encoding="utf-8-sig")


def write_ass(path: Path, captions: Sequence[str], frames: Sequence[int], config: dict) -> None:
    video, subtitle, ad = config["video"], config["subtitle"], config["ad"]
    fps, width, height = int(video["fps"]), int(video["width"]), int(video["height"])
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Moodstay,{subtitle['font_name']},{subtitle['font_size']},&H00FFFFFF,&H00000000,&H00101010,&H70000000,0,0,0,0,100,100,0,0,1,{subtitle['outline']},{subtitle['shadow']},5,44,44,0,1
Style: Ad,{ad['font_name']},{ad['font_size']},&H00FFFFFF,&H00000000,&H00101010,&H70000000,0,0,0,0,100,100,0,0,1,0.8,1.6,9,18,{ad['margin_right']},{ad['margin_top']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for index, caption in enumerate(captions):
        start, end = frames[index] / fps, frames[index + 1] / fps
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Moodstay,,0,0,0,,{{\\pos({width // 2},{height // 2})\\blur{subtitle['blur']}\\shad{subtitle['shadow']}}}{caption}")
    total = frames[-1] / fps
    events.append(f"Dialogue: 1,0:00:00.00,{ass_time(total)},Ad,,0,0,0,,{{\\blur1.2}}{ad['label']}")
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"{name} is required and must be available on PATH.")
    return path


def probe_duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], check=True, capture_output=True, text=True)
    return float(result.stdout.strip())


def generate_typecast_audio(text: str, out_path: Path, settings: dict):
    api_key = os.environ.get("TYPECAST_API_KEY")
    voice_id = os.environ.get("TYPECAST_VOICE_ID") or settings.get("voice_id")
    if not api_key or not voice_id:
        raise RuntimeError("Set TYPECAST_API_KEY in the current shell and provide TYPECAST_VOICE_ID either in the shell or render.json.")
    try:
        from typecast import Typecast
        from typecast.models import Output, PresetPrompt, TTSModel, TTSRequestWithTimestamps
    except ImportError as exc:
        raise RuntimeError("Typecast SDK missing. Install with: python -m pip install -r requirements.txt") from exc
    if settings.get("model", "ssfm-v30").casefold() != "ssfm-v30":
        raise ValueError("This workflow currently supports Typecast ssfm-v30 only")
    request = TTSRequestWithTimestamps(
        text=text,
        voice_id=voice_id,
        model=TTSModel.SSFM_V30,
        language="kor",
        prompt=PresetPrompt(emotion_type="preset", emotion_preset=str(settings.get("emotion", "normal")), emotion_intensity=float(settings.get("emotion_intensity", 1.0))),
        output=Output(target_lufs=float(settings.get("target_lufs", -16.0)), audio_tempo=float(settings.get("audio_tempo", 1.2)), audio_format="wav"),
    )
    response = Typecast(api_key=api_key).text_to_speech_with_timestamps(request, granularity="char")
    response.save_audio(str(out_path))
    return response


def save_alignment(path: Path, narration: str, audio_duration: float, characters: Sequence[object]) -> None:
    payload = {
        "narration": narration,
        "audio_duration": audio_duration,
        "characters": [{"text": str(item.text), "start": float(item.start), "end": float(item.end)} for item in characters],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_alignment(path: Path, narration: str) -> tuple[float, list[object]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if compact(str(payload.get("narration", ""))) != compact(narration):
        raise ValueError("Saved Typecast alignment belongs to different narration text")
    characters = [SimpleNamespace(**item) for item in payload.get("characters", [])]
    if not characters:
        raise ValueError("Saved Typecast alignment has no characters")
    return float(payload["audio_duration"]), characters


def ffmpeg_filter_path(path: Path) -> str:
    return path.name.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def render_aligned_video(ffmpeg: str, cuts: Sequence[Cut], audio: Path, ass: Path, first_speech: float, frames: Sequence[int], config: dict, output: Path, workdir: Path) -> None:
    video = config["video"]
    fps, width, height = int(video["fps"]), int(video["width"]), int(video["height"])
    speed, crf = float(video.get("playback_speed", 1.0)), int(video.get("crf", 18))
    if speed <= 0:
        raise ValueError("video.playback_speed must be positive")
    durations = [(frames[i + 1] - frames[i]) / fps for i in range(len(cuts))]
    inputs: list[str] = []
    for cut in cuts:
        inputs.extend(("-i", str(cut.clip)))
    audio_index = len(cuts)
    inputs.extend(("-i", str(audio)))
    filters: list[str] = []
    labels: list[str] = []
    for index, (cut, duration) in enumerate(zip(cuts, durations)):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]trim=start={cut.source_start:.6f},setpts=PTS-STARTPTS,setpts=PTS/{speed:.6f},fps={fps},"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1,"
            f"tpad=stop_mode=clone:stop_duration=60,trim=duration={duration:.6f},setpts=PTS-STARTPTS[{label}]"
        )
        labels.append(f"[{label}]")
    filters.append(f"{''.join(labels)}concat=n={len(cuts)}:v=1:a=0[vbase]")
    filters.append(f"[vbase]subtitles=filename='{ffmpeg_filter_path(ass)}'[vout]")
    total = frames[-1] / fps
    filters.append(f"[{audio_index}:a]atrim=start={first_speech:.6f},asetpts=PTS-STARTPTS,atrim=duration={total:.6f},asetpts=PTS-STARTPTS[aout]")
    command = [
        ffmpeg, "-hide_banner", "-y", *inputs, "-filter_complex", ";".join(filters),
        "-map", "[vout]", "-map", "[aout]", "-t", f"{total:.6f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(output),
    ]
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        lines = result.stderr.strip().splitlines()
        causes = [line for line in lines if any(word in line.casefold() for word in ("error", "invalid", "failed"))]
        raise RuntimeError("FFmpeg render failed: " + " | ".join(causes[-8:] or lines[-8:]))


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Validate project files without calling Typecast")
    parser.add_argument("--force", action="store_true", help="Replace output/final_reel.mp4")
    parser.add_argument("--reuse-tts", action="store_true", help="Reuse output/narration.wav and output/typecast_timestamps.json")
    parser.add_argument("--speed", type=float, help="Override render.json video.playback_speed")
    parser.add_argument("--ad-label", help="Override the top-right disclosure text")
    args = parser.parse_args()

    folder = args.project.resolve()
    captions = read_script(folder / "script.txt")
    narration = read_narration(folder, captions)
    config = load_config(folder)
    if args.speed is not None:
        config["video"]["playback_speed"] = args.speed
    if args.ad_label is not None:
        config["ad"]["label"] = args.ad_label
    cuts = load_cuts(folder, captions, config)
    ffmpeg, ffprobe = require_tool("ffmpeg"), require_tool("ffprobe")

    if args.dry_run:
        print(f"VALID: {len(set(cut.clip for cut in cuts))} unique clips -> {len(cuts)} edit cuts/captions")
        for index, (cut, caption) in enumerate(zip(cuts, captions), start=1):
            print(f"{index:02d}  {cut.clip.name} @ {cut.source_start:.2f}s  |  {caption}")
        print(f"Output: {config['video']['width']}x{config['video']['height']} @ {config['video']['fps']}fps")
        print(f"Typecast: one continuous request, normal preset, tempo {config['typecast']['audio_tempo']}x, no API silence compression")
        return 0

    output_dir = folder / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_video = output_dir / "final_reel.mp4"
    if output_video.exists() and not args.force:
        raise FileExistsError(f"{output_video} exists; pass --force after reviewing the current file")
    audio_path = output_dir / "narration.wav"
    timestamps_path = output_dir / "typecast_timestamps.json"
    if args.reuse_tts:
        if not audio_path.is_file() or not timestamps_path.is_file():
            raise FileNotFoundError("--reuse-tts needs output/narration.wav and output/typecast_timestamps.json")
        audio_duration, characters = load_alignment(timestamps_path, narration)
    else:
        print("Generating one continuous Typecast narration...")
        response = generate_typecast_audio(narration, audio_path, config["typecast"])
        characters = list(response.characters or [])
        if not characters:
            raise RuntimeError("Typecast returned no character timestamps")
        audio_duration = probe_duration(ffprobe, audio_path)
        save_alignment(timestamps_path, narration, audio_duration, characters)

    segments = align_caption_segments(captions, characters, audio_duration)
    first_speech, frames = frame_boundaries(segments, audio_duration, int(config["video"]["fps"]))
    ass_path = output_dir / "captions.ass"
    write_ass(ass_path, captions, frames, config)
    for index, cut in enumerate(cuts, start=1):
        duration = probe_duration(ffprobe, cut.clip)
        if duration <= cut.source_start + 0.05:
            raise ValueError(f"Cut {index} starts after clip end: {cut.clip.name} @ {cut.source_start:.2f}s / {duration:.2f}s")

    print("Rendering frame-aligned video/caption transitions...")
    render_aligned_video(ffmpeg, cuts, audio_path, ass_path, first_speech, frames, config, output_video, output_dir)
    rendered = probe_duration(ffprobe, output_video)
    expected = frames[-1] / int(config["video"]["fps"])
    if abs(rendered - expected) > 1 / int(config["video"]["fps"]) + 0.01:
        raise RuntimeError(f"Final duration mismatch: expected {expected:.3f}s, got {rendered:.3f}s")
    print(f"DONE: {output_video}")
    print(f"Cuts/captions: {len(cuts)} | duration: {rendered:.3f}s | TTS: {audio_path} | captions: {ass_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
