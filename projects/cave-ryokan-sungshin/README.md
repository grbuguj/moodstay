# 새 릴스 프로젝트 템플릿

1. 저장소 루트에서 `python tools/new_project.py <주제명>`을 실행한다.
2. `research.md`에 검증된 사실과 출처를 기록한다.
3. `script.txt`에 편집 컷별 화면 자막을 한 줄씩 쓴다. 문장부호는 넣지 않는다.
4. `narration.txt`에는 **동일한 단어**를 자연스러운 한 문단으로 연결해 쉼표와 마침표만 넣는다.
5. Typecast 키를 현재 셸에만 설정하고 `python tools/prepare_reel_timing.py projects/<주제명>`으로 승인된 음성과 타임스탬프를 먼저 잠근다.
6. 고유 이미지별 영상 프롬프트를 `video_prompts.md`에 적는다. 콜백 컷은 재생성하지 않는다.
7. 고유 영상은 `clips/01.mp4`부터 넣고, 편집 컷과 파일의 관계는 `render.json`의 `cuts`에 적는다.
8. `python tools/render_reel.py projects/<주제명> --dry-run`으로 매핑을 검증한다.
9. `python tools/render_reel.py projects/<주제명> --reuse-tts`로 잠근 음성을 사용해 렌더한다.

출력은 `output/`에 생성된다. API 키, 원본 이미지, 영상, 음성, 최종 MP4는 Git에 넣지 않는다.
