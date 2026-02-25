# 프리프로덕션: 아웃라인 자동 생성 오케스트레이터

장르 리서치 → 스토리 구조 설계 → 아웃라인 생성 → 플롯 설계 → 검증의 5단계 프리프로덕션 파이프라인을 실행합니다.
모든 단계가 완전 자동(AUTO)으로 실행됩니다.

---

## 인자 파싱

`$ARGUMENTS`에서 프로젝트와 옵션을 파싱합니다.

| 입력 | 해석 |
|------|------|
| `ssulhwa` | Stage 1부터 전체 실행 |
| `ssulhwa --from-stage 3` | Stage 3부터 실행 (이전 산출물 존재 전제) |
| (빈 값) | 프로젝트 자동감지, Stage 1부터 |

**프로젝트 자동 감지**: `$ARGUMENTS`가 비거나 `--from-stage`만 있으면, `*/project.yaml`을 Glob으로 검색하여 프로젝트가 1개뿐이면 자동 사용.

**--from-stage 파싱**: `--from-stage N` 형태에서 N을 추출. 미지정 시 1.

---

## 실행 전 준비

### 프로젝트 설정 로드
`{project}/project.yaml`을 Read로 읽어 설정을 파악합니다:
- `name`: 작품명
- `language`: 언어
- `episodes.total`: 총 에피소드 수
- `format`: 분량/형식 설정 (씬 수, 글자 수 — Stage 4에서 참조)
- `lore`: 로어 파일 경로
- `preproduction`: 프리프로덕션 설정 (genre, structure, outline, plot, review)

### 필수 파일 확인
다음 파일이 존재하는지 확인합니다:
- `{project}/lore/characters.md` — **필수** (없으면 ERROR 종료)
- `{project}/lore/world.md` — **필수** (없으면 ERROR 종료)
- `{project}/lore/scenario.md` — 선택 (없으면 Stage 2에서 신규 생성)
- `{project}/lore/genre-reference.md` — 선택 (없으면 Stage 1에서 신규 생성)
- `{project}/lore/episode-outline.md` — 선택 (없으면 Stage 3에서 신규 생성)
- `{project}/lore/plot-beats.md` — 선택 (없으면 Stage 4에서 신규 생성)

### 스테이징 디렉토리
중간 산출물 경로: `{project}/{preproduction.staging_dir}` (기본: `episodes/.staging/preproduction`)

---

## Stage 1: 장르 리서치

**조건**: `--from-stage`가 1 이하일 때 실행.

**입력 수집**:
1. `{project}/project.yaml` 읽기
2. `{project}/lore/characters.md` 읽기
3. `{project}/lore/world.md` 읽기
4. `{project}/lore/genre-reference.md` 읽기 (존재하면)

**Task 호출**:
```
Task(
  subagent_type="genre-researcher",
  model="sonnet",
  prompt=아래 프롬프트
)
```

**프롬프트 구성**:
```
아래 프로젝트의 장르를 분석하고 genre-reference.md를 작성/보강하세요.

## 프로젝트 설정
{project.yaml 내용}

## 캐릭터 참조
{characters.md 내용}

## 세계관 참조
{world.md 내용}

## 기존 genre-reference.md (있으면)
{genre-reference.md 내용 또는 "없음 — 신규 생성"}

## 출력
{project}/lore/genre-reference.md 에 Write로 저장하세요.
```

**결과 확인**: `{project}/lore/genre-reference.md` 파일이 생성/갱신되었는지 확인.

**에러 처리**: WebSearch 실패 시 기존 데이터만으로 진행 (WARN 기록).

---

## Stage 2: 스토리 구조 설계

**조건**: `--from-stage`가 2 이하일 때 실행.

**입력 수집**:
1. `{project}/project.yaml` 읽기
2. `{project}/lore/genre-reference.md` 읽기
3. `{project}/lore/scenario.md` 읽기 (존재하면)
4. `{project}/lore/characters.md` 읽기
5. `{project}/lore/world.md` 읽기

**Task 호출**:
```
Task(
  subagent_type="story-architect",
  model="opus",
  prompt=아래 프롬프트
)
```

**프롬프트 구성**:
```
아래 프로젝트의 전체 서사 구조를 설계하고 scenario.md를 작성/보강하세요.

## 프로젝트 설정
{project.yaml 내용}

## 장르 레퍼런스
{genre-reference.md 내용}

## 기존 시나리오 (있으면)
{scenario.md 내용 또는 "없음 — 신규 설계"}

## 캐릭터 참조
{characters.md 내용}

## 세계관 참조
{world.md 내용}

## 출력
{project}/lore/scenario.md 에 Write로 저장하세요.
```

**결과 확인**: `{project}/lore/scenario.md` 파일이 생성/갱신되었는지 확인.

---

## Stage 3: 아웃라인 생성

**조건**: `--from-stage`가 3 이하일 때 실행.

**입력 수집**:
1. `{project}/project.yaml` 읽기
2. `{project}/lore/scenario.md` 읽기
3. `{project}/lore/characters.md` 읽기
4. `{project}/lore/world.md` 읽기
5. `{project}/lore/genre-reference.md` 읽기
6. `{project}/lore/episode-outline.md` 읽기 (존재하고 수정 모드인 경우)

**Task 호출**:
```
Task(
  subagent_type="outline-generator",
  model="opus",
  prompt=아래 프롬프트
)
```

**프롬프트 구성 (신규 생성)**:
```
아래 프로젝트의 전체 에피소드 아웃라인을 생성하세요.

## 프로젝트 설정
{project.yaml 내용}

## 시나리오 구조
{scenario.md 내용}

## 캐릭터 참조
{characters.md 내용}

## 세계관 참조
{world.md 내용}

## 장르 레퍼런스
{genre-reference.md 내용}

## 출력
{project}/lore/episode-outline.md 에 Write로 저장하세요.
```

**프롬프트 구성 (수정 모드 — Stage 5 FAIL 후 재실행 시)**:
```
아래 리뷰 결과의 FAIL 항목을 수정하여 아웃라인을 개선하세요.

## 수정 지시
{FAIL 항목별 수정 지시 목록}

## 현재 아웃라인
{episode-outline.md 내용}

## 참조 자료
{scenario.md, characters.md, world.md, genre-reference.md}

## 출력
{project}/lore/episode-outline.md 에 Write로 저장하세요.
```

**결과 확인**: `{project}/lore/episode-outline.md` 파일이 생성/갱신되었는지 확인.

---

## Stage 4: 플롯 설계 (씬 비트 + 에피소드 경계)

**조건**: `--from-stage`가 4 이하일 때 실행.

**입력 수집**:
1. `{project}/project.yaml` 읽기 (format.scenes, format.char_count, preproduction.plot)
2. `{project}/lore/episode-outline.md` 읽기
3. `{project}/lore/scenario.md` 읽기
4. `{project}/lore/genre-reference.md` 읽기
5. `{project}/lore/characters.md` 읽기
6. `{project}/lore/plot-beats.md` 읽기 (존재하고 수정 모드인 경우)

**Task 호출**:
```
Task(
  subagent_type="plot-designer",
  model="opus",
  prompt=아래 프롬프트
)
```

**프롬프트 구성 (신규 생성)**:
```
아래 프로젝트의 전체 에피소드에 대해 씬 비트시트와 에피소드 경계를 설계하세요.

## 프로젝트 설정
{project.yaml 내용}

플롯 모델: {preproduction.plot.structure_model} (기본: 기승전결)
씬 수 범위: {preproduction.plot.scene_count_range 또는 format.scenes}
글자 수 범위: {format.char_count}
클리프행어 유형: {preproduction.plot.cliffhanger_types}

## 에피소드 아웃라인
{episode-outline.md 내용}

## 시나리오 구조
{scenario.md 내용}

## 장르 레퍼런스
{genre-reference.md 내용}

## 캐릭터 참조
{characters.md 내용}

## 출력
{project}/lore/plot-beats.md 에 Write로 저장하세요.
```

**프롬프트 구성 (수정 모드 — Stage 5 FAIL 후 재실행 시)**:
```
아래 리뷰 결과의 FAIL 항목을 수정하여 플롯 비트시트를 개선하세요.

## 수정 지시
{FAIL 항목별 수정 지시 목록 (P1~P8 관련)}

## 현재 플롯 비트시트
{plot-beats.md 내용}

## 에피소드 아웃라인
{episode-outline.md 내용}

## 출력
{project}/lore/plot-beats.md 에 Write로 저장하세요.
```

**결과 확인**: `{project}/lore/plot-beats.md` 파일이 생성/갱신되었는지 확인.

---

## Stage 5: 검증 (정량 + 정성 병렬)

**조건**: 항상 실행.

### Stage 5a: 정량 검증 (Python)

**실행**:
```bash
python workflow/outline_validate.py {project}
```

**결과 파싱**: JSON 출력에서:
- `overall`: "PASS" 또는 "FAIL"
- `fail_items`: FAIL 항목 ID 배열 (V1~V5)
- `warn_items`: WARN 항목 ID 배열
- `results`: 각 항목별 상세

### Stage 5b: 정성 검증 (에이전트)

**5a와 병렬로 실행**:

```
Task(
  subagent_type="outline-reviewer",
  model="opus",
  prompt=아래 프롬프트
)
```

**프롬프트 구성**:
```
아래 아웃라인과 플롯 비트시트의 서사 품질을 R1~R8 체크리스트로 검증하세요.

## 아웃라인
{episode-outline.md 내용}

## 플롯 비트시트
{plot-beats.md 내용}

## 시나리오 구조
{scenario.md 내용}

## 장르 레퍼런스
{genre-reference.md 내용}

## 캐릭터 참조
{characters.md 내용}

## 프로젝트 설정
{project.yaml 내용 중 episodes, format, preproduction 섹션}

떡밥 회수율 기준: {preproduction.review.min_foreshadow_recovery_rate} (기본 0.7)

추가 검증: 플롯 비트시트의 클리프행어 다양성, 오프닝-클리프행어 연결성, 씬 비트 완비도도 함께 확인하세요.
```

### 검증 결과 병합 및 판정

두 검증 결과를 수신한 후:
1. **5a + 5b의 FAIL 항목**을 모두 수집
2. 검증 결과를 스테이징에 저장:
   - `{staging_dir}/outline_validation.json` (5a 결과)
   - `{staging_dir}/outline_review.md` (5b 결과)

**판정 로직**:
- 5a **PASS** + 5b **APPROVED** → **완료**
- **아웃라인 FAIL** (V1~V5 또는 R1~R3, R7~R8) + 루프 < 최대 → Stage 3 **수정 모드**로 재실행 → Stage 4 재실행
- **플롯 FAIL** (비트시트/경계 관련) + 루프 < 최대 → Stage 4 **수정 모드**로 재실행
- 루프 횟수 >= `preproduction.review.max_revision_loops` (기본 2) → `_WARNING` 접미사 저장, 사람 검토 알림

**수정 지시 구성** (FAIL 시):
5a의 FAIL 항목(V1~V5)과 5b의 FAIL 항목(R1~R8 + 플롯 관련)을 분류하여 해당 Stage의 수정 모드 프롬프트에 전달.

---

## 완료 리포트

모든 단계 완료 후 리포트를 출력합니다:

```markdown
## 프리프로덕션 완료: {project_name}

| 단계 | 상태 | 산출물 |
|------|------|--------|
| Stage 1 장르 리서치 | DONE/SKIP | genre-reference.md |
| Stage 2 스토리 구조 | DONE/SKIP | scenario.md |
| Stage 3 아웃라인 생성 | DONE | episode-outline.md |
| Stage 4 플롯 설계 | DONE | plot-beats.md |
| Stage 5a 정량 검증 | PASS/FAIL | V1:{v} V2:{v} V3:{v} V4:{v} V5:{v} |
| Stage 5b 정성 검증 | APPROVED/REVISION | R1:{v} ... R8:{v} |
| 수정 루프 | {count}회 |

**최종 판정**: PASS / WARNING (사람 검토 필요)
**산출물**:
- 아웃라인: `{project}/lore/episode-outline.md`
- 플롯 비트시트: `{project}/lore/plot-beats.md`

### 다음 단계
`/project:generate-episode {project} EP-01` 또는
`/project:generate-batch {project}` 으로 에피소드 생성을 시작하세요.
```

---

## 에러 처리

| 상황 | 대응 |
|------|------|
| characters.md 없음 | **ERROR** — 최소 캐릭터 설정 필요. 종료 |
| world.md 없음 | **ERROR** — 최소 세계관 설정 필요. 종료 |
| genre-reference.md 없음 | 신규 생성 (정상) |
| scenario.md 없음 | 신규 설계 (정상) |
| episode-outline.md 없음 | 신규 생성 (정상) |
| plot-beats.md 없음 | 신규 생성 (정상) |
| WebSearch 실패 (Stage 1) | 기존 데이터만으로 진행 (WARN) |
| Stage 5 루프 2회 후 FAIL | `_WARNING` 접미사, 사람 검토 |
| Python 스크립트 실패 | 에러 기록, 정성 검증(5b)만으로 판정 |
