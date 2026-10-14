# 연화문호텔 양양 Grok 영상 프롬프트

각 프롬프트에 해당 V 이미지를 한 장씩 넣는다. 생성 영상은 4~5초여도 최종 편집에서는 컷 맵 구간만 사용한다.

## 공통 규칙

```text
Vertical 9:16 realistic smartphone travel footage. Preserve the exact architecture, layout, furniture, colors and objects in the input image. Natural subtle handheld motion only. Do not add or remove people, hands, furniture, signs, text, logos, decorations or architectural elements. No morphing, warping, object duplication, dramatic cinematic movement or artificial depth-of-field.
```

| V | 개별 프롬프트 |
|---|---|
| V01 | `Very gentle forward push toward the water courtyard. Fountain streams flow naturally and blossom branches move slightly in a light breeze. Keep the camera nearly level.` |
| V02 | `Slow, subtle forward drift over the illuminated water. Fountain arcs and reflections move naturally; lantern brightness stays stable.` |
| V03 | `A short handheld walking motion along the black stepping-stone path, moving forward only. Water ripples gently beside the path.` |
| V04 | `Tiny rightward pan across the broad pale-turquoise water toward the hanok building. Fountain water flows naturally; no new objects appear.` |
| V05 | `Hold mostly still on the small wooden boat. The boat moves only a few centimeters with the water while fountain arcs continue smoothly.` |
| V06 | `First-person guest gently slides the wooden lattice door farther open and takes one small step into the room. Keep the visible hand anatomically stable and secondary.` |
| V07 | `Very slow push from the low table toward the large window. Outside fountain water moves softly while the room remains perfectly unchanged.` |
| V08 | `Brief steady night shot with a slight forward drift. Lantern reflections shimmer and fountain streams continue naturally.` |
| V09 | `Subtle lateral move along the glowing water edge. Keep the hanok lights stable while reflections and water provide the only noticeable movement.` |
| V10 | `Slowly lean closer to the window as if admiring the courtyard at night. Exterior fountain water and reflections move naturally; preserve the room exactly.` |
| V11 | `One small forward step into the room. Keep all doors, lanterns, pebbles and furniture fixed with no geometry changes.` |
| V12 | `Almost locked camera with a very slight push toward the low tea table and circular landscape feature. No object movement.` |
| V13 | `Gentle forward movement through the doorway toward the bedroom, as if filmed while quietly looking around. Preserve all room details.` |
| V14 | `Small sideways handheld shift across the low table and floor cushion. Keep the bath and room layout unchanged.` |
| V15 | `Slowly move forward from the sitting area toward the bedroom doorway. No doors move and no objects appear.` |
| V16 | `Very slight tilt down to emphasize the large bath, then hold. Water remains calm with only tiny natural surface movement.` |
| V17 | `The existing wall spout continues filling the bath. Show realistic flowing water and expanding ripples only; keep every fixture and the window unchanged.` |
| V18 | `Locked relaxing shot of the filled bath. Only faint natural water movement; no steam, hands, feet, petals or props.` |
| V19 | `Tiny slow pan from the low table toward the bath, like a guest deciding to stay inside. Preserve all furniture and lighting.` |
| V20 | `Gentle pullback from the illuminated courtyard for a calm ending. Fountain arcs and reflections move naturally; end on a stable frame suitable for looping.` |

## 편집 주의

- Grok 결과의 앞 0.2~0.4초가 흔들리면 잘라내고 안정된 부분부터 사용한다.
- V01/V02/V05/V10/V17/V20은 핵심 컷이라 구조 변형이나 물체 추가가 보이면 재생성한다.
- V02와 V20은 같은 이미지를 사용하지만 동작은 `전진`과 `후퇴`로 달리해 의도적인 회수처럼 보이게 한다.
