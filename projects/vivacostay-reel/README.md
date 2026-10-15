# 양평 비바코스테이 릴스 재현 프로젝트

2026-10-15 실제 제작본에서 확정한 대본, 16개 고유 영상→19개 편집 컷 매핑, Typecast 설정, 자막 스타일, 영상 프롬프트, 썸네일·게시문 규칙을 보존한다.

## 재현

1. 현재 PowerShell 세션에 `TYPECAST_API_KEY`를 설정한다. 비밀이 아닌 보이스 ID는 `render.json`에 기록되어 있으며 환경변수로 덮어쓸 수 있다.
2. `python tools/prepare_reel_timing.py projects/vivacostay-reel`로 승인된 TTS와 프레임별 컷 길이를 먼저 잠근다.
3. 생성 영상 16개를 한 폴더에 받는다.
4. `python tools/import_clips.py projects/vivacostay-reel <다운로드폴더>`를 실행한다. 파일명과 SHA-256이 맞으면 `clips/01.mp4`~`16.mp4`로 복사된다.
5. `python tools/render_reel.py projects/vivacostay-reel --dry-run`으로 16개 고유 영상이 19개 컷에 올바르게 매핑됐는지 확인한다.
6. `python tools/render_reel.py projects/vivacostay-reel --reuse-tts`를 실행한다.
7. TTS를 바꾸지 않고 영상·자막 설정만 다시 렌더할 때는 `--reuse-tts --force`를 사용한다.

최종 파일: `projects/vivacostay-reel/output/final_reel.mp4`

원본 사진·생성 영상·음성·완성 MP4는 권리와 용량 문제로 Git에 넣지 않는다. 대신 파일명, 해시, 매핑과 모든 생성 규칙을 기록한다.
