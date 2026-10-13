# 스테이 보다 릴스 렌더 작업 폴더

Typecast narration, narration-synced cuts, and burned-in Korean captions are produced from this folder.

To resume the full project on another computer, first read [`workflow.json`](workflow.json), [`cut-map.md`](cut-map.md), and [`video_prompts.md`](video_prompts.md). The selected photo ZIP currently remains outside GitHub at the local Codex `outputs/stayboda_vertical_20.zip` path; its source is documented in [`photo_manifest.json`](photo_manifest.json). Public-repository redistribution permission has not been verified, so the photos were intentionally not committed.

## Put generated clips here

Copy the 20 generated videos into `clips/` and name them in edit order:

```text
01.mp4
02.mp4
...
20.mp4
```

MOV and M4V are also accepted, but do not put two extensions for the same shot in the folder. Replace the 20 lines in `script.txt` with the narration/caption fragments in the same cut order. A line maps to the video with the same number.

## One-time setup

1. Install FFmpeg and FFprobe and make sure both commands work in PowerShell.
2. From the repository root, install the Typecast SDK:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Set your Typecast API key and chosen voice ID in the current PowerShell window. Do not paste the API key into chat or commit it:

   ```powershell
   $env:TYPECAST_API_KEY = "your-api-key"
   $env:TYPECAST_VOICE_ID = "tc_your_voice_id"
   ```

## Render

From the repository root:

```powershell
python tools/render_reel.py projects/stayboda-reel --dry-run
python tools/render_reel.py projects/stayboda-reel
```

The engine makes one Typecast request for a continuous voice track and character timestamps, then uses those timestamps to time the 20 cuts and captions. It renders a 1080×1920, 30fps H.264/AAC MP4 to `output/final_reel.mp4`, with the audio and subtitle/timing sidecars beside it. Short clips are extended by holding their last frame. Existing output is protected; inspect it first, then use `--force` only if you want to replace it.

The sample `script.txt` currently contains the 20-cut Stayboda draft. It can be changed to any new lodging narration, keeping exactly one non-empty line per clip.
