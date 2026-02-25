# 에피소드 배치 생성

에피소드를 구간/전체 단위로 순차 자동 생성합니다.
각 에피소드는 8단계 파이프라인(generate-episode)을 따르며, 이전 에피소드의 연속성을 자동 참조합니다.

---

## 인자 파싱

`$ARGUMENTS`를 파싱하여 프로젝트와 시작/끝 번호를 결정합니다:

| 입력 | 해석 | 범위 |
|------|------|------|
| `ssulhwa EP-05 EP-17` | 구간 생성 | EP-05 ~ EP-17 |
| `ssulhwa EP-05` | 지정~끝 | EP-05 ~ EP-{total} |
| `ssulhwa` | 전체 생성 | EP-01 ~ EP-{total} |
| `EP-05 EP-17` | 프로젝트 자동감지 + 구간 | EP-05 ~ EP-17 |
| (빈 값) | 자동감지 + 전체 | EP-01 ~ EP-{total} |

**프로젝트 자동 감지**: `*/project.yaml`이 1개뿐이면 자동 사용.
**총 에피소드 수**: `{project}/project.yaml`의 `episodes.total`에서 읽음.

---

## 실행 전 준비

### 1. 프로젝트 설정 로드
`{project}/project.yaml`을 Read로 읽어 설정을 파악합니다.
- `episodes.total`: 총 에피소드 수
- `format`: 분량/형식 설정
- `lore`: 로어 파일 경로

### 2. MCP 도구 탐색
`ToolSearch("mcp")`를 **1회만** 실행하여 ask_codex, ask_gemini 발견.
배치 전체에서 재탐색 불필요.

### 3. 기존 에피소드 확인
시작 번호 직전 에피소드가 `{project}/episodes/`에 존재하는지 확인.
존재하면 연속성 컨텍스트로 활용.

### 4. 진행 상태 파일 초기화
```
{project}/episodes/.staging/batch_progress.json
```
```json
{
  "project": "{project}",
  "range": "EP-{start} ~ EP-{end}",
  "started_at": "2026-02-25T...",
  "episodes": {}
}
```

---

## 배치 루프

**반드시 순차 실행** — 이전 에피소드 엔딩이 다음 에피소드 컨텍스트에 필요합니다.

```
for ep_num in range(start, end + 1):
    ep_tag = f"EP-{ep_num:02d}"
```

### 각 에피소드마다 수행할 단계

아래 8단계 파이프라인을 **직접 실행**합니다 (generate-episode.md와 동일한 로직):

#### Stage 1: 컨텍스트 조립
```bash
python workflow/context_assembly.py {project} {ep_tag}
```

#### Stage 2: 초고 생성
```
Task(subagent_type="draft-writer", model="sonnet", prompt=컨텍스트+아웃라인+형식요구사항)
```
→ `.staging/{ep_tag}_draft_v1.md` 저장

#### Stage 3+4: 품질 리뷰 (병렬)
- ask_gemini → 문체 리뷰 (폴백: Task style-reviewer)
- ask_codex → 일관성 검증 (폴백: Task consistency-checker)

#### Stage 5: 수정 (FAIL 시)
```
Task(subagent_type="draft-writer", model="sonnet", prompt=수정지시+초고)
```

#### Stage 6: 검증
```bash
python workflow/validate.py {project} .staging/{ep_tag}_최신.md
```
→ FAIL이면 Stage 5로 (최대 2회)

#### Stage 7: 이미지 프롬프트
ask_gemini 또는 직접 → `.staging/{ep_tag}_img_prompts.json`

#### Stage 8: 저장
→ `{project}/episodes/{ep_tag}_{제목}.md`

### 에피소드 완료 후

1. **진행 상태 업데이트:**
```json
{
  "EP-05": {
    "status": "PASS",
    "file": "EP-05_제목.md",
    "char_count": 10234,
    "revision_count": 1,
    "fail_items": [],
    "duration": "~3min"
  }
}
```

2. **진행 상황 출력:**
```
[EP-05] PASS (10,234자, 수정 1회)
[EP-06] 생성 중...
```

3. **다음 에피소드 연속성 확보:**
방금 저장한 에피소드가 다음 EP의 `previous_ending` 소스가 됨.
context_assembly.py가 자동으로 감지하므로 추가 작업 불필요.

---

## 에러 처리 (배치 전용)

| 상황 | 대응 |
|------|------|
| 개별 EP FAIL (2회 루프 후) | `_WARNING`으로 저장, **다음 EP 계속 진행** |
| 개별 EP 에러 (스크립트 실패 등) | 에러 기록, **다음 EP 계속 진행** |
| 연속 3개 EP FAIL | 경고 메시지 출력, 사용자에게 계속 여부 확인 |
| MCP 도구 중간에 끊김 | Claude 에이전트로 폴백, 배치 계속 |
| 컨텍스트 윈도우 압박 | 이전 EP의 .staging 중간 산출물은 참조하지 않음 (최종본만 참조) |

---

## 배치 완료 리포트

모든 에피소드 생성 완료 후 종합 리포트를 출력합니다:

```markdown
## 배치 생성 완료: EP-{start} ~ EP-{end}

### 결과 요약
| EP | 상태 | 글자 수 | 수정 횟수 | FAIL 항목 |
|----|------|---------|----------|----------|
| EP-05 | PASS | 10,234 | 1 | — |
| EP-06 | PASS | 9,872 | 0 | — |
| EP-07 | WARNING | 8,743 | 2 | F1 |
| ... | ... | ... | ... | ... |

### 통계
- 전체: {total}편
- PASS: {pass_count}편
- WARNING: {warn_count}편 (사람 검토 필요)
- ERROR: {error_count}편

### WARNING 에피소드 (사람 검토 필요)
- EP-07: F1 글자 수 부족 (8,743자) → `EP-07_WARNING_제목.md`

### 이미지 프롬프트
- 생성됨: {img_count}편 x 3~5개 = ~{total_imgs}개
- 위치: `{project}/episodes/.staging/EP-XX_img_prompts.json`

### 파일 위치
- 최종 에피소드: `{project}/episodes/EP-XX_제목.md`
- 중간 산출물: `{project}/episodes/.staging/`
- 배치 진행 로그: `{project}/episodes/.staging/batch_progress.json`
```

---

## 주의사항

1. **순차 실행 필수**: 에피소드 간 연속성 때문에 병렬 생성 불가
2. **컨텍스트 효율**: 각 EP 생성 시 이전 EP의 중간 산출물(.staging)은 참조하지 않음. 오직 최종 에피소드 파일만 참조
3. **MCP 탐색 1회**: 배치 시작 시 1회만 ToolSearch 실행
4. **실패해도 계속**: 개별 EP 실패가 배치 전체를 중단시키지 않음
5. **진행 상태 저장**: batch_progress.json으로 중단 후 재개 가능 (수동)
