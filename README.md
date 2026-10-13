# moodstay

국내 숙소를 소개하는 인스타그램 릴스 제작 자료 저장소입니다.

현재 포함된 첫 프로젝트는 `스타빌 제주`입니다. 숙소명을 영상 본문에서 직접 공개하지 않고, 강한 첫 훅으로 댓글 반응을 유도하는 큐레이션형 릴스 포맷을 사용합니다.

## 구성

- `docs/reel-production-playbook.md` — 오늘 확정한 계정 톤, 대본 및 썸네일 규칙
- `AGENTS.md` / `docs/script-generation-engine.md` — 숙소명 입력부터 레퍼런스형 대본 생성까지의 실행 규칙
- `projects/starville-jeju/` — 대본, 19컷 매칭, 영상 프롬프트
- `assets/starville-jeju/9x16/` — 릴스 입력용 1080×1920 PNG 19장
- `docs/reference-style-spec.md` — 2026-10-13 레퍼런스 실측, 제작 단계와 편집 데이터 구조
- `tools/analyze_reference.py` — 로컬 영상의 프레임·장면 경계·검수 보드 분석 도구
- `tools/validate_script.py` — 숙소명 노출·직접 댓글 CTA·엔딩 형식 검사기

## 핵심 원칙

1. 숙소명은 릴스 본문에서 공개하지 않는다.
2. 자막이 전환되면 이미지도 반드시 새 원본으로 전환한다.
3. 이미지 링크가 아니라, 검수된 실제 9:16 로컬 이미지로 작업한다.
4. 텍스트·로고·워터마크가 박힌 이미지는 영상 소스에서 제외한다.
5. 첫 1초는 기능 설명보다 강한 의외성으로 시작한다.

## 레퍼런스 분석

원본 영상 파일이 있을 때 FFmpeg, ffprobe, Pillow가 설치된 환경에서 실행한다.

```text
python tools/analyze_reference.py reference.mp4 --out analysis
```

분석 도구는 네트워크나 계정 접근을 하지 않는다. 자동 탐지한 컷은 후보이며 검수 후 확정한다. 이미지 수집부터 최종 렌더링까지의 전체 자동화는 아직 구현되지 않았다.

대본 규칙 검사:

```text
python tools/validate_script.py projects/starville-jeju/script.md --property-name "제주 스타빌"
```

이 저장소의 `AGENTS.md`는 Codex가 숙소명만 입력받았을 때 조사 후 이름을 감춘 대본을 생성하도록 규정한다. Python 검사기는 이름 노출, 직접 댓글 CTA, 질문형 엔딩만 자동 점검하며 사실조사나 문장 품질을 대신하지 않는다.
