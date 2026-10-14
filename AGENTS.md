# Moodstay content-generation instructions

When the user supplies only a lodging name, treat it as a request to continue the production workflow in [`docs/reel-production-workflow.md`](docs/reel-production-workflow.md), not merely write a standalone script. Create or resume a property project, research current differentiators, select and document about 20 strong portrait photo candidates, arrange them into a story, write narration split into short shot lines, write one video-generation prompt per cut, and persist the state/artifacts in that project. Usually give each cut a distinct image, but intentionally reuse a memorable image later when it strengthens the story or creates a visual callback. Then wait for the user-generated clips and use `tools/render_reel.py` for Typecast narration, timing-aligned edits, subtitles, and final rendering. Do not ask for a brief unless a missing detail blocks useful work.

Keep every phase explicit and truthful: a source page is not proof of image redistribution rights; a prompt is not a generated clip; a render command succeeding is not final QA. Never claim a stage is complete without its named artifact/check. Do not commit photo/video assets to a public GitHub repository unless the user's rights specifically permit that redistribution. Store reusable prompts, scripts, source links, selection rationale, rights status, and resume state in Git-tracked project files. Keep API keys out of Git and chat.

Non-negotiable output rules:

- Never say the lodging's proper name in the narration. The unanswered identity is part of the comment strategy.
- Do not append a direct comment CTA such as “여기 어딘지 궁금하면 댓글로 물어봐요,” “댓글에 정보 남겨주세요,” or “DM 보내드릴게요.” The supplied references do not use those endings.
- End with an experience-style personal verdict that resolves the story, not a question or sales CTA.
- Use the user's supplied examples as structural references, not text to copy.
- Research the property's actual differentiators; do not invent amenities, prices, inclusions, seasonal availability, or personal incidents.
- Keep all narration clean and ready to paste into Typecast. Keep the property name and citations outside the spoken block.
