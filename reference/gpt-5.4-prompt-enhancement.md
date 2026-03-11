# GPT-5 / GPT-5.2 프롬프트 전략 가이드

> 최종 업데이트: 2026-03 | 출처:
> - https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide
> - https://www.atlabs.ai/blog/gpt-5.2-prompting-guide-the-2026-playbook-for-developers-agents
> - https://platform.openai.com/docs/guides/prompt-engineering

## 핵심 요약

GPT-5/5.2는 강력한 추론 능력과 에이전트 자율성을 갖추고 있으며, `reasoning_effort`와 `verbosity` 파라미터로 추론 깊이와 출력 길이를 독립적으로 제어할 수 있다. 컨텍스트 압축 패턴(CTCO)과 Responses API의 `previous_response_id`를 활용하면 장기 에이전트 워크플로에서 성능과 비용 효율이 크게 향상된다.

---

## 1. GPT-5 아키텍처 특성 이해

### 추론 기반 생성

GPT-5는 응답 전에 내부 추론 과정을 실행한다. 이 추론 과정이 토큰을 소비하므로 비용과 지연시간에 영향을 준다.

**핵심 특성**:
- 모호하거나 모순된 지시는 추론 토큰을 소비하며 "조정"한다
- 잘못 구성된 프롬프트는 GPT-4보다 더 큰 성능 저하를 일으킨다
- 프롬프트 명확성이 이전 모델보다 훨씬 중요하다

### GPT-5.2의 개선점

- 더 간결하고 태스크 집중적 (불필요한 장황함 감소)
- 클리너한 포맷 생성 (구조화된 출력 신뢰도 향상)
- 더 강한 지시 따르기 능력

---

## 2. 핵심 API 파라미터

### reasoning_effort

추론 깊이를 제어하는 파라미터:

```python
response = client.responses.create(
    model="gpt-5.2",
    reasoning_effort="medium",  # minimal / medium / high
    input="복잡한 플롯 분석 태스크..."
)
```

| 값 | 추론 깊이 | 적합 태스크 |
|---|---|---|
| `minimal` | 최소 | 간단한 분류, 빠른 응답 |
| `medium` | 중간 | 표준 생성, 분석 |
| `high` | 최대 | 복잡한 추론, 플롯 설계 |

### verbosity

출력 길이를 추론과 독립적으로 제어:

```python
response = client.responses.create(
    model="gpt-5.2",
    verbosity="concise",  # minimal / concise / standard / detailed
    input="..."
)
```

또는 프롬프트 내 자연어로 재정의:
```
3-6문장으로 간결하게 답하세요.
단순 예/아니오 질문은 2문장 이내로 답하세요.
```

---

## 3. CTCO 패턴 (Context-Task-Constraints-Output)

GPT-5.2에서 환각 방지에 가장 신뢰할 수 있는 프롬프트 구조:

```
[Context] 모델이 누구이고 배경 상태가 무엇인지
[Task] 요구되는 단일하고 원자적인 행동
[Constraints] 부정적 제약사항과 범위 제한
[Output] 원하는 출력 형식 명세
```

**예시**:
```
[Context]
당신은 한국 웹소설 로맨스 판타지 장르 전문 작가입니다.
다음 로어 파일과 EP-04 아웃라인을 기반으로 작업합니다.

[Task]
EP-05의 1화 초고를 작성하세요. (4,000~5,000자)

[Constraints]
- EP-04의 클리프행어를 직접 이어받으세요
- 새로운 주인공을 도입하지 마세요
- 아직 공개되지 않은 비밀을 누설하지 마세요

[Output]
마크다운 없이 순수 텍스트로 출력하세요.
IMG 마커는 [IMG: 설명] 형식으로 3개 삽입하세요.
```

---

## 4. Responses API와 컨텍스트 유지

### previous_response_id 활용

에이전트 워크플로에서 이전 추론 컨텍스트를 보존하는 핵심 기능:

```python
# 첫 번째 호출
first_response = client.responses.create(
    model="gpt-5.2",
    reasoning_effort="high",
    input="EP-05 플롯 분석..."
)

# 두 번째 호출 - 이전 추론 컨텍스트 재사용
second_response = client.responses.create(
    model="gpt-5.2",
    previous_response_id=first_response.id,  # 핵심!
    input="이제 분석을 바탕으로 초고를 작성하세요."
)
```

**효과**:
- CoT 토큰 보존 → 처음부터 계획을 재구성할 필요 없음
- 성능 통계적으로 유의미한 향상
- 멀티스텝 에이전트 작업에서 일관성 유지

---

## 5. 에이전트 자율성 제어

### 적극적 탐색 제어

```python
# 범위 축소 (더 집중된 실행)
response = client.responses.create(
    model="gpt-5.2",
    reasoning_effort="low",
    input="""
    다음 단일 태스크만 수행하세요. 탐색 범위는 characters.md로 제한합니다.
    다른 파일은 열지 마세요.
    태스크: 소피아의 성격 특성 3가지를 추출하세요.
    """
)

# 범위 확대 (더 자율적 탐색)
response = client.responses.create(
    model="gpt-5.2",
    reasoning_effort="high",
    input="""
    EP-05~EP-10의 플롯 일관성을 전면적으로 검토하세요.
    관련 모든 파일을 참조하고, 발견한 문제를 모두 보고하세요.
    """
)
```

### Tool Preamble (도구 전 계획)

GPT-5는 도구 실행 전에 계획을 먼저 서술하도록 훈련되어 있다:

```
각 도구 호출 전에 한 문장으로 수행할 작업을 설명하세요.
도구 완료 후 결과를 한 줄로 요약하고 다음 단계를 제시하세요.
```

---

## 6. 출력 길이 제어

### 길이 기본값 설정

```
응답 길이 가이드라인:
- 일반 답변: 3-6문장
- 목록 항목: 최대 5개 항목
- 예/아니오 질문: 2문장 이내
- 코드 블록: 필요한 코드만 (설명은 최소화)
- 장문 창작: 지정된 글자 수 범위 내 (예: 4,000~5,000자)
```

### 장문 창작을 위한 출력 제어

```
정확히 4,000~5,000자의 한국어 에피소드를 작성하세요.
응답은 에피소드 본문만 포함하세요. 설명, 메타 코멘트, 요약은 제외하세요.
작성 중에 토큰이 부족해지면 자연스러운 단락 경계에서 중단하고
"[계속]"을 붙여주세요.
```

---

## 7. 한국어 토큰 효율

### 한국어 토큰 특성

한국어는 영어보다 토큰 소비가 많다 (평균 1글자당 약 1.5~2 토큰). 효율화 전략:

**시스템 프롬프트 효율화**:
```
# 비효율 (중복 설명)
당신은 훌륭하고 뛰어나며 전문적인 한국어 웹소설 작가입니다.
한국어로 작성하는 것을 매우 잘하며 독자들이 좋아하는 스타일로 씁니다.

# 효율적 (핵심만)
한국 웹소설 작가. 로맨스 판타지 전문. 독자 몰입 최우선.
```

**컨텍스트 배치 우선순위**:
1. 현재 태스크에 직접 관련된 설정만 포함
2. 전체 로어 파일 대신 해당 에피소드 관련 섹션만 추출
3. 이전 에피소드 전체 텍스트 대신 핵심 사건 요약본 사용

**토큰 예산 추정** (한국어 기준):
```
시스템 프롬프트: ~2,000 토큰
로어 컨텍스트: ~5,000 토큰
이전 에피소드 요약: ~1,000 토큰
현재 아웃라인: ~1,000 토큰
생성 대상: 4,000~5,000자 ≈ ~6,000~8,000 토큰
총계: ~15,000~17,000 토큰
```

---

## 8. 구조화된 출력 (Structured Output)

```python
from pydantic import BaseModel
from typing import List

class EpisodeValidation(BaseModel):
    char_count: int
    scene_count: int
    img_marker_count: int
    cliffhanger_present: bool
    issues: List[str]

response = client.responses.parse(
    model="gpt-5.2",
    input="다음 에피소드를 검증하세요: ...",
    text={"format": {"type": "json_schema", "schema": EpisodeValidation.model_json_schema()}}
)
result = EpisodeValidation.model_validate_json(response.output_text)
```

---

## 9. 프롬프트 품질 검증

GPT-5.2는 OpenAI의 프롬프트 최적화 도구 사용을 권장한다:

- 모순된 지시 감지
- 모호한 표현 식별
- 불필요한 중복 발견

**300단어 초과 프롬프트 점검 기준**:
- 모든 문장이 명확한 기능을 하는가?
- 같은 내용이 반복되지 않는가?
- 중요한 정보가 컨텍스트 창 중간에 묻히지 않는가?

---

## 10. 코딩 태스크 특화 전략

```
다음 규칙에 따라 코드를 작성하세요:
- 프레임워크: Python 3.11, pathlib 사용
- 변수명: 설명적이고 의도가 명확한 이름 사용
- 주석: 핵심 로직에 충분한 설명 (간결성보다 가독성 우선)
- 디렉토리 구조: [명시적 경로 제공]
- 오류 처리: 모든 외부 파일/API 호출에 try/except 추가
```

---

## 우리 파이프라인 적용 포인트

| 파이프라인 단계 | GPT-5.2 설정 | 핵심 전략 |
|---|---|---|
| 초고 집필 | `reasoning_effort: medium`, `verbosity: detailed` | CTCO 패턴, 글자수 명시 |
| 플롯 분석 | `reasoning_effort: high`, `previous_response_id` | 컨텍스트 체인, 구조화 출력 |
| 일관성 검증 | `reasoning_effort: high`, Structured Output | EpisodeValidation 스키마 |
| 빠른 분류 | `reasoning_effort: minimal` | 간단한 지시, 짧은 컨텍스트 |
| 한국어 생성 | 모든 단계 | 토큰 효율 최적화 컨텍스트 |

---

## 추가 참고 자료

- [GPT-5 Prompting Guide (OpenAI Cookbook)](https://developers.openai.com/cookbook/examples/gpt-5/gpt-5_prompting_guide)
- [GPT-5.2 Prompting Guide - Atlabs](https://www.atlabs.ai/blog/gpt-5.2-prompting-guide-the-2026-playbook-for-developers-agents)
- [OpenAI Prompt Engineering](https://platform.openai.com/docs/guides/prompt-engineering)
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)

## 버전 노트

- GPT-5 (gpt-5): 2025년 출시, 강력한 추론 기능 도입
- GPT-5.2 (gpt-5.2): 2025년 후반, 간결성/포맷 개선, `verbosity` 파라미터 추가
- GPT-5.2-Codex: 코드 특화 버전, reasoning_effort에 더 민감하게 반응
- 이 문서의 파라미터는 OpenAI API 기준이며 Azure OpenAI에서 지원 여부 별도 확인 필요
