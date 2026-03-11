# 에피소드 자동 생성 오케스트레이터

에피소드를 8단계 파이프라인으로 자동 생성합니다.
모든 단계가 완전 자동(AUTO)으로 실행되며, 휴먼 트리거 없이 끝까지 진행합니다.

---

## 인자 파싱

`$ARGUMENTS`에서 프로젝트와 에피소드 번호를 파싱합니다.

| 입력 | 해석 |
|------|------|
| `ssulhwa EP-05` | 프로젝트=ssulhwa, 에피소드=EP-05 |
| `EP-05` | 프로젝트=자동감지, 에피소드=EP-05 |
| `ssulhwa 5` | 프로젝트=ssulhwa, 에피소드=EP-05 |

**프로젝트 자동 감지**: 인자가 에피소드 번호 1개만이면, 루트 디렉토리에서 `*/project.yaml`을 검색하여 프로젝트가 1개뿐이면 자동 사용.

---

## 실행 전 준비

### MCP 도구 탐색
가장 먼저 `ToolSearch("mcp")`를 실행하여 `ask_codex`와 `ask_gemini` MCP 도구를 발견하세요.
- 발견되면: 멀티모델 라우팅 활성화 (Codex=QC, Gemini=문체리뷰/이미지프롬프트)
- 발견 안 되면: Claude 에이전트로 전체 폴백 (정상 동작)

### 프로젝트 설정 로드
`{project}/project.yaml`을 Read로 읽어 format/lore/context 설정을 파악합니다.
이 설정은 이후 모든 Stage에서 에이전트 프롬프트에 주입됩니다.

### 에피소드 번호 정규화
- "EP-05" → ep_num=5, ep_tag="EP-05"
- "EP-5" → ep_num=5, ep_tag="EP-05"
- "5" → ep_num=5, ep_tag="EP-05"

---

## Stage 1: 컨텍스트 조립

Python 헬퍼로 컨텍스트를 자동 추출합니다.

**실행:**
```bash
python workflow/context_assembly.py {project} EP-{ep_num:02d}
```

**결과 파싱:** JSON 출력에서 다음을 추출:
- `project`: 프로젝트명
- `outline`: 해당 EP 아웃라인
- `ep_title`: 에피소드 제목
- `prev_ending_hook`: 직전 EP 엔딩 훅
- `characters`: 등장 캐릭터 설정
- `world`: 관련 세계관 설정
- `style_guide`: 문체 가이드
- `previous_ending`: 직전 에피소드 마지막 500자
- `format`: 분량/형식 설정

**폴백 (스크립트 실패 시):**
직접 로어 파일들을 Read로 읽어서 수동 조립:
- `{project}/lore/episode-outline.md` → 해당 EP 아웃라인 추출
- `{project}/lore/plot-beats.md` → 해당 EP 씬 비트시트 추출 (존재하면)
- `{project}/lore/characters.md` → 아웃라인에 언급된 캐릭터만
- `{project}/lore/world.md` → 키워드 기반 관련 섹션만
- `{project}/lore/style-guide.md` → 전체
- 직전 에피소드 파일 → 마지막 500자

---

## Stage 2: 초고 생성 (씬 분할 생성)

LLM은 한국어 순수 9,000자를 단일 생성으로 달성하지 못합니다 (Claude/GPT 모두 ~5,500~6,500자 한계).
따라서 **씬별로 분할 생성 후 병합**합니다.

### Step 2-1: 씬 분할 계획

plot-beats.md에서 해당 EP의 씬 비트시트를 파싱하여 씬 수와 분량 배분을 확인합니다.
- 씬 수: 보통 4개 (기승전결)
- 분량 배분: plot-beats.md의 비중(%) × format.char_count 목표
- 예) 목표 10,000자, 씬1 20% = 2,000자, 씬2 35% = 3,500자, 씬3 30% = 3,000자, 씬4 15% = 1,500자

### Step 2-2: 씬별 병렬 생성

각 씬을 **별도 Task로 병렬 호출**합니다. 씬 1과 나머지는 직전 씬의 마지막 문장이 필요하므로,
**씬 1을 먼저 생성 → 나머지 씬을 병렬 생성** (또는 전체 순차 생성).

단, plot-beats.md에 오프닝/클리프행어 설계가 있으므로 각 씬의 시작/끝이 이미 정의되어 있어 **병렬 생성이 가능**합니다.

**씬 1 (헤더 포함) Task 호출:**
```
Task(
  subagent_type="draft-writer",
  model="sonnet",
  prompt=아래 프롬프트
)
```

**씬 1 프롬프트:**
```
당신은 웹소설 "{context.project}"의 집필 에이전트입니다.

## 임무
{ep_tag}의 **씬 1만** 작성하세요. 이 에피소드의 첫 번째 씬입니다.

## ⚠️ 분량 (절대 규칙)
- 순수 글자 수(공백/줄바꿈 제거) **최소 {씬1_target}자 이상**
- 공백 포함으로는 약 {씬1_target * 1.32}자 이상 작성 필요
- 20문단 이상 목표

## 출력 형식 (씬 1은 헤더 포함)
```markdown
# {ep_tag}: {제목}

> {한줄요약}

---

[씬 1 본문]

[IMG:유형-설명]
```
헤더/요약/첫 구분자를 포함하고, 씬 1 끝에서 멈추세요. --- 로 끝내지 마세요.

## 씬 1 비트
{plot_beats에서 씬 1 비트 추출}

## 직전 에피소드 연결
{context.prev_ending_hook 또는 "(첫 화)"}

## 참조 자료
{캐릭터, 세계관, 문체 가이드 — 파일 경로 전달하여 에이전트가 Read}
```

**씬 2~N 프롬프트 (병렬):**
```
## 임무
{ep_tag}의 **씬 {N}만** 작성하세요.

## ⚠️ 분량
- 순수 글자 수 최소 {씬N_target}자 이상

## 출력 형식
[씬 N 본문만 출력. 헤더/구분자 없이 본문만]
[IMG:유형-설명] (해당 씬에 배치할 마커가 있으면)

## 씬 {N} 비트
{plot_beats에서 씬 N 비트 추출}

## 직전 씬 마지막 문장 (연결용)
{직전 씬의 클리프행어/마지막 2~3문장}

## 참조 자료
{캐릭터, 세계관, 문체 가이드}
```

**마지막 씬은 다음 화 예고 포함:**
```
[씬 N 본문]

---

**다음 화 예고**: {한 줄 티저}
```

### Step 2-3: 병합

모든 씬 생성 완료 후 하나의 파일로 병합합니다:
```
씬1 (헤더+요약+---+본문)
---
씬2 본문
---
씬3 본문
---
씬4 본문 (+ --- + 다음 화 예고)
```

병합 후 **즉시 분량 사전 검증**:
```bash
python workflow/validate.py {project} {merged_file}
```
- F1 PASS → Stage 3+4로 진행
- F1 FAIL (특정 씬이 부족) → **해당 씬만 재생성** (전체 재생성 아님)

**결과 저장:**
- 씬별: `.staging/{ep_tag}_scene_{N}.md`
- 병합본: `.staging/{ep_tag}_draft_v1.md`

---

## Stage 3+4: 품질 리뷰 (병렬 실행)

초고에 대해 **문체 리뷰**와 **일관성 검증**을 병렬로 실행합니다.

### 방법 A: MCP 멀티모델 (ask_codex/ask_gemini 발견 시)

**병렬로 2개 호출:**

1. **문체 리뷰** → `ask_gemini` (1M 컨텍스트 활용)
```
ask_gemini(
  agent_role="style-reviewer",
  task="아래 에피소드 초고의 문체 품질을 S1~S10 체크리스트로 검증하세요. FAIL 항목은 구체적 위치 + 대안 문장을 반드시 제시하세요.",
  context_files=[초고, style-guide.md, characters.md]
)
```

2. **일관성 검증** → `ask_codex` (분석적 검증)
```
ask_codex(
  agent_role="consistency-checker",
  task="아래 에피소드 초고의 세계관/캐릭터 일관성을 C1~C7 체크리스트로 검증하세요. FAIL 항목은 참조 문서 인용 + 해결 방안을 반드시 제시하세요.",
  context_files=[초고, world.md, characters.md, episode-outline.md, 직전EP]
)
```

### 방법 B: Claude 에이전트 폴백 (MCP 미사용 시)

**병렬로 2개 Task 호출:**

1. **문체 리뷰:**
```
Task(
  subagent_type="style-reviewer",
  model="sonnet",
  prompt="아래 초고를 S1~S10 체크리스트로 문체 리뷰하세요.\n\n## 초고\n{draft}\n\n## 문체 가이드\n{style_guide}\n\n## 캐릭터 참조\n{characters}"
)
```

2. **일관성 검증:**
```
Task(
  subagent_type="consistency-checker",
  model="sonnet",
  prompt="아래 초고를 C1~C7 체크리스트로 일관성 검증하세요.\n\n## 초고\n{draft}\n\n## 세계관\n{world}\n\n## 캐릭터\n{characters}\n\n## 아웃라인\n{outline}\n\n## 직전 에피소드\n{previous_ending}"
)
```

### 리뷰 결과 병합

두 리뷰 결과를 수신한 후:
1. **FAIL 항목** 추출 → 수정 지시 목록 생성
2. **WARN 항목** 기록 (리비전 트리거하지 않음)
3. 리뷰 결과를 `.staging/{ep_tag}_style_review.md`, `.staging/{ep_tag}_consistency_review.md`에 저장

**판정:**
- FAIL 0개 → Stage 6로 직행
- FAIL 1개 이상 → Stage 5 진입

---

## Stage 5: 수정 (FAIL 있을 때만)

**Task 호출:**
```
Task(
  subagent_type="draft-writer",
  model="sonnet",
  prompt=아래 프롬프트
)
```

**프롬프트 구성:**
```
당신은 웹소설 "{context.project}"의 원고 수정 에이전트입니다.

## 임무
아래 초고에서 리뷰 결과 지적된 문제점만 수정하세요.

## 수정 지시 (FAIL 항목)
{fail_items_with_instructions}

## 수정 규칙
1. 지적된 부분만 수정. 정상 부분은 변경 금지
2. 분량 유지 (±500자 이내)
3. [IMG] 마커 위치/개수 유지
4. 문체 톤 일관성 유지

## 현재 초고
{draft}
```

**결과 저장:**
- `.staging/{ep_tag}_revision_v{n}.md`에 저장 (v1, v2 순번)

---

## Stage 6: 최종 검증

Python 스크립트로 정량적 검증을 실행합니다.

**실행:**
```bash
python workflow/validate.py {project} {project}/episodes/.staging/{ep_tag}_최신파일.md
```

**결과 파싱:** JSON 출력에서:
- `overall`: "PASS" 또는 "FAIL"
- `fail_items`: FAIL 항목 ID 배열 (F1~F6)
- `results`: 각 항목별 상세

**판정 로직:**
- **overall = "PASS"** → Stage 7로 진행
- **overall = "FAIL"** + 루프 횟수 < 2 → Stage 5로 돌아가서 FAIL 항목 수정
  - F1 (글자 수) FAIL → 수정 지시에 구체적 분량 조정 포함 (현재 X자, 목표 범위)
  - F6 (문미 연속) FAIL → 수정 지시에 위반 구간 샘플 포함
- **overall = "FAIL"** + 루프 횟수 >= 2 → `_WARNING` 접미사로 저장, 사람 검토 알림

**검증 결과 저장:**
- `.staging/{ep_tag}_validation.json`에 저장

---

## Stage 7: 이미지 프롬프트 생성 (논블로킹)

초고의 `[IMG:유형-설명]` 마커를 파싱하여 이미지 프롬프트를 자동 생성합니다.
**파이프라인을 멈추지 않습니다.** 프롬프트만 생성하여 저장합니다.

### 방법 A: ask_gemini (우선)
```
ask_gemini(
  agent_role="designer",
  task="아래 에피소드의 [IMG] 마커들을 이미지 생성에 최적화된 프롬프트로 변환하세요. 각 마커별로 영문 프롬프트 + 한국어 설명을 생성하세요.",
  context_files=[최종본, characters.md]
)
```

### 방법 B: Claude 직접 (폴백)
최종본에서 [IMG:...] 패턴을 추출하고, 각각에 대해 이미지 생성 프롬프트를 직접 작성합니다.

**결과 저장:**
- `.staging/{ep_tag}_img_prompts.json`에 저장
- 형식: `[{"marker": "[IMG:landscape-숲]", "prompt_en": "...", "description_kr": "..."}]`

---

## Stage 8: 최종 저장 및 리포트

### 파일 저장
최종 검증 통과한 에피소드를 정식 위치에 저장:
```
{project}/episodes/{ep_tag}_{제목_스네이크케이스}.md
```
- 제목은 context에서 추출한 `ep_title`을 사용
- 공백은 언더스코어로, 특수문자 제거

### 결과 리포트 출력

```markdown
## {ep_tag} 생성 완료

| 단계 | 상태 | 상세 |
|------|------|------|
| Stage 1 컨텍스트 | DONE | {total_chars}자, {sections} |
| Stage 2 초고 | DONE | {draft_chars}자 |
| Stage 3 문체 리뷰 | {APPROVED/REVISION} | FAIL: {ids} |
| Stage 4 일관성 | {APPROVED/REVISION} | FAIL: {ids} |
| Stage 5 수정 | {DONE/SKIP} | {revision_count}회 |
| Stage 6 검증 | {PASS/FAIL} | F1:{v} F2:{v} F3:{v} F4:{v} F5:{v} F6:{v} |
| Stage 7 이미지 | DONE | {img_count}개 프롬프트 |

**최종 파일**: `{project}/episodes/{filename}`
**최종 판정**: PASS / WARNING (사람 검토 필요)
```

---

## 에러 처리

| 상황 | 대응 |
|------|------|
| context_assembly.py 실패 | 직접 파일 읽기로 폴백 |
| MCP 도구 미발견 | Claude 에이전트로 폴백 (정상 동작) |
| 초고 분량 심각 부족 (순수 글자 수 <7500자, 목표 하한의 83% 미만) | 즉시 재생성 (수정 아닌 새 초고) |
| Stage 5↔6 루프 2회 후 FAIL | _WARNING 접미사, 사람 검토 전환 |
| ask_codex/ask_gemini 타임아웃 | Claude 에이전트로 즉시 폴백 |
| 이전 에피소드 미존재 (EP-01) | prev_ending 비워두고 정상 진행 |
