# 웹소설 자동 생성 프레임워크

## 개요
웹소설 에피소드 자동 생성 파이프라인.
Claude Code + OMC 멀티모델 오케스트레이션으로 **완전 자동화**.
`{project}/project.yaml` + `{project}/lore/` 설정만 교체하면 어떤 작품이든 동일 파이프라인으로 생성 가능.
휴먼 트리거 없이 끝까지 실행 (이미지 프롬프트는 생성만, 실제 이미지는 별도 배치).

## 에이전트 아키텍처 (architecture v4.1)
```
OMC 오케스트레이터 (Claude Code)
├─ [프리프로덕션]
│  ├─ AUTO  Claude sonnet      → 장르 리서치 (genre-researcher)
│  ├─ AUTO  Claude opus        → 스토리 구조 (story-architect)
│  ├─ AUTO  Claude opus        → 아웃라인 생성 (outline-generator)
│  ├─ AUTO  Claude opus        → 플롯 설계: 씬 비트 + 에피소드 경계 (plot-designer)
│  ├─ AUTO  Claude opus        → 아웃라인 검증 (outline-reviewer)
│  └─ AUTO  Python scripts     → 아웃라인 정량 검증
├─ [프로덕션]
│  ├─ AUTO  Claude sonnet      → 집필 + 수정 (draft-writer)
│  ├─ AUTO  ask_gemini (MCP)   → 문체 리뷰 + 이미지 프롬프트
│  ├─ AUTO  ask_codex (MCP)    → 일관성 검증
│  ├─ AUTO  Python scripts     → 컨텍스트 조립 + 최종 검증
│  └─ (폴백) Claude agents     → MCP 미사용 시 전체 대체 가능
```

## 프로젝트 구조
```
workflow/                        # 공용 파이프라인 스크립트
├── context_assembly.py          # 프로덕션 Stage 1 컨텍스트 조립
├── validate.py                  # 프로덕션 Stage 6 자동 검증
└── outline_validate.py          # 프리프로덕션 아웃라인 검증
{project}/                       # 작품별 디렉토리 (예: ssulhwa/)
├── project.yaml                 # 프로젝트 설정 허브
├── lore/                        # 설정 자료
│   ├── characters.md            # 캐릭터 설정
│   ├── world.md                 # 세계관 설정
│   ├── genre-reference.md       # 장르 레퍼런스 (프리프로덕션 생성)
│   ├── scenario.md              # 시나리오 구조 (프리프로덕션 생성/보강)
│   ├── style-guide.md           # 문체/형식 가이드
│   ├── episode-outline.md       # 에피소드 아웃라인 (프리프로덕션 생성)
│   ├── plot-beats.md            # 씬 비트시트 + 에피소드 경계 (프리프로덕션 생성)
│   └── relationships.md         # 관계 설정 (선택)
├── workflow/                    # 작품별 파이프라인 문서
│   └── pipeline.md              # 파이프라인 명세
└── episodes/                    # 생성된 에피소드
    ├── .staging/                # 중간 산출물
    │   └── preproduction/       # 프리프로덕션 중간 산출물
    └── pilot/                   # 파일럿 에피소드
```

## project.yaml 설정
각 작품 디렉토리의 `project.yaml`이 설정 허브 역할:
- `name`: 작품명
- `language`: 언어 코드 (ko, en, ja 등)
- `episodes`: 총 에피소드 수, ID 형식
- `format`: 글자 수, 씬 수, IMG 마커 수, 헤더 패턴 등
- `lore`: 로어 파일 경로 매핑
- `context`: 캐릭터 이름 매핑, 세계관 키워드→섹션 매핑
- `validation`: 검증 기준 (문미 연속 허용 수 등)
- `preproduction`: 프리프로덕션 설정 (장르/구조/아웃라인/플롯/검증 기준)

## 슬래시 커맨드
- `/project:generate-outline <project>` — 프리프로덕션 실행 (장르 리서치 → 아웃라인/플롯 생성/검증)
- `/project:generate-episode <project> <episode>` — 단편 생성 (예: `ssulhwa EP-05`)
- `/project:generate-batch <project> [start] [end]` — 구간/전체 생성 (예: `ssulhwa EP-05 EP-17`)

프로젝트 인자가 1개뿐이면 자동 감지 (project.yaml이 1개인 경우).

## 프리프로덕션 파이프라인 (5단계, 전체 AUTO)
```
Stage 1 (Genre)    → genre-researcher (sonnet) → genre-reference.md
Stage 2 (Structure)→ story-architect (opus)    → scenario.md
Stage 3 (Outline)  → outline-generator (opus)  → episode-outline.md
Stage 4 (Plot)     → plot-designer (opus)      → plot-beats.md
Stage 5 (Review)   → outline_validate.py + outline-reviewer (opus)
  └→ FAIL → Stage 3 or 4 수정 재실행 (최대 2회)
```

### 프리프로덕션 멀티모델 라우팅
| Stage | 모델 | 이유 |
|-------|------|------|
| 1 (장르) | Claude sonnet | 리서치 + WebSearch |
| 2 (구조) | Claude opus | 전체 서사 추론 |
| 3 (아웃라인) | Claude opus | 전 EP 연결 추론 |
| 4 (플롯) | Claude opus | 씬 비트/경계 설계, 전 EP 클리프행어 연결 |
| 5 (검증) | Claude opus + Python | 정성+정량 검증 |

## 프로덕션 파이프라인 (8단계, 전체 AUTO)
```
Stage 1 (Context)  → Python workflow/context_assembly.py
Stage 2 (Draft)    → Claude sonnet (draft-writer)
Stage 3 (Style)    → ask_gemini / Claude (style-reviewer)  ─┐ 병렬
Stage 4 (Consist)  → ask_codex / Claude (consistency-checker) ─┘
Stage 5 (Revise)   → Claude sonnet (draft-writer, 수정 모드) — FAIL 시만
Stage 6 (Validate) → Python workflow/validate.py
  └→ FAIL → Stage 5 재실행 (최대 2회)
Stage 7 (ImgPrompt)→ ask_gemini / Claude → 이미지 프롬프트 저장 (논블로킹)
Stage 8 (Save)     → 최종 에피소드 저장 + 리포트
```

### 프로덕션 멀티모델 라우팅
| Stage | 우선 | 폴백 | 이유 |
|-------|------|------|------|
| 2 (초고) | Claude sonnet | — | 한국어 창작 최적 |
| 3 (문체) | Gemini (1M ctx) | Claude sonnet | 대용량 텍스트 리뷰 |
| 4 (일관성) | Codex | Claude sonnet | 분석적 검증 |
| 5 (수정) | Claude sonnet | — | 한국어 창작 최적 |

## 새 프로젝트 시작 가이드
1. 프로젝트 디렉토리 생성: `mkdir {project_name}`
2. `{project_name}/project.yaml` 작성 (`ssulhwa/project.yaml` 참조)
3. `{project_name}/lore/` 아래 최소 필수 파일 배치:
   - `characters.md`, `world.md`
4. `/project:generate-outline {project_name}` 으로 아웃라인 자동 생성 (프리프로덕션)
5. `/project:generate-episode {project_name} EP-01` 으로 첫 에피소드 생성
