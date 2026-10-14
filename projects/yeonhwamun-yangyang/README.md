# 연화문호텔 양양 릴스 프로젝트

현재 단계: `upscaled_visual_pack_ready`

승인 대본과 Typecast 음성(32.05초)을 잠갔고, 자막과 영상 컷 경계를 같은 프레임으로 맞췄다. 20개의 9:16 스틸은 원본 세로 크롭 16컷과 AI 보완 4컷으로 구성한다. 같은 외관에 손만 추가한 중복 시안은 폐기했다.

화질이 낮았던 고유 원본 세로 크롭 15컷은 구도 보존 방식으로 AI 복원했고, 기존 AI 보완 4컷은 그대로 유지했다. V20은 복원한 V02의 엔딩 회수본이다. Grok 입력에는 `still-pack-upscaled/V01.png`부터 `V20.png`까지 사용하며, 기존 `still-pack/`은 원본 보존본으로 남긴다.

다음 작업: `video_prompts.md`에 따라 V01~V20을 Grok에서 영상화하고 승인본을 `clips/01.mp4`부터 `clips/20.mp4`까지 넣는다. 이후 검증과 최종 렌더링을 진행한다.

로컬 전달 팩: `output/yeonhwamun-yangyang-grok-pack-upscaled.zip` (Git 제외). 전체 검수 이미지는 `output/upscaled-still-contact-sheet.jpg`다. 사진과 생성 영상은 재배포 권리가 확인되지 않았으므로 공개 GitHub에 커밋하지 않는다.
