# 컨텍스트 엔지니어링 컬렉션

> 최종 업데이트: 2026-03 | 출처:
> - https://www.philschmid.de/context-engineering (Phil Schmid)
> - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (Anthropic Engineering)
> - Tobi Lutke (Shopify CEO) 원개념

## 핵심 요약

컨텍스트 엔지니어링은 "LLM이 태스크를 해결할 수 있도록 올바른 정보와 도구를 올바른 형식으로, 올바른 시점에 제공하는 시스템을 설계하는 학문"이다. 프롬프트 엔지니어링이 단일 텍스트를 다듬는 것이라면, 컨텍스트 엔지니어링은 전체 정보 생태계를 오케스트레이션한다. Anthropic의 핵심 원칙: "LLM이 원하는 결과를 최대화하는 최소한의 고신호 토큰 집합을 찾아라."

---

## 1. 컨텍스트 엔지니어링이란

### 정의 (Tobi Lutke, Shopify CEO)

> "컨텍스트 엔지니어링은 LLM이 태스크를 그럴듯하게 해결할 수 있도록 모든 맥락을 제공하는 기술이다."

### Phil Schmid의 확장 정의

> "컨텍스트 엔지니어링은 동적 시스템을 설계하고 구축하는 학문이다. 이 시스템은 LLM이 태스크를 수행하는 데 필요한 올바른 정보와 도구를 올바른 형식으로, 올바른 시점에 제공한다."

### 프롬프트 엔지니어링과의 차이

| | 프롬프트 엔지니어링 | 컨텍스트 엔지니어링 |
|---|---|---|
| 초점 | 단일 텍스트 명령 완성 | 전체 정보 생태계 오케스트레이션 |
| 범위 | 정적 템플릿 | 동적 시스템 |
| 주요 관심사 | 지시의 명확성 | 정보의 품질, 타이밍, 형식 |
| 실패 원인 | 잘못된 지시 | 잘못된 정보 제공 |

**핵심 통찰**: "대부분의 에이전트 실패는 모델 실패가 아니라 컨텍스트 실패다."

---

## 2. 컨텍스트의 7가지 구성 요소

Phil Schmid의 프레임워크:

| 레이어 | 설명 | 예시 |
|---|---|---|
| **Instructions / System Prompt** | 행동 지침, 예시, 규칙 | 역할 정의, 포맷 규칙, 금지사항 |
| **User Prompt** | 즉각적 태스크/질문 | "EP-05를 작성하세요" |
| **State / History** | 현재 대화 및 이전 교환 | 이전 turn의 피드백, 수정 요청 |
| **Long-Term Memory** | 이전 상호작용의 지속 지식 | 에이전트가 저장한 프로젝트 메모리 |
| **Retrieved Information (RAG)** | 문서/API에서 가져온 외부 현재 데이터 | 관련 로어 섹션, 이전 에피소드 요약 |
| **Available Tools** | 모델이 호출 가능한 함수 정의 | read_file, write_episode, validate |
| **Structured Output** | 응답 형식 명세 | JSON 스키마, 마크다운 구조 |

---

## 3. 핵심 원칙

### 원칙 1: 유한한 주의 예산 (Finite Attention Budget)

LLM은 본질적 제약 아래 작동한다. "컨텍스트 부패(context rot)" 연구에 따르면 토큰 수가 증가함에 따라 정보 정확 회상 능력이 저하된다. 트랜스포머 아키텍처의 n² 쌍방향 토큰 관계 때문에 컨텍스트가 커질수록 관계 포착 능력이 감소한다.

**실천**: 필요한 정보만, 최소한으로.

### 원칙 2: 올바른 고도 (Right Altitude)

시스템 프롬프트는 두 극단 사이의 균형을 맞춰야 한다:
- **너무 딱딱한 규칙**: 취약성 생성 (경직된 하드코딩 로직)
- **너무 모호한 가이던스**: 구체적 신호 제공 실패

최적: "효과적으로 행동을 안내할 만큼 구체적이면서, 모델이 강력한 휴리스틱을 적용할 만큼 유연한" 수준.

### 원칙 3: 최소 도구 세트 (Minimal Tool Sets)

도구 정의는 자기완결적이고, 명확하게 정의되며, 목적이 모호하지 않아야 한다. "사람 엔지니어가 어떤 도구를 써야 할지 결정적으로 말할 수 없다면, AI 에이전트도 마찬가지다."

### 원칙 4: 형식 중요성 (Format Matters)

간결한 요약이 원시 데이터 덤프보다 낫고, 명확한 도구 스키마가 모호한 지시보다 낫다.

---

## 4. "마법 같은 에이전트" vs "싸구려 데모" 비교

Phil Schmid의 미팅 스케줄링 예시:

**빈약한 컨텍스트 (싸구려 데모)**:
```
에이전트 입력: "Jim과 미팅을 잡아줘"
출력: "선호하는 시간이 있으신가요? 30분과 1시간 중 어떤 게 좋으세요?"
```

**풍부한 컨텍스트 (마법 같은 에이전트)**:
```
에이전트 입력: "Jim과 미팅을 잡아줘"
+ 캘린더 데이터 (내일 종일 회의 가득)
+ 이메일 기록 (Jim과의 어조, 관계)
+ 연락처 정보 (Jim = 우선순위 파트너)
+ 도구 (send_invite, send_email)
출력: "Jim! 내일은 종일 미팅이 가득 찼어요. 목요일 오전 가능한데 어때요? 초대 보냈으니 확인해주세요."
```

**핵심**: 마법은 준비에 있다, 지능이 아니라.

---

## 5. 컨텍스트 관리 기법

### 기법 1: Just-In-Time (JIT) 검색

모든 데이터를 사전 로드하는 대신, 런타임에 동적으로 컨텍스트를 로드한다.

```python
# 나쁜 예: 모든 로어를 미리 로드
context = load_all_lore_files()  # 수만 토큰

# 좋은 예: 관련 섹션만 동적 로드
def get_relevant_lore(episode_id: str, required_topics: list[str]) -> str:
    relevant_chars = extract_relevant_characters(episode_id)
    relevant_world = extract_relevant_world_sections(required_topics)
    return combine(relevant_chars, relevant_world)
```

경량 식별자(파일 경로, URL, 저장 쿼리)를 유지하고 필요 시에만 로드하는 방식. 인간의 인지 방식 모방 - 외부 조직 시스템 활용, 전체 코퍼스 암기 안 함.

### 기법 2: 컨텍스트 압축 (Compaction)

대화가 컨텍스트 한도에 가까워질 때, 내용을 요약하고 압축된 요약으로 재초기화.

**구현 전략**:
1. 최대 회상 우선: 모든 관련 세부사항 포착
2. 정밀도 향상: 불필요한 내용(반복적 도구 출력 등) 제거

```python
def compact_context(conversation_history: list) -> str:
    """대화 기록을 핵심 정보로 압축"""
    summary_prompt = """
    다음 대화에서 다음을 추출하세요:
    1. 완료된 태스크 목록
    2. 결정된 사항 (취소 불가 결정 표시)
    3. 현재 진행 중인 태스크와 상태
    4. 다음 단계
    5. 중요 발견사항

    세부사항은 유지하되 중복 제거.
    """
    return summarize(conversation_history, summary_prompt)
```

### 기법 3: 구조화된 노트 테이킹

에이전트가 컨텍스트 창 외부에 지속적 메모를 작성하고 필요 시 검색:

```
# progress.txt (에이전트 노트)
세션 5 상태:
- 완료: EP-01 ~ EP-10 아웃라인
- 진행 중: EP-11 초고 (3,200/5,000자)
- 다음: EP-11 문체 리뷰
- 미결: EP-15 클리프행어 - EP-16 연결 확인 필요
- 주의: 소피아 사망 EP-12에서 공개 예정 - EP-01~11에서 누설 금지
```

### 기법 4: 서브에이전트 아키텍처

전문화된 에이전트가 깨끗한 컨텍스트 창으로 집중 태스크 처리, 조율 에이전트에 압축된 요약(1,000~2,000 토큰) 반환.

```
오케스트레이터 에이전트 (경량 컨텍스트)
├── 문체 리뷰 에이전트 → 요약 반환
├── 일관성 검증 에이전트 → 요약 반환
└── 이미지 프롬프트 에이전트 → 요약 반환
```

이 분리는 상세 탐색과 고수준 합성/분석을 분리한다.

---

## 6. 컨텍스트 배치 순서 (Ordering)

최적 컨텍스트 배치 순서 (Claude/GPT 모두 적용):

```
1. [시스템 프롬프트] 역할, 핵심 규칙
2. [장기 메모리] 프로젝트 영구 정보
3. [검색된 정보] 현재 태스크 관련 RAG 결과
4. [대화 기록] 이전 교환 (압축 버전)
5. [현재 태스크] 실제 요청
```

**긴 문서 (20K+ 토큰)**: 문서를 상단에, 쿼리를 하단에 배치. 연구에 따르면 30%까지 성능 향상.

---

## 7. 시스템 프롬프트 설계 가이드라인

Anthropic Engineering 권장 사항:

1. **최소 프롬프트로 시작**: 최고 모델로 시작, 실패 패턴 발견 후 점진적 지시 추가
2. **섹션 구분**: 배경, 지시사항, 도구 가이던스, 출력 설명을 명확히 구분
3. **XML 태그 또는 마크다운 헤더**: 구조 명확화
4. **컨텍스트를 소중한 자원으로**: 각 추론 단계에서 신중하게 큐레이션

```xml
<system_prompt>
  <background>
    당신은 한국 웹소설 자동 생성 시스템의 집필 에이전트입니다.
  </background>

  <instructions>
    주어진 아웃라인과 로어 설정에 따라 에피소드를 작성합니다.
    [핵심 규칙들...]
  </instructions>

  <tool_guidance>
    파일 읽기 도구: 로어 파일 참조 시 사용
    검증 도구: 초고 완성 후 자동 실행
  </tool_guidance>

  <output_format>
    순수 텍스트, IMG 마커 3개, 4000~5000자
  </output_format>
</system_prompt>
```

---

## 8. 메모리 전략 비교

| 메모리 유형 | 저장 위치 | 영속성 | 적합 용도 |
|---|---|---|---|
| In-context | 현재 프롬프트 | 세션 내 | 즉각적 태스크 정보 |
| External file | 파일 시스템 | 영구 | 프로젝트 상태, 아웃라인 |
| Vector store | 벡터 DB | 영구 | 대규모 로어 RAG |
| Structured DB | SQL/NoSQL | 영구 | 에피소드 메타데이터 |
| Agent memory tool | API 저장소 | 세션 간 | 에이전트 자체 학습 |

---

## 9. 컨텍스트 품질 체크리스트

각 파이프라인 단계에서:

- [ ] 현재 태스크에 직접 필요한 정보만 포함했는가?
- [ ] 중복 정보가 없는가?
- [ ] 중요 정보가 컨텍스트 중간에 묻히지 않는가? (처음 또는 끝 배치)
- [ ] 도구 정의가 명확하고 목적이 모호하지 않은가?
- [ ] 출력 형식이 명확하게 명세되어 있는가?
- [ ] 이전 세션의 상태가 적절히 로드되어 있는가?

---

## 우리 파이프라인 적용 포인트

### 컨텍스트 조립 전략 (Stage 1: context_assembly.py)

```python
def assemble_episode_context(project: str, episode_id: str) -> dict:
    """
    JIT 방식으로 에피소드별 최소 필수 컨텍스트 조립
    """
    # 1. 현재 에피소드 아웃라인만 추출
    outline = extract_episode_outline(episode_id)

    # 2. 등장 캐릭터만 필터링
    characters = extract_relevant_characters(outline.character_names)

    # 3. 관련 세계관 섹션만 추출
    world = extract_world_sections(outline.location_keywords)

    # 4. 이전 에피소드 요약 (전문이 아닌 요약)
    prev_summary = get_episode_summary(episode_id - 1)

    return {
        "outline": outline,      # ~1,000 토큰
        "characters": characters, # ~2,000 토큰
        "world": world,          # ~1,500 토큰
        "prev_summary": prev_summary, # ~500 토큰
        # 총계: ~5,000 토큰 (전체 로어 ~50,000 토큰 대신)
    }
```

### 세션 간 상태 유지

```
# progress.txt 형식 (구조화되지 않은 에이전트 노트)
[EP-05 생성 세션 - 2026-03-12]
상태: 초고 완성, 문체 리뷰 중
완료된 수정: 도입부 클리프행어 연결 강화
미결 이슈: 3막 속도감 부족 (리뷰어 피드백)
다음 단계: 3막 씬 비트 확장 후 재검증
```

### 서브에이전트별 컨텍스트 격리

| 서브에이전트 | 받는 컨텍스트 | 반환 요약 |
|---|---|---|
| 문체 리뷰어 | 초고 + style-guide.md | 수정 사항 목록 (500토큰) |
| 일관성 검증 | 초고 + characters.md + prev_summary | 불일치 목록 (300토큰) |
| 이미지 프롬프트 | 초고 + world.md + art style | 3개 IMG 프롬프트 (200토큰) |

---

## 추가 참고 자료

- [Phil Schmid - Context Engineering](https://www.philschmid.de/context-engineering)
- [Anthropic - Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic - Context Windows & Awareness](https://platform.claude.com/docs/en/docs/build-with-claude/context-windows)
- [Claude Memory Tool](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/memory-tool)
