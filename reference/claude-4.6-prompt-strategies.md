# Claude 4.6 프롬프트 전략 가이드

> 최종 업데이트: 2026-03 | 출처:
> - https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices
> - https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/overview
> - 적용 모델: Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5

## 핵심 요약

Claude 4.6 (Opus/Sonnet)은 이전 세대보다 훨씬 더 자율적이고 도구 사용에 적극적이다. 프롬프트는 "엄격한 규칙"보다 "올바른 고도의 휴리스틱"으로 작성해야 하며, Adaptive Thinking, 병렬 도구 호출, 서브에이전트 오케스트레이션이 핵심 기능이다.

---

## 1. 일반 원칙

### 명확하고 직접적으로 지시하기

Claude는 새로 입사한 유능한 직원처럼 행동한다. 맥락과 규범을 모르므로 명확히 설명해야 한다.

**황금 규칙**: 프롬프트를 맥락을 모르는 동료에게 보여줬을 때 혼란스럽다면, Claude도 혼란스럽다.

```
# 덜 효과적
분석 대시보드를 만드세요.

# 더 효과적
분석 대시보드를 만드세요. 관련 기능과 상호작용을 최대한 포함하세요.
기본 수준을 넘어 완전히 구현된 버전을 만드세요.
```

### 맥락과 이유 제공

지시사항 뒤에 이유를 추가하면 성능이 향상된다.

```
# 덜 효과적
줄임표(...)를 절대 사용하지 마세요.

# 더 효과적
응답은 TTS 엔진이 읽어줄 것입니다. TTS가 줄임표를 발음하지 못하므로 절대 사용하지 마세요.
```

### 예시 효과적으로 사용하기

- 3~5개 예시가 최적
- `<example>` 태그로 감싸기 (`<examples>` 태그 안에 복수 예시)
- 엣지 케이스 포함, 의도치 않은 패턴 방지

### XML 태그로 프롬프트 구조화

복잡한 프롬프트에서 XML 태그는 모호성을 제거한다.

```xml
<instructions>행동 지침</instructions>
<context>배경 정보</context>
<input>사용자 입력</input>
<examples>
  <example><input>...</input><output>...</output></example>
</examples>
```

### 역할(Role) 부여

시스템 프롬프트의 역할 한 문장이 큰 차이를 만든다.

```python
client.messages.create(
    model="claude-opus-4-6",
    system="당신은 한국 웹소설 전문 작가입니다. 로맨스 판타지 장르에 특화되어 있습니다.",
    messages=[{"role": "user", "content": "..."}]
)
```

---

## 2. 출력 및 포맷 제어

### 간결성과 자연스러운 소통

Claude 4.6은 이전 모델보다 더 간결하고 자연스럽다. 도구 호출 후 요약을 생략하고 바로 다음 행동으로 넘어갈 수 있다. 요약이 필요하면 명시적으로 요청:

```
도구를 사용한 후, 수행한 작업을 간략히 요약하세요.
```

### 포맷 제어 4가지 방법

1. "하지 마라" 대신 "이렇게 하라"로 지시:
   ```
   # 대신: "마크다운을 사용하지 마세요"
   # 사용: "자연스럽게 흐르는 산문 단락으로 응답하세요."
   ```

2. XML 포맷 지시자 활용:
   ```
   응답의 산문 섹션은 <smooth_prose> 태그 안에 작성하세요.
   ```

3. 프롬프트 스타일을 원하는 출력 스타일과 일치시키기 (마크다운 없는 프롬프트 → 마크다운 없는 출력)

4. 상세 포맷 가이드라인 명시 (아래 예시 참조):

```xml
<avoid_excessive_markdown>
보고서, 기술 설명, 분석 작성 시 완전한 문단과 문장으로 이루어진 산문을 사용하세요.
마크다운은 인라인 코드, 코드 블록, 단순 제목(###)에만 사용하세요.
**굵게**나 *기울임*은 피하세요.
목록(1./*)은 진정으로 분리된 항목에만 사용하세요.
</avoid_excessive_markdown>
```

### Prefilled Response 마이그레이션

Claude 4.6부터 마지막 어시스턴트 턴의 prefill이 지원되지 않는다.

| 기존 prefill 용도 | 대체 방법 |
|---|---|
| 출력 형식 강제 | Structured Outputs 기능 |
| 서문 제거 | 시스템 프롬프트: "서론 없이 바로 응답하세요" |
| 불필요한 거부 방지 | 명확한 user 메시지 지시 |
| 이전 응답 이어받기 | user 메시지: "이전 응답이 [내용]에서 중단됐습니다. 이어서 작성하세요." |

---

## 3. 도구 사용 (Tool Use)

### 명시적 행동 지시

Claude 4.6은 정확한 지시 따르기로 훈련됐다. 모호하면 제안만 하고 실행 안 함.

```
# 제안만 함 (원하지 않는 동작)
이 함수를 개선할 방법을 제안해줄 수 있나요?

# 실행함 (원하는 동작)
이 함수의 성능을 개선하세요.
```

적극적 행동 기본값 설정:
```xml
<default_to_action>
기본적으로 변경사항을 구현하세요. 사용자 의도가 불명확하면 가장 유용한 행동을 추론하고 도구로 세부사항을 파악한 후 진행하세요.
</default_to_action>
```

보수적 행동 기본값 설정:
```xml
<do_not_act_before_instructions>
명확히 지시받기 전에는 구현이나 파일 변경을 하지 마세요. 모호할 때는 정보 제공, 리서치, 권장사항만 제시하세요.
</do_not_act_before_instructions>
```

### 병렬 도구 호출 최적화

Claude 4.6은 병렬 도구 실행에 탁월하다. 100% 병렬 호출을 위한 프롬프트:

```xml
<use_parallel_tool_calls>
독립적인 도구 호출이 여러 개면 모두 동시에 실행하세요.
예: 3개 파일을 읽을 때 3개 도구 호출을 병렬로 실행해 속도를 높이세요.
단, 이전 호출 결과가 필요한 의존적 호출은 순차적으로 실행하세요.
</use_parallel_tool_calls>
```

**주의**: Claude Opus 4.5/4.6은 이전 모델에서 도구 미작동을 유도하던 공격적 언어("반드시 사용해야 한다", "CRITICAL")가 이제 과도 작동을 일으킬 수 있다. 보통 수준의 언어로 완화:
- 이전: `CRITICAL: 이 도구를 반드시 사용해야 한다`
- 이후: `이 상황에서 이 도구를 사용하세요`

---

## 4. Thinking & Reasoning (사고 기능)

### Adaptive Thinking (Claude Opus 4.6 기본)

Claude Opus 4.6은 adaptive thinking(`thinking: {type: "adaptive"}`)을 사용한다. 모델이 언제 얼마나 생각할지 동적으로 결정.

```python
# Opus 4.6 - Adaptive Thinking
client.messages.create(
    model="claude-opus-4-6",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # max/high/medium/low
    messages=[{"role": "user", "content": "..."}],
)
```

**effort 파라미터**:
- `max`: 최대 추론 (장기 복잡 태스크)
- `high`: 높은 추론 (기본값 Sonnet 4.6)
- `medium`: 균형 (대부분 코딩 태스크)
- `low`: 빠른 응답 (간단한 태스크, 비용 민감)

### Extended Thinking (Claude Sonnet 4.6)

Sonnet 4.6은 manual extended thinking도 지원:

```python
# Sonnet 4.6 - Extended Thinking with budget
client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=16384,
    thinking={"type": "enabled", "budget_tokens": 16384},
    output_config={"effort": "medium"},
    messages=[{"role": "user", "content": "..."}],
)
```

### 과도한 사고(overthinking) 제어

Opus 4.6은 특히 높은 effort에서 광범위한 탐색을 한다. 제어 방법:

```
문제 접근 방식을 결정할 때, 하나를 선택하고 실행하세요.
새 정보가 없는 한 결정을 재검토하지 마세요. 두 가지 접근이 있으면 하나를 선택하고 진행하세요.
```

### 사고 유도 프롬프팅

```
도구 결과를 받은 후, 품질을 신중히 평가하고 다음 최적 단계를 결정하세요.
thinking을 활용해 새 정보를 바탕으로 계획하고 반복한 후 최선의 다음 행동을 취하세요.
```

Extended thinking이 없을 때 수동 CoT:
```xml
<thinking>
[여기서 단계별로 추론]
</thinking>
<answer>
[최종 답변]
</answer>
```

**주의**: Extended thinking 비활성화 시, Opus 4.5는 "think"라는 단어에 민감하다. "consider", "evaluate", "reason through" 같은 대안어 사용 권장.

---

## 5. 에이전트 시스템

### 장기 추론 및 상태 추적

Claude 4.6은 긴 세션에서 방향성을 유지한다. 컨텍스트 압축(context compaction)이 자동으로 일어나는 환경에서의 프롬프트:

```
컨텍스트 창이 한계에 도달하면 자동으로 압축되어 중단 없이 계속 작업할 수 있습니다.
따라서 토큰 예산 우려로 작업을 일찍 중단하지 마세요.
토큰 예산 한계에 가까워지면 컨텍스트 창이 갱신되기 전에 현재 진행 상황과 상태를 메모리에 저장하세요.
태스크가 완전히 완료될 때까지 가능한 한 자율적이고 지속적으로 작업하세요.
```

### 멀티 컨텍스트 창 워크플로

1. **첫 번째 컨텍스트 창**: 프레임워크 설정 (테스트 작성, 설정 스크립트)
2. **이후 컨텍스트 창**: todo 목록 기반 반복 작업

상태 추적 권장 형식:
```json
// structured state (tests.json)
{
  "tasks": [
    { "id": 1, "name": "task_name", "status": "completed" },
    { "id": 2, "name": "next_task", "status": "in_progress" }
  ]
}

// progress notes (progress.txt)
세션 3 진행:
- 완료: 인증 토큰 검증 수정
- 다음: 사용자 관리 테스트 실패 조사 (task #2)
```

### 자율성과 안전성 균형

```
행동의 가역성과 잠재적 영향을 고려하세요.
파일 편집, 테스트 실행 같은 로컬 가역적 행동은 자유롭게 하세요.
가역하기 어렵거나 공유 시스템에 영향을 주거나 파괴적일 수 있는 행동에는 먼저 확인을 요청하세요.

확인이 필요한 예시:
- 파괴적 작업: 파일/브랜치 삭제, DB 테이블 삭제
- 되돌리기 어려운 작업: git push --force, 공개 커밋 수정
- 다른 사람에게 보이는 작업: 코드 푸시, PR 댓글, 메시지 발송
```

### 서브에이전트 오케스트레이션

Opus 4.6은 서브에이전트 위임을 자동으로 인식하고 실행한다. 잘 정의된 도구 정의가 있으면 명시적 지시 없이도 위임.

과도한 서브에이전트 사용 제어:
```
태스크가 병렬 실행 가능하거나 독립적 컨텍스트가 필요하거나 독립적 워크스트림인 경우에 서브에이전트를 사용하세요.
단순 태스크, 순차적 작업, 단일 파일 편집, 단계 간 컨텍스트 공유가 필요한 경우는 직접 처리하세요.
```

### 과잉엔지니어링 방지

Opus 4.6은 요청 이상의 기능을 추가하는 경향이 있다:

```xml
<avoid_overengineering>
명시적으로 요청되거나 명확히 필요한 변경만 하세요.
- 범위: 요청 외 기능 추가, 리팩토링, "개선" 금지
- 문서: 변경하지 않은 코드에 docstring/주석 추가 금지
- 방어적 코딩: 발생 불가능한 시나리오의 오류 처리 추가 금지
- 추상화: 일회성 작업의 헬퍼/유틸리티 생성 금지
</avoid_overengineering>
```

---

## 6. 장기 컨텍스트 프롬프팅 (20K+ 토큰)

- **긴 데이터를 상단에 배치**: 긴 문서/입력을 쿼리, 지시, 예시 위에 배치. 쿼리를 끝에 두면 성능 30%까지 향상.
- **XML 태그로 문서 구조화**:
  ```xml
  <documents>
    <document index="1">
      <source>characters.md</source>
      <document_content>{{CHARACTER_DATA}}</document_content>
    </document>
    <document index="2">
      <source>episode-outline.md</source>
      <document_content>{{OUTLINE_DATA}}</document_content>
    </document>
  </documents>
  분석하고 EP-05 초고를 작성하세요.
  ```
- **Quote 기반 응답**: 문서에서 관련 인용구를 먼저 추출하게 지시 → 노이즈 감소

---

## 7. 모델별 권장 설정 요약

| 모델 | 용도 | thinking | effort | max_tokens |
|---|---|---|---|---|
| Opus 4.6 | 장기 복잡 태스크, 에이전트 오케스트레이션 | adaptive | high/max | 64000 |
| Sonnet 4.6 | 표준 생성, 코딩, 대화 | adaptive 또는 enabled | medium | 16384 |
| Sonnet 4.6 (비용 우선) | 대량 처리, 빠른 응답 | disabled | low | 8192 |
| Haiku 4.5 | 간단한 분류, 요약 | - | - | 4096 |

---

## 우리 파이프라인 적용 포인트

| 파이프라인 단계 | 모델 | 설정 | 핵심 프롬프트 전략 |
|---|---|---|---|
| 장르 리서치 | Sonnet 4.6 | effort: medium | ReAct + 명시적 검색 지시 |
| 스토리 구조 | Opus 4.6 | effort: high, adaptive | CoT + XML 구조화 + 역할 부여 |
| 아웃라인 생성 | Opus 4.6 | effort: high, adaptive | 장기 컨텍스트 배치 + Few-Shot |
| 플롯 설계 | Opus 4.6 | effort: max, adaptive | 병렬 도구 호출 + 상태 추적 |
| 초고 집필 | Sonnet 4.6 | effort: medium | 포맷 명시 + 과잉엔지니어링 방지 |
| 문체 리뷰 | Sonnet 4.6 | effort: low | 구체적 평가 기준 명시 |
| 검증 | Opus 4.6 | effort: high | 자기 검증 루프 + Python 도구 |

---

## 추가 참고 자료

- [Claude Prompting Best Practices](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Extended Thinking](https://platform.claude.com/docs/en/docs/build-with-claude/extended-thinking)
- [Adaptive Thinking](https://platform.claude.com/docs/en/docs/build-with-claude/adaptive-thinking)
- [Structured Outputs](https://platform.claude.com/docs/en/docs/build-with-claude/structured-outputs)
- [Claude Code Overview](https://code.claude.com/docs)
