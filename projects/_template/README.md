# 새 릴스 프로젝트 템플릿

1. 이 폴더를 `projects/<주제명>/`으로 복사한다.
2. `script.txt`에 컷별 자막을 한 줄씩 쓴다. 문장부호는 넣지 않는다.
3. `narration.txt`에는 같은 문구를 자연스러운 한 문단으로 연결하고 쉼표와 마침표를 넣는다.
4. Typecast 키와 보이스 ID를 현재 PowerShell 세션에만 설정하고, 클립을 만들기 전에 `python tools/prepare_reel_timing.py projects/<주제명>`을 실행한다. 생성된 고정 음성·타임스탬프로 `cut-map.md`의 컷 길이를 확정한다.
5. `clips/01.mp4`부터 자막 줄 수만큼 영상을 넣는다.
6. `python tools/render_reel.py projects/<주제명> --speed 1.2`를 실행한다. 렌더러는 4단계에서 잠근 음성과 타임스탬프를 그대로 사용한다.

출력은 프로젝트의 `output/`에 생성된다. API 키와 영상·오디오는 Git에 올라가지 않는다.
