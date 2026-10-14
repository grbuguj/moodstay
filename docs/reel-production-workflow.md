# Moodstay Reel production flow

This is the persistent workflow used when the user names a lodging. Project folders are the source of truth; do not rely on chat history alone. Read the project's `workflow.json` first and resume from its `current_stage`.

## Stages and handoffs

| Stage | Work | Required project artifacts | Handoff |
|---|---|---|---|
| `property_selected` | Record the user's lodging name and intended angle. | `workflow.json` | Begin fact/source research. |
| `research_ready` | Verify current differentiators from public pages and guest/creator content; record URLs, access date, and uncertainty. | `research.md` | Select visual sources that prove the story. |
| `photos_selected` | Select about 20 visually strong camera photos (not collages or graphic edits); maintain provenance and rights status. Distinct images are preferred, not mandatory. | `photo_manifest.json`, numbered vertical image assets (or an explicit external-asset handoff) | Arrange them into a story. |
| `storyboard_ready` | Set one image per cut in narrative order. Reuse a photo only intentionally—for example, as a brief callback or to reinforce a key visual—and document the repeated source/cut numbers. | `cut-map.md` | Write the narration against the selected visuals. |
| `generation_pack_ready` | Produce reference-style narration split into exactly 20 short shot lines and one English image-to-video prompt per cut. Reused stills still receive separate numbered clips/prompts so timing and edit choices can differ. | `script.txt`, `video_prompts.md` | User generates the 20 video clips. |
| `awaiting_generated_clips` | Confirm handoff instructions and preserve all inputs. | `workflow.json`, `clips/` folder | Wait for clips named 01–20. |
| `clips_verified` | Validate all 20 clips, sequence, duration, decode health, and any severe black/frozen frames. | `clip-check.json` | Run Typecast TTS and edit. |
| `rendered` | Synthesize one continuous Typecast narration with character timestamps; align 20 cuts and captions; render 1080×1920/30fps MP4. | `output/final_reel.mp4`, `output/captions.srt`, `output/typecast_timestamps.json` | Inspect final video/audio/subtitles. |
| `qa_passed` | Confirm frame size/rate, all 20 cut changes, subtitle readability and sync, no unintended gaps, and audio ending. | `qa-report.md` | Deliver the file and mark the project complete. |

The stages are ordered and must not be skipped. Record incomplete or externally blocked work in `workflow.json` rather than marking it done. The user performs image-to-video generation outside this repository; a video prompt never counts as a received clip.

## New property procedure

1. Create `projects/<property-slug>/` with `workflow.json`, `research.md`, `photo_manifest.json`, `cut-map.md`, `script.txt`, `video_prompts.md`, and `clips/.gitkeep`.
2. Check current lodging facts quickly. Use official info when available and public guest/creator content where helpful. Log direct source URLs and which statements remain uncertain. Do not invent facilities, seasonal availability, rates, inclusions, or personal incidents.
3. Select roughly 20 visually strong portrait photos. Reject collages, text/graphics, watermarks, and images that do not support the narration. Keep source URL and rights status for each photo. Do not hide a watermark with a crop. Prefer varied, distinct visuals, but retain candidates that may work as an intentional callback.
4. Crop accepted originals to 9:16 portrait. Assign final cut numbers only after choosing the story order. A photo may appear again if the repeat has a clear editorial purpose (such as a quick callback near the ending); note the source image and every cut that reuses it in `photo_manifest.json` and `cut-map.md`. Reuse must not be accidental filler. `01` in every project artifact must refer to the same cut.
5. Write the short-form narration after image selection. Split into 20 consecutive spoken fragments, one per cut, preserving the user's reference pacing and unnamed-property/comment-curiosity rules in `AGENTS.md`. The spoken property name and direct comment CTA are prohibited.
6. Write one English video-generation prompt per image. Every prompt must use the exact image as its sole visual source, lock architecture/object identity/layout/materials/colors, and specify only a restrained action for named, already-visible elements. Natural localized actions (such as a visible hinged door opening slightly or an existing faucet starting to run) are allowed when requested; all other scene details stay fixed. Forbid morphing, warping, flicker, object duplication/removal, invented off-frame content, and text/logos. Prefer high image adherence, low motion, and a mask over the moving object when supported. Keep prompt numbers aligned with `script.txt` and `cut-map.md`.
7. Set `current_stage` to `awaiting_generated_clips` only after all generation-pack artifacts exist. Tell the user exactly where to place the clips. Do not generate the Typecast audio until clips are received and the user has configured a Typecast API key and voice ID locally.
8. Once the clips arrive, verify them, render, inspect the final result, write QA findings, and update `workflow.json` at every completed handoff.

## Cross-computer continuity

- Push Git-tracked project manifests, research citations, scripts, cut maps, prompts, and status to GitHub.
- Do not place credentials in project files. Use `TYPECAST_API_KEY` and `TYPECAST_VOICE_ID` environment variables on each computer.
- Clip inputs and rendered output are git-ignored. Transfer user-generated clips separately or recreate them on the next computer.
- Photo inputs are not automatically committed. If the source's rights permit GitHub redistribution, the user may explicitly authorize adding them; otherwise transfer the image ZIP separately or recreate the selected set from its documented source/manifest. The STAYFOLIO photo source in the current Stayboda project is recorded as not verified for public-repository redistribution.
- After cloning, read `workflow.json`, then follow this document and the property's `README.md`. Never restart completed work unless an artifact is missing or the user requests a revision.

## Current implementation boundary

`tools/render_reel.py` automates the final audiovisual stage: Typecast timestamp TTS, 20 ordered cuts, caption timing, vertical crop/scale, and MP4 encoding. Research and image selection are Codex-assisted and documented per project; the user currently generates the motion clips with an external image-to-video model. Instagram publishing/DM automation is out of scope.
