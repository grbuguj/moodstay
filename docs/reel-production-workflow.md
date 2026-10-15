# Moodstay Reel production flow

This is the persistent workflow used when the user names a lodging. Project folders are the source of truth; do not rely on chat history alone. Read the project's `workflow.json` first and resume from its `current_stage`.

## Stages and handoffs

| Stage | Work | Required project artifacts | Handoff |
|---|---|---|---|
| `property_selected` | Record the user's lodging name and intended angle. | `workflow.json` | Begin fact/source research. |
| `research_ready` | Verify current differentiators from public pages and guest/creator content; record URLs, access date, and uncertainty. | `research.md` | Select visual sources that prove the story. |
| `narration_ready` | Complete the unnamed-property story before visual selection; split its natural beats without making the wording serve the images. | `script.txt`, `narration.txt` | Design factual anchors and POV beats. |
| `timing_ready` | Lock the Typecast narration and derive cut timing targets; raw clips retain handles for editing. | `output/narration.wav`, `output/typecast_timestamps.json`, `cut-map.md` | Build the exact still and Grok package. |
| `visual_plan_ready` | Assign clean 9:16 crops of strong real-property photos first, then add reference-grounded first-person AI stills only for important missing actions or transitions. Document every reference source, generation status, and any intentional callback. | `photo_manifest.json`, `cut-map.md`, numbered 9:16 still assets (or an explicit external-asset handoff) | Write video prompts. |
| `generation_pack_ready` | Produce reference-style narration split into its natural short shot lines and one English image-to-video prompt per cut. Reused stills still receive separate numbered clips/prompts so timing and edit choices can differ. | `script.txt`, `video_prompts.md` | User generates the numbered video clips. |
| `awaiting_generated_clips` | Confirm handoff instructions and preserve all inputs. | `workflow.json`, `clips/` folder | Wait for clips named 01–NN. |
| `clips_verified` | Validate every expected clip's number, decode health, duration, orientation, and severe black/frozen warnings. | `clip-check.json` | Edit with the already locked Typecast TTS. |
| `rendered` | Reuse the locked Typecast narration and character timestamps to align cuts and captions; render 1080×1920/30fps MP4. | `output/final_reel.mp4`, `output/captions.srt`, `output/typecast_timestamps.json` | Perform final reel QA. |
| `reel_qa_passed` | Confirm frame size/rate, every cut change, subtitle readability and sync, no unintended gaps, and audio ending. | `qa-report.md` | Ask the user to choose cover copy. |
| `thumbnail_copy_pending` | After final reel QA, propose five cover-copy candidates based on the final first frame; record the user's selected option. | `thumbnail.json` | Create the final cover. |
| `thumbnail_ready` | Create the selected 9:16 thumbnail from the final first frame. | `output/thumbnail.png` | Package and deliver both files. |
| `delivered` | Confirm the final reel, thumbnail, captions, and posting sheet are present and readable. | `output/`, `posting.md` | Mark the project complete. |

The stages are ordered and must not be skipped. Record incomplete or externally blocked work in `workflow.json` rather than marking it done. The user performs image-to-video generation outside this repository; a video prompt never counts as a received clip.

## New property procedure

1. The user provides only the lodging name to start. Optionally they may add a target audience, a non-negotiable angle, a price/deal fact, or owned property photos.
2. Create `projects/<property-slug>/` with `workflow.json`, `research.md`, `photo_manifest.json`, `cut-map.md`, `script.txt`, `video_prompts.md`, `still-pack/`, and `clips/.gitkeep`.
3. Research current lodging facts. Use official info when available and public guest/creator content where helpful. Log direct source URLs and which statements remain uncertain. Do not invent facilities, seasonal availability, rates, inclusions, or objective property facts.
4. Ask the user for roughly 8–15 property photos if they have not already supplied them. These are factual visual anchors, not a limit on the final cut count. Record subject, room type, source, and rights status in the manifest.
5. Write the complete short-form narration **before** selecting final images. Use the verified differentiator plus the fictional account persona to create a strong story: hook → relatable desire/conflict or discovery → the property solving/escalating that situation → concrete praise → experience-style verdict. Split it only at natural spoken beats—usually 16–24, never padding weak beats just to reach a number. Do not distort the narration to fit available images. Preserve the unnamed-property/comment-curiosity rules in `AGENTS.md`; the spoken property name and direct comment CTA are prohibited. The user approves or revises this script before still generation.
6. Generate and listen to a Typecast narration draft. If pronunciation, breathing, or story rhythm is awkward, revise the script now and repeat this step. Once approved, lock that WAV and its timestamps, then use the timestamps to set desired cut boundaries in `cut-map.md`. Every Grok clip needs at least 0.5 seconds more source duration than its assigned spoken beat; split any beat that exceeds the generation length rather than freezing a frame. This timing pass prevents a good script from becoming an arbitrary sequence of equal-length clips.
7. Build the final visual plan from the approved script. First use clean 9:16 crops of every supplied photo that already communicates the required beat. Add first-person AI stills only for important arrival, touch, rest, food, or transition actions that the real photos cannot show. Do not target an AI percentage and do not create near-duplicate scenes by adding hands to the same background. Every AI still must be generated from the relevant verified property photo and must not fabricate or change factual details.
8. Deliver a complete `still-pack/` with one actual 9:16 image per cut, named `V01.png` through `VNN.png`. This includes both supplied real-photo crops and generated POV stills. The user should never have to infer an AI scene from a text prompt alone. Identify each still's factual reference and generated status in `photo_manifest.json` and `cut-map.md`.
9. Write one image-to-video prompt per **unique** still. Start with only a slow single-direction camera instruction such as `천천히 줌인` or `카메라 무빙 천천히 우측으로`; long scene descriptions and negative lists often destabilize the result. Add `원본 장면 유지` only after a real test changes the scene. Do not request object, person, door, water, or foliage animation unless the user specifically wants it.
10. The user generates one vertical clip per unique still. Record the downloaded filename and SHA-256 in `clip_manifest.json`, import it as `clips/01.mp4` onward, and map any later visual callbacks to the same clip with a different `source_start` in `render.json`. Set `current_stage` to `awaiting_generated_clips` only after all generation-pack artifacts exist.
11. Once the clips arrive, run `tools/verify_clips.py`, render, inspect the final result, and write QA findings. Then propose exactly five thumbnail-copy options based on the final first frame. Save the user's selected option in `thumbnail.json`.
12. Create `output/thumbnail.png` from the selected copy and final first frame, and deliver it together with the approved `output/final_reel.mp4`. Package a separate posting sheet with the caption, disclosure, and pinned-comment/DM copy if requested. The user adds BGM during Instagram publishing.

## Cross-computer continuity

- Push Git-tracked project manifests, research citations, scripts, cut maps, prompts, and status to GitHub.
- Do not place credentials in project files. Use `TYPECAST_API_KEY` and `TYPECAST_VOICE_ID` environment variables on each computer.
- Clip inputs and rendered output are git-ignored. Transfer user-generated clips separately or recreate them on the next computer.
- Photo inputs are not automatically committed. If the source's rights permit GitHub redistribution, the user may explicitly authorize adding them; otherwise transfer the image ZIP separately or recreate the selected set from its documented source/manifest. The STAYFOLIO photo source in the current Stayboda project is recorded as not verified for public-repository redistribution.
- After cloning, read `workflow.json`, then follow this document and the property's `README.md`. Never restart completed work unless an artifact is missing or the user requests a revision.

## Current implementation boundary

`tools/prepare_reel_timing.py` locks one Typecast narration WAV and its character timestamps after the script is approved and before any motion clips are generated. `tools/render_reel.py` reuses that exact locked timing for ordered cuts, captions, vertical crop/scale, and MP4 encoding. Research and image selection are Codex-assisted and documented per project; the user currently generates the motion clips with an external image-to-video model. Instagram publishing/DM automation is out of scope.
