# Anima Prompt Data Strings

카테고리: `EasyUse Anima/Prompt`

입력:

- `EASYUSE_ANIMA_PROMPT_DATA`

출력:

- `positive_prompt`
- `negative_prompt`
- `anima_mod_guidance_quality_tags`
- `anima_mod_guidance_negative_prompt`
- `metadata_prompt`
- `metadata_negative_prompt`
- `global_prompt`
- `positive_without_artist_section`
- `negative_without_artist_section`
- `artist_tags`
- `artist_weighted_tags`
- `artist_mix_prompt`
- `artist_mix_mode`

`EASYUSE_ANIMA_PROMPT_DATA` dict에서 자주 필요한 문자열 값을 각각 꺼내는
노드입니다. 기존 문자열 기반 workflow 구간이나 텍스트 표시 노드에 v2 prompt
data를 연결할 때 사용합니다.

`EASYUSE_ANIMA_PROMPT_DATA` 노드는 prompt data를 통과시키면서 기존 Advanced
호환 출력, Boolean, width/height까지 펼칩니다. `Anima Prompt Data Strings`는
문자열 출력만 필요할 때 쓰는 더 단순한 추출 노드입니다.

## Artist 관련 출력

- `global_prompt`: artist mix를 사용할 때 base positive prompt로 쓰기 좋은 문자열입니다.
- `positive_without_artist_section`: Advanced artist field가 제거된 positive prompt입니다.
- `artist_tags`: Advanced artist field의 작가 태그 문자열입니다.
- `artist_weighted_tags`: 가중치 문법을 보존한 작가 태그 문자열입니다.
- `artist_mix_prompt`: artist mix conditioning에서 사용할 작가 태그 문자열입니다.
- `artist_mix_mode`: prompt data에 저장된 artist mix mode 문자열입니다.

작가 태그 기준은 `@` 접두사가 아니라 Advanced의 artist field 또는 standalone
노드의 `artist_tags` 입력칸입니다.
