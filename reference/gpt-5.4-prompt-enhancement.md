# GPT-5.4 프롬프트 전략 가이드

> 최종 업데이트: 2026-03 | 출처:
> - https://developers.openai.com/api/docs/guides/prompt-guidance (GPT-5.4 공식 프롬프트 가이드)
> - https://developers.openai.com/api/docs/guides/latest-model (GPT-5.4 사용 가이드)
> - https://developers.openai.com/api/docs/models/gpt-5.4 (GPT-5.4 모델 스펙)
> - https://openai.com/index/introducing-gpt-5-4/ (GPT-5.4 발표)
> - https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide (GPT-5 시리즈 쿡북)
> - 적용 모델: GPT-5.4, GPT-5.4 Pro, GPT-5.4 Mini, GPT-5.4 Nano

## 핵심 요약

GPT-5.4는 2026년 3월 5일 출시된 OpenAI의 최신 프론티어 모델이다. 1M 토큰 컨텍스트 창, 네이티브 컴퓨터 사용, 빌트인 도구 오케스트레이션, reasoning effort 5단계(none~xhigh)를 지원한다. 핵심 전략은 "reasoning effort를 올리기 전에 프롬프트를 먼저 개선하라"이며, Output Contract, Verification Loop, Tool Persistence가 품질의 핵심 레버다.

---

## 1. GPT-5.4 아키텍처 특성

### GPT-5.2 → GPT-5.4 주요 개선

| 항목 | GPT-5.2 | GPT-5.4 |
|---|---|---|
| 컨텍스트 창 | 1M | 1,050,000 토큰 |
| 최대 출력 | 65,536 토큰 | 128,000 토큰 |
| reasoning effort | minimal/medium/high | none/low/medium/high/xhigh |
| 컴퓨터 사용 | 미지원 | 네이티브 지원 |
| 도구 검색 (Tool Search) | 미지원 | 지원 |
| verbosity | concise/standard/detailed | low/medium/high |
| 지식 컷오프 | 2025-04 | 2025-08-31 |
| 입력 가격 (1M 토큰) | $1.75 | $2.50 |
| 출력 가격 (1M 토큰) | $10.00 | $15.00 |
| 캐시 입력 | - | $0.25/1M |

### 모델 변형

| 변형 | 용도 |
|---|---|
| `gpt-5.4` | 범용 — 복잡한 추론, 코딩, 에이전트 워크플로 |
| `gpt-5.4-pro` | 최고 난이도 문제 (medium/high/xhigh만 지원) |
| `gpt-5.4-mini` | 대량 코딩 및 에이전트 워크플로 (비용 최적화) |
| `gpt-5.4-nano` | 단순 고처리량 태스크 (속도/비용 최우선) |

### 핵심 특성

- **프로덕션급 에이전트 설계**: 멀티스텝 추론, 증거 기반 합성, 장기 컨텍스트에서 안정적 성능
- **Output Contract 기반 동작**: 출력 계약, 도구 사용 기대, 완료 기준이 명확할수록 성능 향상
- **reasoning effort는 최종 튜닝 노브**: 프롬프트 품질이 1차 레버, reasoning effort는 2차

---

## 2. 핵심 API 파라미터

### reasoning.effort (추론 깊이 제어)

```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5.4",
    input="복잡한 플롯 분석 태스크...",
    reasoning={"effort": "medium"}
)
```

| 값 | 추론 깊이 | 적합 태스크 | 비고 |
|---|---|---|---|
| `none` (기본값) | 없음 | 실행 중심 태스크, 추출, 분류, 변환 | temperature/top_p 지원 |
| `low` | 최소 | 지연시간 민감, 가벼운 정확도 향상 | |
| `medium` | 균형 | 리서치, 멀티 문서 합성, 전략 작성 | |
| `high` | 깊은 추론 | 복잡한 추론, 지연/비용 감수 가능 시 | |
| `xhigh` | 최대 | 장기 에이전트 워크플로, 지능 최우선 | |

**권장**: 대부분의 팀은 `none`, `low`, `medium` 범위를 기본으로 사용. `none`으로 시작해서 eval 결과에 따라 올릴 것.

**중요**: temperature, top_p, logprobs는 `reasoning.effort`가 `none`일 때**만** 지원.

### verbosity (출력 길이 제어)

```python
response = client.responses.create(
    model="gpt-5.4",
    input="질문...",
    text={"verbosity": "low"}
)
```

| 값 | 설명 |
|---|---|
| `low` | 간결한 답변, 최소 코멘터리 |
| `medium` (기본값) | 균형 잡힌 설명 |
| `high` | 상세 설명, 인라인 주석 포함 코드 |

또는 프롬프트 내 자연어로 재정의:
```
3-6문장으로 간결하게 답하세요.
단순 예/아니오 질문은 2문장 이내로 답하세요.
```

---

## 3. 핵심 프롬프트 패턴 (공식 가이드 기반)

### Output Contract (출력 계약)

구조적 요구사항을 명시적으로 정의:

```xml
<output_contract>
- 요청된 섹션을 요청된 순서대로 정확히 반환하세요.
- 길이 제한은 해당 섹션에만 적용하세요.
- 형식이 요구되면(JSON, Markdown, SQL, XML) 해당 형식만 출력하세요.
</output_contract>
```

### Verbosity Controls (장황함 제어)

```xml
<verbosity_controls>
- 간결하고 정보 밀도가 높은 글쓰기를 선호하세요.
- 사용자의 요청을 반복하지 마세요.
- 진행 업데이트는 간략하게.
- 단, 필수 증거나 검증이 생략될 정도로 과도하게 줄이지 마세요.
</verbosity_controls>
```

### Default Follow-Through Policy (기본 실행 정책)

```xml
<default_follow_through_policy>
- 의도가 명확하고 다음 단계가 가역적/저위험이면 묻지 말고 진행하세요.
- 다음 경우에만 허가를 요청하세요: (a) 비가역적, (b) 외부 부작용 있음, (c) 민감 정보 부족.
</default_follow_through_policy>
```

### Instruction Priority (지시 우선순위)

```xml
<instruction_priority>
- 사용자 지시가 기본 스타일/톤/포맷을 오버라이드합니다.
- 안전, 정직, 프라이버시 제약은 양보하지 않습니다.
- 최신 사용자 지시가 이전 지시와 충돌하면 최신을 우선합니다.
- 충돌하지 않는 이전 지시는 유지합니다.
</instruction_priority>
```

---

## 4. 도구 사용 & 에이전트 패턴

### Tool Persistence Rules (도구 지속 규칙)

```xml
<tool_persistence_rules>
- 도구가 정확성이나 완전성을 실질적으로 개선할 때마다 사용하세요.
- 추가 도구 호출이 결과를 개선할 수 있다면 일찍 멈추지 마세요.
- 다음 조건이 모두 충족될 때까지 도구를 계속 호출하세요: (1) 태스크 완료, (2) 검증 통과.
- 도구가 빈/부분 결과를 반환하면 다른 전략으로 재시도하세요.
</tool_persistence_rules>
```

### Dependency Checks (의존성 검사)

```xml
<dependency_checks>
- 행동하기 전에 선행 조건 탐색/조회 단계가 필요한지 확인하세요.
- 최종 행동이 명확해 보여도 선행 조건을 건너뛰지 마세요.
- 태스크가 이전 단계 출력에 의존하면 먼저 해당 의존성을 해결하세요.
</dependency_checks>
```

### Parallel Tool Calling (병렬 도구 호출)

```xml
<parallel_tool_calling>
- 여러 검색 단계가 독립적이면 병렬 호출을 선호하세요.
- 선행 의존성이 있는 단계는 병렬화하지 마세요.
- 병렬 검색 후, 추가 호출 전에 잠시 합성하세요.
- 선택적 병렬화: 독립적 증거 수집은 병렬, 투기적 사용은 순차.
</parallel_tool_calling>
```

### Completeness Contract (완전성 계약)

```xml
<completeness_contract>
- 요청된 모든 항목이 처리되거나 [blocked]로 표시될 때까지 태스크를 미완료로 취급하세요.
- 필수 산출물의 내부 체크리스트를 유지하세요.
- 목록/배치/페이지네이션: 예상 범위를 파악하고, 처리 항목을 추적하고, 완료 전 커버리지를 확인하세요.
- 누락 데이터로 차단된 항목은 [blocked]로 표시하고 정확히 무엇이 부족한지 명시하세요.
</completeness_contract>
```

### Empty Result Recovery (빈 결과 복구)

```xml
<empty_result_recovery>
조회가 빈/부분/의심스럽게 좁은 결과를 반환하면:
- 결과가 없다고 즉시 결론 내리지 마세요.
- 최소 1~2개 대안 전략을 시도하세요: 다른 표현, 넓은 필터, 선행 조회, 대체 소스.
- 그 후에만 결과가 없다고 보고하되, 시도한 내용을 포함하세요.
</empty_result_recovery>
```

### Preambles (도구 호출 전 설명)

GPT-5.4는 도구 호출 전 간단한 설명을 자동 생성한다. 활성화:

```
도구를 호출하기 전에, 왜 호출하는지 설명하세요.
```

**효과**: 도구 호출 정확도를 높이되 추론 오버헤드는 최소화.

### Tool Search (도구 검색)

대규모 도구 생태계에서 필요한 도구 정의만 런타임에 로드:
- 토큰 사용량 감소
- 도구가 많은 시스템에서 정확도 향상

---

## 5. 검증 & 안전

### Verification Loop (검증 루프)

```xml
<verification_loop>
최종화 전:
- 정확성 검사: 출력이 모든 요구사항을 충족하는가?
- 근거 검사: 사실적 주장이 컨텍스트나 도구 출력으로 뒷받침되는가?
- 포맷 검사: 요청된 스키마/스타일과 일치하는가?
- 안전/비가역성 검사: 다음 단계에 외부 효과가 있으면 먼저 허가를 요청하세요.
</verification_loop>
```

### Missing Context Gating (누락 컨텍스트 게이팅)

```xml
<missing_context_gating>
- 필수 컨텍스트가 없으면 추측하지 마세요.
- 검색 가능하면 도구를 사용; 아니면 명확히 질문.
- 진행해야 하면 가정을 명시적으로 표시하고 가역적 행동을 선택하세요.
</missing_context_gating>
```

### Action Safety Frame (행동 안전 프레임)

```xml
<action_safety>
- 사전 점검: 의도한 행동과 파라미터를 1-2줄로 요약.
- 도구로 실행.
- 사후 점검: 결과와 수행한 검증을 확인.
</action_safety>
```

---

## 6. 리서치 & 인용

### Research Mode (리서치 모드)

```xml
<research_mode>
리서치를 3패스로 수행하세요:
  1) 계획: 답해야 할 3-6개 하위 질문 나열.
  2) 검색: 각 하위 질문을 검색하고 1-2개 2차 리드 추적.
  3) 합성: 모순을 해결하고 인용 포함 최종 답변 작성.
- 추가 검색이 결론을 바꿀 가능성이 낮을 때만 중단.
</research_mode>
```

### Citation Rules (인용 규칙)

```xml
<citation_rules>
- 현재 워크플로에서 검색된 소스만 인용하세요.
- 인용, URL, ID, 인용구를 절대 날조하지 마세요.
- 호스트 애플리케이션이 요구하는 정확한 인용 형식을 사용하세요.
- 인용을 끝에만 모으지 말고 특정 주장에 첨부하세요.
</citation_rules>
```

### Grounding Rules (근거 규칙)

```xml
<grounding_rules>
- 주장은 제공된 컨텍스트나 도구 출력에만 근거하세요.
- 소스가 충돌하면 충돌을 명시하고 각 측을 귀속시키세요.
- 컨텍스트가 불충분하면 답변 범위를 좁히거나 지원 불가를 명시하세요.
- 직접 지원 사실이 아닌 추론이면 추론임을 표시하세요.
</grounding_rules>
```

---

## 7. Phase 파라미터 (Responses API)

장기 실행, 도구 집약적 흐름에서 작업 중간 코멘터리와 최종 답변을 구분:

```python
response = client.responses.create(
    model="gpt-5.4",
    input=[
        {
            "role": "assistant",
            "phase": "commentary",
            "content": "로그를 검사하고 근본 원인을 요약하겠습니다."
        },
        {
            "role": "assistant",
            "phase": "final_answer",
            "content": "근본 원인: 캐시 무효화 경쟁 조건."
        },
        {
            "role": "user",
            "content": "롤아웃 안전한 수정 계획을 제공하세요."
        }
    ]
)
```

**주의사항**:
- `phase` 값을 어시스턴트 히스토리 리플레이 시 반드시 보존할 것
- 누락/삭제된 `phase`는 preamble이 최종 답변으로 해석되는 오류 유발
- 사용자 메시지에는 `phase` 추가하지 말 것
- 가능하면 `previous_response_id` 사용 (OpenAI가 이전 상태를 복원)

---

## 8. previous_response_id (추론 컨텍스트 보존)

멀티턴 에이전트에서 이전 추론 체인을 보존하는 핵심 기능:

```python
# 첫 번째 호출
first_response = client.responses.create(
    model="gpt-5.4",
    reasoning={"effort": "high"},
    input="EP-05 플롯 분석..."
)

# 두 번째 호출 - 이전 추론 컨텍스트 재사용
second_response = client.responses.create(
    model="gpt-5.4",
    previous_response_id=first_response.id,
    input="이제 분석을 바탕으로 초고를 작성하세요."
)
```

**효과**:
- CoT 토큰 보존 → 처음부터 계획 재구성 불필요
- 지능 향상, 추론 토큰 절감, 캐시 히트율 증가, 지연시간 감소
- 멀티스텝 에이전트 작업에서 일관성 유지

---

## 9. 컨텍스트 창 압축 (Compaction)

장기 세션에서 컨텍스트 창 확장을 위한 `/responses/compact` API:

- 주요 마일스톤 후에 compact 실행
- 압축된 항목은 `encrypted_content`로 불투명 상태 유지
- compact 후에도 프롬프트 기능이 동일하게 유지되도록 설계
- GPT-5.4는 compaction 사용 시 멀티턴 대화에서 더 일관적

---

## 10. 모델 변형별 프롬프팅 전략

### gpt-5.4 (기본)

범용 사용. 대부분의 태스크에 적합.

### gpt-5.4-pro

최고 난이도 문제. `reasoning.effort`: medium/high/xhigh만 지원.

### gpt-5.4-mini (주의 필요)

GPT-5.4보다 더 문자 그대로 해석, 암묵적 가정이 약함:

```
프롬프팅 전략:
- 중요한 규칙을 먼저 배치
- 도구 사용/부작용의 전체 실행 순서를 명시
- 구조적 스캐폴딩 사용 (번호 단계, 결정 규칙, 행동 정의)
- "행동 실행"과 "행동 보고"를 분리
- 최종 형식뿐 아니라 올바른 흐름을 보여주기
- 모호성 행동을 명시적으로 정의
- 패키징 직접 지정 (길이, 후속 질문, 인용 스타일, 섹션 순서)
- 범위 지정 지시 사용; 포괄적 "그 외 아무것도 출력하지 마라" 지양
```

### gpt-5.4-nano (매우 제한적)

좁고 명확한 태스크에만 사용:

```
적합: 라벨, enum, 짧은 JSON, 고정 템플릿
부적합: 멀티스텝 오케스트레이션, 모호성 해결
기본 패턴:
1. 태스크
2. 핵심 규칙
3. 정확한 단계 순서
4. 엣지 케이스/명확화 행동
5. 출력 형식
6. 올바른 예시 1개
```

---

## 11. 마이그레이션 가이드

### 마이그레이션 순서 (한 번에 한 가지만 변경)

1. 모델을 먼저 교체
2. `reasoning.effort`를 현재 설정에 맞춰 고정
3. eval 실행
4. 그 후 반복 개선

### 출발 모델별 권장 시작점

| 출발 모델 | 시작 reasoning effort |
|---|---|
| GPT-5.2 | 현재 설정과 동일하게 |
| GPT-5.3 Codex | 현재 설정과 동일하게 |
| GPT-4.1 / GPT-4o | `none`으로 시작, eval 후 올릴 것 |
| o3 시리즈 | `medium`으로 시작, 프롬프트 튜닝 |
| 리서치 어시스턴트 | `medium` 또는 `high` |
| 장기 에이전트 | `medium` 또는 `high` |

### reasoning effort 올리기 전에 먼저 추가할 것

1. `<completeness_contract>` — 완전성 계약
2. `<verification_loop>` — 검증 루프
3. `<tool_persistence_rules>` — 도구 지속 규칙

모델이 여전히 너무 표면적이면:

```xml
<dig_deeper_nudge>
- 첫 번째 그럴듯한 답에 멈추지 마세요.
- 2차 이슈, 엣지 케이스, 누락된 제약을 찾으세요.
- 안전/정확성이 중요한 태스크면 최소 1회 검증 단계를 수행하세요.
</dig_deeper_nudge>
```

---

## 12. 구조화된 출력 (Structured Output)

```python
from pydantic import BaseModel
from typing import List

class EpisodeValidation(BaseModel):
    char_count: int
    scene_count: int
    img_marker_count: int
    cliffhanger_present: bool
    issues: List[str]

response = client.responses.create(
    model="gpt-5.4",
    input="다음 에피소드를 검증하세요: ...",
    text={
        "format": {
            "type": "json_schema",
            "schema": EpisodeValidation.model_json_schema()
        }
    }
)
result = EpisodeValidation.model_validate_json(response.output_text)
```

---

## 13. 코딩 에이전트 패턴

### Autonomy & Persistence (자율성 & 지속성)

```xml
<autonomy_and_persistence>
태스크가 분석이나 부분 수정이 아닌 구현, 검증, 결과 설명까지 완전히 처리될 때까지 지속하세요.
명시적 중단/방향 전환 요청이 없는 한 계속 진행하세요.
사용자가 명시적으로 계획을 요청하지 않는 한, 코드 변경이나 도구 실행으로 문제를 해결하세요.
도전에 부딪히면 직접 해결을 시도하세요.
</autonomy_and_persistence>
```

### User Updates (사용자 업데이트)

```xml
<user_updates_spec>
- 중간 업데이트는 `commentary` 채널로 전송.
- 진행 상황과 새로운 정보를 전달하는 1-2문장 업데이트 사용.
- 대화형 감탄사나 메타 코멘터리로 시작하지 마세요.
- 상당한 작업 전에 이해한 내용과 첫 단계를 설명하는 업데이트 전송.
- 작업 중 약 30초마다 업데이트 제공.
- 오래 작업할 때는 업데이트를 유익하고 다양하게, 하지만 간결하게.
- 충분한 컨텍스트를 모은 후 더 긴 계획 제공.
- 파일 편집 전에 변경할 내용을 설명.
</user_updates_spec>
```

### Terminal Tool Hygiene (터미널 도구 위생)

```xml
<terminal_tool_hygiene>
- 셸 명령은 오직 터미널 도구를 통해서만 실행.
- 도구 이름을 셸 명령으로 "실행"하지 마세요.
- 패치/편집 도구가 있으면 직접 사용; bash에서 시도하지 마세요.
- 변경 후, 태스크 완료 선언 전에 경량 검증(ls, 테스트, 빌드) 실행.
</terminal_tool_hygiene>
```

---

## 14. 한국어 토큰 효율

한국어는 영어보다 토큰 소비가 많다 (평균 1글자당 약 1.5~2 토큰). 효율화 전략:

**시스템 프롬프트 효율화**:
```
# 비효율 (중복 설명)
당신은 훌륭하고 뛰어나며 전문적인 한국어 웹소설 작가입니다.

# 효율적 (핵심만)
한국 웹소설 작가. 로맨스 판타지 전문. 독자 몰입 최우선.
```

**토큰 예산 추정** (한국어 기준):
```
시스템 프롬프트: ~2,000 토큰
로어 컨텍스트: ~5,000 토큰
이전 에피소드 요약: ~1,000 토큰
현재 아웃라인: ~1,000 토큰
생성 대상: 4,000~5,000자 ≈ ~6,000~8,000 토큰
총계: ~15,000~17,000 토큰
```

**272K 토큰 임계값 주의**: 프롬프트가 272K 토큰을 초과하면 입력 2배, 출력 1.5배 가격 적용.

---

## 15. 모델별 권장 설정 요약

| 모델 | 용도 | reasoning.effort | verbosity | 비고 |
|---|---|---|---|---|
| gpt-5.4 (기본) | 범용 복잡 태스크, 에이전트 | none~medium | medium | 대부분의 팀 기본값 |
| gpt-5.4 (리서치) | 멀티 문서 합성, 전략 | medium~high | high | research_mode 추가 |
| gpt-5.4 (장기 에이전트) | 장기 워크플로 | medium~xhigh | medium | phase + previous_response_id |
| gpt-5.4-pro | 최고 난이도 | medium~xhigh | - | 비용 민감 시 gpt-5.4로 대체 |
| gpt-5.4-mini | 대량 코딩/에이전트 | none~medium | low~medium | 구조적 스캐폴딩 필수 |
| gpt-5.4-nano | 분류, 추출, 라벨링 | none | low | 좁은 태스크만 |

---

## 우리 파이프라인 적용 포인트

| 파이프라인 단계 | 모델 | 설정 | 핵심 프롬프트 전략 |
|---|---|---|---|
| 장르 리서치 | gpt-5.4 | effort: medium, verbosity: medium | research_mode + citation_rules |
| 스토리 구조 | gpt-5.4 | effort: high, verbosity: high | output_contract + dependency_checks |
| 아웃라인 생성 | gpt-5.4 | effort: high, verbosity: high | completeness_contract + previous_response_id |
| 플롯 설계 | gpt-5.4 | effort: high | parallel_tool_calling + verification_loop |
| 초고 집필 | gpt-5.4 | effort: none~low, verbosity: high | output_contract + 글자수 명시 |
| 문체 리뷰 | gpt-5.4-mini | effort: low, verbosity: low | 구조적 스캐폴딩 + 평가 기준 명시 |
| 검증 | gpt-5.4 | effort: medium | verification_loop + structured_output |
| 빠른 분류 | gpt-5.4-nano | effort: none | 단순 지시 + 짧은 컨텍스트 |

---

## 추가 참고 자료

- [GPT-5.4 Prompt Guidance (공식)](https://developers.openai.com/api/docs/guides/prompt-guidance)
- [Using GPT-5.4 (공식)](https://developers.openai.com/api/docs/guides/latest-model)
- [GPT-5.4 Model Spec (공식)](https://developers.openai.com/api/docs/models/gpt-5.4)
- [Introducing GPT-5.4 (공식 발표)](https://openai.com/index/introducing-gpt-5-4/)
- [GPT-5 Prompting Cookbook](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
- [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [GPT-5.4 Complete Guide (ThePromptBuddy)](https://www.thepromptbuddy.com/prompts/gpt-5-4-complete-guide-features-and-what-s-new-2026)
- [GPT-5.4 API Guide (CometAPI)](https://www.cometapi.com/how-to-use-gpt-5-4-api/)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)

## 버전 노트

- GPT-5 (gpt-5): 2025년 출시, 추론 기능 도입
- GPT-5.1: 프롬프팅 가이드 초판
- GPT-5.2 (gpt-5.2): 2025년 후반, 간결성/포맷 개선, `verbosity` 파라미터 추가
- GPT-5.3-Codex: 코드 특화 버전
- **GPT-5.4 (gpt-5.4)**: 2026-03-05 출시, 1M 컨텍스트, 네이티브 컴퓨터 사용, Tool Search, phase 파라미터, 5단계 reasoning effort (none~xhigh), 128K 출력 토큰
- GPT-5.4 Pro (gpt-5.4-pro): 최고 성능 변형
- GPT-5.4 Mini (gpt-5.4-mini): 대량 처리 최적화
- GPT-5.4 Nano (gpt-5.4-nano): 속도/비용 최우선
