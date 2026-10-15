# Moodstay 릴스 완전 재현 가이드

새 컴퓨터에서 저장소를 클론한 뒤 동일한 제작 규칙으로 새 숙소 릴스를 만들거나 기존 프로젝트를 다시 렌더하는 단일 기준이다.

## 저장 범위

Git에는 계정 페르소나, 조사·대본·영상·썸네일 규칙, 프로젝트별 대본/프롬프트/컷맵/렌더 설정, 입력 파일명과 SHA-256, 자동화 코드와 테스트를 저장한다. API 키, 권리 미확인 사진·영상, Typecast WAV, 최종 MP4는 저장하지 않는다.

동일 미디어 파일이 있으면 렌더 설정과 편집 결과를 재현할 수 있다. 생성형 서비스 자체는 시드가 고정되지 않으므로 새로 생성한 픽셀까지 동일하다고 보장할 수 없다. 대신 `clip_manifest.json`의 SHA-256으로 동일 입력을 판별한다.

## 새 컴퓨터 설치

필수: Git, Python 3.11+, FFmpeg/FFprobe, `Noto Serif KR`, Typecast 계정.

```powershell
git clone https://github.com/grbuguj/moodstay.git
cd moodstay
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:TYPECAST_API_KEY = "로컬에서만 입력"
$env:TYPECAST_VOICE_ID = "tc_프로젝트설정을_덮어쓸때만_입력"
python tools/check_environment.py --project projects/vivacostay-reel
python -m unittest discover -s tools -p "test_*.py"
```

실제 API 키를 `.env`, 소스, 문서에 저장하지 않는다. 비밀이 아닌 보이스 ID는 재현성을 위해 프로젝트 `render.json`에 기록할 수 있고 환경변수로 덮어쓸 수 있다. 채팅이나 화면 공유에 노출된 API 키는 폐기하고 재발급한다.

## 전체 제작 흐름

### 1. 프로젝트 생성

```powershell
python tools/new_project.py my-stay-reel
```

숙소별 상태는 `projects/my-stay-reel/` 안에서 관리한다.

### 2. 사실 조사

`research.md`에 위치, 실제 시설, 시즌성, 가격/포함 혜택, 출처, 권리 상태를 기록한다. 화면으로 확인되지 않거나 출처가 충돌하는 정보는 대본에서 제외한다.

### 3. 대본

화자는 여행을 많이 다녀본 20대 여성이고, 친구에게 직접 다녀온 숨은 곳을 알려주는 말투다. 시설 목록보다 발견→공간 진입→낮→저녁→밤→개인적 결론의 흐름을 우선한다.

금지 사항:

- 내레이션/화면 자막에 숙소명 노출
- 직접 댓글 CTA
- 근거 없는 가격·무료 혜택·프라이빗·거리
- 억지 동행자·갈등·지인 추천·당일치기·1박 설정
- `A프레임`처럼 시청자가 쓰지 않는 내부 제작 용어

`script.txt`는 편집 컷마다 짧은 자막 한 줄을 넣고 문장부호를 뺀다. `narration.txt`는 동일한 단어를 자연스러운 한 문단으로 연결한다. 띄어쓰기·문장부호 외에 단어가 다르면 렌더러가 중단한다.

```powershell
python tools/validate_script.py projects/my-stay-reel/script.txt --property-name "실제 숙소명"
```

### 4. 이미지·영상 생성

- 실제 숙소 이미지를 구조와 시설의 사실 기준으로 사용한다.
- 가로 원본이 세로 크롭에서 핵심을 잃으면 세로 구도로 재구성한다.
- 장소가 주인공이다. AI 인물은 얼굴 없는 1인칭 손·발 정도로 제한한다.
- 고유 이미지만 영상화하고, 후반 콜백은 기존 영상을 재사용한다.
- 영상 프롬프트는 먼저 `천천히 줌인`, `카메라 무빙 천천히 우측으로`처럼 한 줄로 쓴다.
- 실제 결과가 흔들릴 때만 `원본 장면 유지`를 붙인다. 긴 설명과 금지 목록은 새 물체와 구조 변형을 유발할 수 있다.

영상은 5초, 세로 9:16을 기본으로 한다. 고유 영상과 사용 컷은 `video_prompts.md`, `cut-map.md`, `render.json`에 함께 기록한다.

### 5. 영상 수령·자동 매핑

`clip_manifest.json`에 다운로드 파일명, 프로젝트 파일명, SHA-256, 장면을 기록한다.

```powershell
python tools/import_clips.py projects/my-stay-reel C:\Downloads\영상_넣는곳
python tools/render_reel.py projects/my-stay-reel --dry-run
```

콜백은 `render.json`의 `cuts`에서 같은 파일과 다른 `source_start`를 지정한다. 영상을 복제하거나 다시 생성할 필요가 없다.

### 6. Typecast·편집

1. 자막 한 줄마다 TTS를 따로 요청하지 않는다.
2. `narration.txt` 전체를 한 번의 요청으로 생성한다.
3. 기본은 `normal` 프리셋과 Typecast 자체 `audio_tempo=1.2`다.
4. API의 `remove_silence_ms`는 쓰지 않는다. 압축된 오디오와 반환 타임스탬프가 달라질 수 있다.
5. 첫 발화 전 무음은 오디오와 영상에서 함께 제거한다.
6. 자막 시작 시점을 출력 FPS의 누적 정수 프레임으로 한 번 계산한다.
7. 같은 프레임 경계를 영상 컷과 ASS 자막에 공용하므로 둘이 동시에 전환된다.

승인된 대본은 영상 생성 전에 음성·타이밍을 먼저 잠근다.

```powershell
python tools/prepare_reel_timing.py projects/my-stay-reel
```

음성을 듣고 문제가 없을 때 영상들을 준비한 뒤, 같은 WAV와 타임스탬프를 재사용해 렌더한다.

```powershell
python tools/render_reel.py projects/my-stay-reel --reuse-tts
python tools/validate_render.py projects/my-stay-reel
```

TTS를 유지한 재렌더:

```powershell
python tools/render_reel.py projects/my-stay-reel --reuse-tts --force
```

특정 단어가 길어지는 경우(`따뜻한`, `불멍` 등) 음절을 자르지 않는다. `포근한`, `불 보면서 쉬면`처럼 자연스럽게 바꾸고 전체 TTS를 다시 만든다.

### 7. 자막·광고

- 자막은 화면 정중앙, 흰색 `Noto Serif KR`, 얇은 어두운 외곽선과 부드러운 그림자
- 문장부호 없이 2~5어절의 짧은 단위
- 우측 상단 `[광고]`는 본문보다 훨씬 작게
- 720×1264 기준 본문 48/광고 20, 1080×1920 기준 본문 72/광고 30

### 8. 썸네일

- 가장 강한 첫 장면
- 중앙 두 줄, 초굵은 흰색 한글, 두꺼운 검정 외곽선/그림자
- 숙소명 금지
- `[광고]`는 우측 상단에 아주 작고 저대비
- 카피는 시설 목록보다 장면의 반전. 비바코스테이 예: `풀장 보고 갔는데 / 밤이 더 미쳤다`

### 9. 게시 후

업로드 직후 성급히 수정하지 않는다. 충분히 배포된 뒤 조회수, 첫 3초 유지, 평균 시청 시간, 완주율, 저장, 공유, 프로필 방문을 함께 기록하고 다음 훅과 길이를 조정한다.

## 최종 QA

- 대본과 TTS 원문의 단어가 같은가
- 숙소명·직접 CTA·미확인 사실이 없는가
- 고유 영상 수와 편집 컷 수를 구분했는가
- `--dry-run`의 매핑이 맞는가
- TTS가 한 호흡으로 이어지고 장음 문제가 없는가
- 모든 자막/영상 전환이 같은 프레임인가
- 후반 콜백이 과하지 않은가
- 광고 표기가 콘텐츠를 방해하지 않는가
- 세로 프레임에서 핵심 공간이 잘리지 않는가
- 최종 파일에 H.264 영상과 AAC 음성이 있는가
- 썸네일이 피드 축소 상태에서도 읽히는가

## 실패 원인표

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 음절마다 끊김 | 자막별 TTS 요청 | 전체 내레이션을 한 번에 요청 |
| 특정 단어가 늘어짐 | 보이스 고유 운율 | 자연스러운 동의어로 교체 후 전체 재생성 |
| 자막과 영상이 따로 바뀜 | 경계를 따로 계산 | 공통 정수 프레임 경계 사용 |
| 뒤로 갈수록 싱크 밀림 | 컷 duration을 각각 반올림 | 누적 경계를 먼저 프레임 양자화 |
| 무음 제거 후 싱크 오류 | 오디오만 압축 | `remove_silence_ms` 사용 금지 |
| 새 물체·구조 변경 | 복잡한 영상 프롬프트 | 카메라 무브 한 줄부터 시작 |
| 후반 반복감 | 같은 장면 연속 재사용 | 콜백 시작점을 바꾸고 사이에 다른 장면 배치 |
| 광고 표기가 과함 | 큰 글자와 외곽선 | 작은 저대비 글자 사용 |

현재 기준 구현은 `projects/vivacostay-reel/`이다.
