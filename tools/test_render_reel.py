"""Focused tests for cut-to-caption timing and SRT output."""

from __future__ import annotations

import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

from render_reel import (
    Cut,
    DEFAULTS,
    Segment,
    align_caption_segments,
    frame_boundaries,
    read_narration,
    read_script,
    render_aligned_video,
    srt_timestamp,
    write_ass,
    write_srt,
)


class RenderReelTests(unittest.TestCase):
    def test_character_timestamps_map_to_each_caption(self):
        captions = ["산속에", "정원이 있어요."]
        transcript = " ".join(captions)
        chars = [SimpleNamespace(text=ch, start=i * 0.1, end=(i + 1) * 0.1) for i, ch in enumerate(transcript)]
        segments = align_caption_segments(captions, chars, audio_duration=2.0)
        self.assertEqual([segment.text for segment in segments], captions)
        self.assertAlmostEqual(segments[0].start, 0.0)
        self.assertAlmostEqual(segments[0].end, 0.3)
        self.assertAlmostEqual(segments[1].start, 0.4)
        self.assertAlmostEqual(segments[1].end, 1.1)

    def test_alignment_mismatch_fails_instead_of_misaligning_subtitles(self):
        chars = [SimpleNamespace(text=ch, start=0.0, end=0.1) for ch in "잘못된 문장"]
        with self.assertRaisesRegex(ValueError, "does not match"):
            align_caption_segments(["원래 대사"], chars, audio_duration=1.0)

    def test_srt_uses_timed_captions(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "captions.srt"
            from render_reel import Segment

            write_srt(path, [Segment("안녕하세요.", 1.25, 2.5)])
            text = path.read_text(encoding="utf-8-sig")
            self.assertIn("00:00:01,250 --> 00:00:02,500", text)
            self.assertIn("안녕하세요.", text)

    def test_script_accepts_variable_non_empty_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "script.txt"
            path.write_text("\n".join(f"대사 {n}" for n in range(1, 16)), encoding="utf-8")
            self.assertEqual(len(read_script(path)), 15)
            path.write_text("하나\n둘\n", encoding="utf-8")
            self.assertEqual(read_script(path), ["하나", "둘"])
            path.write_text("\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "at least one"):
                read_script(path)

    def test_srt_timestamp_rounds_to_milliseconds(self):
        self.assertEqual(srt_timestamp(61.2346), "00:01:01,235")

    def test_narration_must_match_caption_words(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "narration.txt").write_text("서울에서 30분이면, 좋아요.", encoding="utf-8")
            self.assertEqual(read_narration(root, ["서울에서", "30분이면", "좋아요"]), "서울에서 30분이면, 좋아요.")
            (root / "narration.txt").write_text("서울에서 한 시간이면 좋아요.", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "same spoken words"):
                read_narration(root, ["서울에서", "30분이면", "좋아요"])

    def test_boundaries_are_monotonic_whole_frames(self):
        segments = [Segment("하나", 0.2, 0.5), Segment("둘", 0.2, 0.8), Segment("셋", 0.21, 1.0)]
        first, frames = frame_boundaries(segments, audio_duration=1.2, fps=24)
        self.assertAlmostEqual(first, 0.2)
        self.assertEqual(frames[0], 0)
        self.assertTrue(all(right > left for left, right in zip(frames, frames[1:])))

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg is not installed")
    def test_ffmpeg_renders_reused_clips_with_frame_aligned_captions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clip_template = root / "template.mp4"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=navy:s=270x480:r=30:d=1", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip_template)],
                check=True,
            )
            cuts = [Cut(clip_template, 0.0), Cut(clip_template, 0.1), Cut(clip_template, 0.2)]
            audio = root / "narration.wav"
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=2", "-t", "2", str(audio)],
                check=True,
            )
            captions = ["첫 컷", "두 번째", "마지막"]
            frames = [0, 15, 30, 48]
            config = {
                **DEFAULTS,
                "video": {**DEFAULTS["video"], "width": 270, "height": 480, "fps": 30},
                "subtitle": {**DEFAULTS["subtitle"], "font_size": 18},
                "ad": {**DEFAULTS["ad"], "font_size": 10},
            }
            ass = root / "captions.ass"
            write_ass(ass, captions, frames, config)
            output = root / "final.mp4"
            render_aligned_video(shutil.which("ffmpeg"), cuts, audio, ass, 0.0, frames, config, output, root)
            self.assertTrue(output.is_file())
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.stdout.strip(), "270x480")


if __name__ == "__main__":
    unittest.main()
