# 스테이 보다 20개 이미지→영상 프롬프트

각 번호 이미지를 같은 번호의 입력 이미지로 쓴다. 목표는 사진 속 물체를 움직이는 게 아니라 **원본 사진 위에서 카메라가 자연스럽게 움직이는 느낌**이다. Grok 출력은 6초이므로, 편집에서 앞부분의 1~2초를 사용한다. 특히 좌우 이동은 3D 공간을 새로 그리는 패닝/오비트 대신, 원본 사진을 평면으로 둔 작은 2D 슬라이드로 요청한다. 화면 가장자리에 새 공간이 필요해지면 생성하지 말고 프레임 안쪽으로 크롭한다.

## 생성기 설정 권장값

- Image/reference adherence: 가능한 한 높게
- Motion strength: 낮게 시작하고, 지정 동작이 보이지 않을 때만 조금 높이기
- Stylization/creativity: 최소 또는 끄기
- Camera motion: 꺼두거나 가장 약하게. 프롬프트의 미세한 2D 이동만 적용
- Mask/motion brush를 지원하면 움직일 대상만 지정하고 나머지는 고정 영역 처리
- Negative prompt 입력란이 있으면 각 프롬프트 뒤의 `AVOID` 문장을 그 칸에 넣기

1. **01.jpg** — `Use the uploaded photo as the exact visual source. Create a 2-second vertical 9:16 image-to-video clip. Preserve the same stay, mountain, garden, architecture, colors, lighting, and composition. Make only a very slow digital push-in toward the stay; allow faint movement only in leaves that are already visible. Keep all buildings and hard edges rigid and unchanged. AVOID: redesign, morphing, warping, bending, flicker, object duplication or removal, new objects, people, animals, invented off-frame scenery, perspective shift, text, logos, watermarks.`
2. **02.jpg** — `Use the uploaded photo as the exact visual source. Create a 2-second vertical 9:16 image-to-video clip. Preserve the moss garden, tree, building, stones, colors, lighting, and framing exactly. Add only a faint, natural breeze to leaves already visible; keep the ground, walls, and all architecture completely still. AVOID: changing the garden layout, adding plants or flowers, morphing, warping, flicker, new objects, people, animals, text, logos, watermarks, perspective shift.`
3. **03.jpg** — `Use the uploaded photo as the exact visual source. Create a 2-second vertical 9:16 image-to-video clip. Keep the room, furniture, window frames, garden, object count, colors, and lighting unchanged. Apply only a slow, subtle digital push toward the window; no depth reconstruction or parallax. AVOID: furniture movement, window distortion, changing the garden, morphing, warping, flicker, new objects, people, text, logos, watermarks, perspective shift.`
4. **04.jpg** — `Use this photo as the exact source. Make a very slow, gentle 2D camera slide from the table toward the window. Move only a small distance at a steady pace, with no sudden acceleration, shake or zoom. Keep the chairs, tableware, room and view fixed exactly as photographed. No 3D orbit, parallax or newly revealed areas; crop the edges if needed. Calm, comfortable motion. Vertical 9:16, 6 seconds.`
5. **05.jpg** — `Use this photo as the exact source. Make a smooth, quick 2D camera slide across the bed toward the window, using only the pixels already in the photo. Keep the bed, furniture, view and every visible detail fixed. No 3D orbit, parallax, or newly revealed areas; crop the edges if needed. Vertical 9:16, 6 seconds.`
6. **06.jpg** — `Use this photo as the exact source. Make a very slow, gentle 2D camera slide from the room toward the garden. Move only a small distance at a steady pace, with no sudden acceleration, shake or zoom. Keep the room, furniture and garden fixed exactly as photographed. No 3D orbit, parallax or newly revealed areas; crop the edges instead of inventing anything outside the photo. Calm, comfortable motion. Vertical 9:16, 6 seconds.`
7. **07.jpg** — `Use this photo as the exact source. Make a gentle camera push toward the sofa and tree, with a tiny natural sway only in leaves that are clearly visible. Keep the sofa, tree shape and room unchanged. No new leaves or objects. Vertical 9:16, 6 seconds.`
8. **08.jpg** — `Use this photo as the exact source. Make a smooth, quick camera push toward the beds. Keep both beds, bedding and every object fixed exactly as photographed. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
9. **09.jpg** — `Use this photo as the exact source. Make a smooth, quick 2D camera slide across the kitchen and dining area. Keep the table, chairs, cabinets and all items fixed exactly as photographed. No 3D orbit, parallax, or newly revealed areas. Vertical 9:16, 6 seconds.`
10. **10.jpg** — `Use this photo as the exact source. Make a smooth, quick camera slide across the kitchen. Keep the cabinets, appliances and room exactly as photographed; do not open or move anything. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
11. **11.jpg** — `Use this photo as the exact source. Make a smooth camera push toward the shelves and appliances. Keep every item fixed and unchanged. No new objects, 3D orbit or parallax. Vertical 9:16, 6 seconds.`
12. **12.jpg** — `Use this photo as the exact source. Make a short, smooth 2D slide across the open drawer. Keep the drawer and every utensil fixed exactly as photographed. No object movement, duplication or newly revealed areas. Vertical 9:16, 6 seconds.`
13. **13.jpg** — `Use this photo as the exact source. Make a gentle camera tilt from the sink toward the mirror. Keep the faucet, sink and all visible details fixed exactly as photographed; do not turn on the water. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
14. **14.jpg** — `Use this photo as the exact source. Make a smooth, quick 2D slide across the wooden cabinetry. Keep the cabinets and appliances fixed exactly as photographed; do not open anything. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
15. **15.jpg** — `Use this photo as the exact source. Make a smooth camera push toward the teacup. Keep the cup, deck and all other details fixed exactly as photographed. No steam, spills, new objects or 3D orbit. Vertical 9:16, 6 seconds.`
16. **16.jpg** — `Use this photo as the exact source. Make a smooth, quick camera push toward the coffee machine. Keep the machine, counter and every item fixed exactly as photographed. Do not operate it or add steam, coffee or cups. Vertical 9:16, 6 seconds.`
17. **17.jpg** — `Use this photo as the exact source. Make a smooth camera push toward the existing doorway. Keep the doorway, walls and room exactly as photographed; do not open a door or reveal another room. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
18. **18.jpg** — `Use this photo as the exact source. Make a smooth, quick 2D camera slide across the wooden hanger area. Keep the hanger and all visible items fixed exactly as photographed. Do not add clothing or reveal anything outside the photo. Vertical 9:16, 6 seconds.`
19. **19.jpg** — `Use this photo as the exact source. Make a smooth camera push toward the speaker. Keep the speaker and nearby details fixed exactly as photographed; do not make it vibrate or play. No 3D orbit or parallax. Vertical 9:16, 6 seconds.`
20. **20.jpg** — `Use this photo as the exact source. Make a smooth, slow camera push toward the bed. Keep the bed, bedding and room fixed exactly as photographed. No new objects, 3D orbit or parallax. Vertical 9:16, 6 seconds.`

## 재생성 기준

건축선·가구·소품 형태가 한 프레임이라도 휘거나 바뀌면 그 클립은 채택하지 말고 다시 생성한다. 다시 생성할 때는 우선 모션 강도를 낮추고, 움직임이 허용된 대상만 남기도록 프롬프트를 줄인다. 프롬프트는 변형을 줄이는 가이드이며, 생성기별 동작을 완전히 보장하지는 않는다.
