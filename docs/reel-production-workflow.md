# Moodstay Reel production flow

This is the persistent workflow used when the user names a lodging. Project folders are the source of truth; do not rely on chat history alone. Read the project's `workflow.json` first and resume from its `current_stage`.

## Stages and handoffs

| Stage | Work | Required project artifacts | Handoff |
|---|---|---|---|
| `property_selected` | Record the user's lodging name and intended angle. | `workflow.json` | Begin fact/source research. |
| `research_ready` | Verify current differentiators from public pages and guest/creator content; record URLs, access date, and uncertainty. | `research.md` | Select visual sources that prove the story. |
| `narration_ready` | Complete the unnamed-property story before visual selection; split its natural beats without making the wording serve the images. | `script.txt`, `narration.txt` | Design factual anchors and POV beats. |
| `timing_ready` | Create a Typecast narration draft and derive cut timing targets; raw clips retain handles for editing. | `typecast_timestamps.json`, `cut-map.md` | Build the exact still and Grok package. |
| `visual_plan_ready` | Assign real-property anchors and reference-grounded first-person AI stills to the completed story. AI POV is normally the majority of experiential cuts; document every reference source, generation status, and any intentional callback. | `photo_manifest.json`, `cut-map.md`, numbered 9:16 still assets (or an explicit external-asset handoff) | Write video prompts. |
| `generation_pack_ready` | Produce reference-style narration split into exactly 20 short shot lines and one English image-to-video prompt per cut. Reused stills still receive separate numbered clips/prompts so timing and edit choices can differ. | `script.txt`, `video_prompts.md` | User generates the 20 video clips. |
| `thumbnail_copy_pending` | Propose five cover-copy candidates based on the locked first still; record the user's selected option. | `thumbnail.json` | User generates clips; keep final cover creation for post-render. |
| `awaiting_generated_clips` | Confirm handoff instructions and preserve all inputs. | `workflow.json`, `clips/` folder | Wait for clips named 01–20. |
| `clips_verified` | Validate all 20 clips, sequence, duration, decode health, and any severe black/frozen frames. | `clip-check.json` | Run Typecast TTS and edit. |
| `rendered` | Synthesize one continuous Typecast narration with character timestamps; align 20 cuts and captions; render 1080×1920/30fps MP4. | `output/final_reel.mp4`, `output/captions.srt`, `output/typecast_timestamps.json` | Inspect final video/audio/subtitles. |
| `thumbnail_ready` | Create the selected 9:16 thumbnail from the first still/final first frame after video QA. | `output/thumbnail.png` | Package reel and posting metadata. |
| `qa_passed` | Confirm frame size/rate, all 20 cut changes, subtitle readability and sync, no unintended gaps, and audio ending. | `qa-report.md` | Deliver the file and mark the project complete. |

The stages are ordered and must not be skipped. Record incomplete or externally blocked work in `workflow.json` rather than marking it done. The user performs image-to-video generation outside this repository; a video prompt never counts as a received clip.

## New property procedure

1. The user provides only the lodging name to start. Optionally they may add a target audience, a non-negotiable angle, a price/deal fact, or owned property photos.
2. Create `projects/<property-slug>/` with `workflow.json`, `research.md`, `photo_manifest.json`, `cut-map.md`, `script.txt`, `video_prompts.md`, `still-pack/`, and `clips/.gitkeep`.
3. Research current lodging facts. Use official info when available and public guest/creator content where helpful. Log direct source URLs and which statements remain uncertain. Do not invent facilities, seasonal availability, rates, inclusions, or objective property facts.
4. Ask the user for roughly 8–15 property photos if they have not already supplied them. These are factual visual anchors, not a limit on the final cut count. Record subject, room type, source, and rights status in the manifest.
5. Write the complete short-form narration **before** selecting final images. Use the verified differentiator plus the fictional account persona to create a strong story: hook → relatable desire/conflict or discovery → the property solving/escalating that situation → concrete praise → experience-style verdict. Split it into about 20 natural spoken fragments. Do not distort the narration to fit available images. Preserve the unnamed-property/comment-curiosity rules in `AGENTS.md`; the spoken property name and direct comment CTA are prohibited. The user approves or revises this script before still generation.
6. Generate a Typecast narration draft and use its timestamps to set desired cut boundaries in `cut-map.md`. The user still generates roughly 5-second Grok clips to retain trim handles; the final edit trims them to the TTS timing. This timing pass prevents a good script from becoming an arbitrary sequence of equal-length clips.
7. Build the final visual plan from the approved script. Assign 4–8 real-photo anchors that prove actual exterior, room layout, amenity, food, and view. Assign first-person AI stills to the emotional, arrival, touch, rest, food, and transition beats—normally about 60–80% of the 20 final stills. Every AI still must be generated from the relevant verified property photo and must not fabricate or change factual details.
8. Deliver a complete `still-pack/` with one actual 9:16 image per cut, named `V01.png` through `V20.png`. This includes both supplied real-photo crops and generated POV stills. The user should never have to infer an AI scene from a text prompt alone. Identify each still's factual reference and generated status in `photo_manifest.json` and `cut-map.md`.
9. Write one English image-to-video prompt per cut and place it with the matching `V01`–`V20` asset. Treat that still as the exact source; preserve architecture, object identity, layout, materials, colors, people, and visible details. Default to a locked camera; if needed, permit only a nearly imperceptible, slow, steady 2D push or slide. No object/person/door/water/foliage animation, shake, sudden acceleration, zoom jumps, 3D orbit, parallax, or invented off-frame content. Build energy in the edit, not inside generated motion.
10. Once `V01` is locked, propose exactly five thumbnail-copy options. Save the user's selected option in `thumbnail.json`; do not create the final image until the final reel is QA-approved.
11. The user generates one vertical clip from each matching still+prompt in Grok, then places the results as `clips/V01.mp4` through `clips/V20.mp4`. Set `current_stage` to `awaiting_generated_clips` only after all generation-pack artifacts exist.
12. Once the clips arrive, verify them, render, inspect the final result, write QA findings, then create `output/thumbnail.png` from the selected copy and final first frame. Package a separate posting sheet with the caption, disclosure, pinned-comment/DM copy if requested, and the BGM handling choice. The editor does not silently add copyrighted BGM: either the user supplies licensed audio or adds an Instagram track at publishing.

## Cross-computer continuity

- Push Git-tracked project manifests, research citations, scripts, cut maps, prompts, and status to GitHub.
- Do not place credentials in project files. Use `TYPECAST_API_KEY` and `TYPECAST_VOICE_ID` environment variables on each computer.
- Clip inputs and rendered output are git-ignored. Transfer user-generated clips separately or recreate them on the next computer.
- Photo inputs are not automatically committed. If the source's rights permit GitHub redistribution, the user may explicitly authorize adding them; otherwise transfer the image ZIP separately or recreate the selected set from its documented source/manifest. The STAYFOLIO photo source in the current Stayboda project is recorded as not verified for public-repository redistribution.
- After cloning, read `workflow.json`, then follow this document and the property's `README.md`. Never restart completed work unless an artifact is missing or the user requests a revision.

## Current implementation boundary

`tools/render_reel.py` automates the final audiovisual stage: Typecast timestamp TTS, 20 ordered cuts, caption timing, vertical crop/scale, and MP4 encoding. Research and image selection are Codex-assisted and documented per project; the user currently generates the motion clips with an external image-to-video model. Instagram publishing/DM automation is out of scope.
