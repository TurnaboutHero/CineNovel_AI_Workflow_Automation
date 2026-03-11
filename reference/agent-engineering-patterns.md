# 멀티에이전트 시스템 설계 패턴 가이드

> 최종 업데이트: 2026-03 | 출처:
> - https://www.infoq.com/news/2026/01/multi-agent-design-patterns/ (Google 8가지 패턴)
> - https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system (Google Cloud)
> - https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/ (Google ADK)
> - https://code.claude.com/docs (Claude Code Agent SDK)
> - https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns (Azure)

## 핵심 요약

2025~2026년 멀티에이전트 시스템은 주요 패턴 8~12가지로 표준화되었다. Sequential Pipeline, Fan-Out/Gather, Coordinator/Dispatcher, Generator-Critic, Iterative Refinement, Human-in-the-Loop, Hierarchical Decomposition, Swarm 패턴이 핵심이다. 선택 기준은 태스크 복잡도, 병렬성, 가역성, 비용이며, 대부분의 실제 시스템은 여러 패턴을 조합한다.

---

## 1. Sequential Pipeline (순차 파이프라인)

**설명**: 에이전트들이 조립 라인처럼 배열되어 각 에이전트의 출력이 다음 에이전트의 입력이 되는 패턴.

**특성**:
- 선형, 결정론적, 디버깅 용이
- 데이터가 어디서 왔는지 항상 명확
- AI 모델 오케스트레이션 없이 미리 정해진 순서로 실행

**구조**:
```
[Agent A] → output_A → [Agent B] → output_B → [Agent C] → final_result
```

**장점**: 낮은 지연시간, 낮은 비용, 추적 가능성 높음
**단점**: 유연성 없음, 불필요한 단계 건너뛰기 불가, 동적 조건 적응 불가

**적용 시나리오**:
- 구조가 고정된 데이터 처리 파이프라인 (추출→정제→저장)
- 단계별 검증이 필요한 문서 생성
- 우리 파이프라인의 프리프로덕션 (장르→구조→아웃라인→플롯→검증)

**구현 패턴**:
```python
class SequentialPipeline:
    def __init__(self, agents: list):
        self.agents = agents

    def run(self, initial_input: str) -> str:
        result = initial_input
        for agent in self.agents:
            result = agent.run(result)
        return result

# 프리프로덕션 파이프라인
pipeline = SequentialPipeline([
    GenreResearcher(),    # Stage 1
    StoryArchitect(),     # Stage 2
    OutlineGenerator(),   # Stage 3
    PlotDesigner(),       # Stage 4
    OutlineReviewer(),    # Stage 5
])
```

---

## 2. Fan-Out / Gather (병렬 팬아웃/수집)

**설명**: 하나의 입력을 여러 전문 에이전트에게 동시에 분배하고 결과를 합성하는 패턴.

**특성**:
- 여러 에이전트가 동시에 독립적으로 작동
- 합성 에이전트(Synthesizer)가 결과를 통합
- AI 모델 오케스트레이션 없이 병렬 워크플로 에이전트로 관리

**구조**:
```
               → [Agent A] → result_A ─┐
input → [Dispatcher]                    → [Synthesizer] → final
               → [Agent B] → result_B ─┘
               → [Agent C] → result_C ─┘
```

**장점**: 전체 지연시간 감소 (병렬 실행)
**단점**: 즉각적 리소스 사용 증가, 토큰 소비 증가, 합성 복잡성

**적용 시나리오**:
- 여러 관점에서 동시 분석 (감정분석 + 키워드추출 + 카테고리 분류 + 긴급도 탐지)
- PR 리뷰 (스타일 + 보안 + 성능을 동시에 검토)
- 우리 파이프라인의 Stage 3/4 병렬 실행 (문체 리뷰 + 일관성 검증)

**구현 패턴**:
```python
import asyncio

async def fan_out_gather(input_text: str) -> dict:
    # 병렬 실행
    results = await asyncio.gather(
        style_reviewer.run(input_text),
        consistency_checker.run(input_text),
        image_prompt_generator.run(input_text),
    )
    return synthesize(results)
```

---

## 3. Coordinator / Dispatcher (조율자/디스패처)

**설명**: 중앙 에이전트가 요청을 분석하고 적합한 전문 에이전트로 라우팅하는 패턴.

**특성**:
- 중앙 에이전트가 AI 모델을 사용해 동적 라우팅
- 조율자가 전체 워크플로를 오케스트레이션
- Fan-Out과 달리 모든 에이전트를 동시 실행하지 않음

**구조**:
```
                    → [Agent A] (if condition_A)
input → [Coordinator]
                    → [Agent B] (if condition_B)
                    → [Agent C] (if condition_C)
```

**장점**: 유연한 라우팅, 적응형 태스크 분배
**단점**: 조율자의 AI 호출 추가 비용, 오케스트레이션 복잡성

**적용 시나리오**:
- 다양한 요청 유형을 처리하는 고객 서비스
- 태스크 유형에 따라 다른 에이전트 활성화
- 우리 파이프라인: OMC 오케스트레이터가 단계별로 적합한 에이전트 라우팅

---

## 4. Generator-Critic (생성자-비평자)

**설명**: 하나의 에이전트가 콘텐츠를 생성하고, 다른 에이전트가 사전 정의된 기준으로 검증하며 승인 또는 수정 요청.

**특성**:
- 생성자: 출력 생성
- 비평자: 기준 대비 평가, 승인 또는 피드백 반환
- 순차 워크플로이나 반복 가능

**구조**:
```
[Generator] → draft → [Critic]
                          ↓ if approved
                       final_output
                          ↓ if rejected
                    feedback → [Generator] (retry)
```

**장점**: 신뢰성 높은 품질 보증
**단점**: 지연시간 및 비용 직접 증가

**적용 시나리오**:
- 코드 생성 + 보안 감사
- 콘텐츠 생성 + 엄격한 기준 검증
- 우리 파이프라인: 초고 집필 → 검증 → FAIL 시 수정 재실행 (최대 2회)

---

## 5. Iterative Refinement (반복 정제)

**설명**: Generator-Critic의 확장. 여러 에이전트가 루프 안에서 품질 임계값에 도달할 때까지 점진적으로 출력을 개선.

**특성**:
- 수정 사항이 세션 상태에 각 반복마다 저장
- 종료 조건(품질 임계값)에 도달하거나 최대 반복 횟수 초과 시 종료

**구조**:
```
[Generator] → draft_v1 → [Critic] → feedback
     ↑                                  ↓
     └──────────── (if not done) ───────┘
                                        ↓ (if done)
                                  final_output
```

**장점**: 복잡한 결과물의 점진적 품질 향상
**단점**: 반복마다 지연시간/비용 증가, 무한 루프 위험 (종료 조건 설계 중요)

**적용 시나리오**:
- 블로그 작성, 코드 개발, 상세 계획
- 여러 개선 사이클이 필요한 장문 문서
- 우리 파이프라인: 아웃라인 검증 실패 → 수정 재실행 루프 (최대 2회)

---

## 6. Hierarchical Decomposition (계층적 분해)

**설명**: 최상위 에이전트가 복잡한 목표를 하위 태스크로 분해하고 전문 에이전트에 위임. 재귀적으로 반복 가능.

**특성**:
- 루트 에이전트: 고수준 태스크 분해 및 위임
- 하위 에이전트: 전문화된 세부 태스크 처리
- 여러 계층에 걸쳐 반복

**구조**:
```
[Root Agent]
├── [Sub-Agent A]
│   ├── [Sub-Sub-Agent A1]
│   └── [Sub-Sub-Agent A2]
└── [Sub-Agent B]
    └── [Sub-Sub-Agent B1]
```

**장점**: 매우 복잡한 문제 처리 가능
**단점**: 높은 아키텍처 복잡성, 모델 호출 대폭 증가, 지연시간/비용 증가

**적용 시나리오**:
- 복잡한 리서치 프로젝트
- 모호하고 개방형 복잡 문제
- 우리 파이프라인: OMC → 프리프로덕션/프로덕션 → 개별 단계 에이전트

---

## 7. Human-in-the-Loop (휴먼 인더루프)

**설명**: 에이전트가 실행을 일시 중지하고 인간 검토자의 승인을 기다린 후 계속하는 패턴.

**특성**:
- 에이전트가 미리 정의된 체크포인트에 도달하면 실행 일시 중지
- 외부 시스템을 통해 인간에게 알림
- 승인 후 계속 실행

**장점**: 인간 감독을 통한 안전성과 신뢰성
**단점**: 외부 상호작용 시스템 구축/유지 필요

**적용 시나리오**:
- 금융 거래 실행, 프로덕션 코드 배포
- 민감한 데이터 작업, 고위험 의사결정
- 우리 파이프라인에서: 새 프로젝트 첫 아웃라인 승인, 배치 생성 전 인간 확인

---

## 8. Swarm (스웜)

**설명**: 여러 전문 에이전트가 협업적 전체-대-전체 통신으로 반복적으로 솔루션을 정제하는 패턴.

**특성**:
- 디스패처가 요청 라우팅
- 에이전트들이 자유롭게 소통하고 발견사항 공유
- 어느 에이전트나 태스크를 다른 에이전트에게 넘길 수 있음

**장점**: "예외적으로 높은 품질과 창의적 솔루션 가능"
**단점**: "구현하기 가장 복잡하고 비용이 많은 멀티에이전트 패턴"

**적용 시나리오**:
- 엔지니어링/마케팅/재무 관점이 모두 필요한 제품 설계
- 창의적 문제 해결 (토론이 도움이 되는 경우)

---

## 9. ReAct Pattern (추론-행동)

**설명**: 에이전트가 완료까지 사고-행동-관찰 사이클을 반복하는 단일 에이전트 패턴.

**구조**:
```
[Thought] → [Action: tool/api call] → [Observation: result]
     ↑                                          ↓
     └──────── (if not done) ───────────────────┘
                                                ↓ (exit condition)
                                          final_answer
```

**특성**:
- 단일 에이전트이므로 멀티에이전트보다 단순할 수 있음
- 높은 지연시간 (사이클마다 추론)
- 모델 추론 품질에 크게 의존

**적용 시나리오**:
- 연속 계획이 필요한 복잡한 동적 태스크
- 로봇 경로 생성, 적응형 문제 해결

---

## 10. Loop Pattern (루프)

**설명**: 특정 종료 조건이 충족될 때까지 전문 에이전트를 반복 실행하는 패턴.

**구조**:
```
[Loop Agent] → [Specialized Agent] → check_condition
     ↑                                      ↓ if not met
     └──────────────────────────────────────┘
                                            ↓ if met
                                      final_result
```

**위험**: 종료 조건이 잘못 정의되면 무한 루프. 반드시 최대 반복 횟수 설정 필요.

**적용**: 반복 정제, 자기 수정, 품질 기준 기반 생성.

---

## 11. Custom Logic Pattern (커스텀 로직)

**설명**: 코드 기반 조건 로직으로 표준 패턴을 넘어서는 복잡한 워크플로를 구현하는 패턴.

**특성**:
- 특정 비즈니스 요구사항에 맞는 브랜칭 로직
- 미리 정의된 규칙과 모델 추론 혼합
- 최대 유연성, 최대 개발 복잡성

**적용**: 고유한 요구사항, 세밀한 프로세스 제어.

---

## 12. 패턴 선택 기준

| 기준 | 권장 패턴 |
|---|---|
| 고정된 선형 단계 | Sequential Pipeline |
| 독립적 병렬 분석 | Fan-Out/Gather |
| 동적 라우팅 필요 | Coordinator/Dispatcher |
| 품질 보증, 단순 검증 | Generator-Critic |
| 점진적 품질 개선 | Iterative Refinement |
| 매우 복잡한 문제 분해 | Hierarchical Decomposition |
| 고위험 불가역적 행동 | Human-in-the-Loop |
| 창의적 다관점 해결 | Swarm |
| 표준 패턴 부적합 | Custom Logic |

### 비용-복잡성 스펙트럼

```
낮은 비용/복잡성 ←────────────────────────────→ 높은 비용/복잡성
Sequential → Fan-Out → Coordinator → Generator-Critic → Iterative → Hierarchical → Swarm
```

---

## 13. 실제 시스템 패턴 조합

대부분의 프로덕션 시스템은 여러 패턴을 조합한다:

**예시: 코드 리뷰 시스템**
```
Coordinator (요청 분류)
├── Fan-Out (스타일+보안+성능 병렬 리뷰)
├── Generator-Critic (수정 제안 생성+검증)
└── Human-in-the-Loop (중요 변경사항 최종 승인)
```

**예시: 우리 파이프라인 패턴 분석**
```
OMC 오케스트레이터 (Coordinator)
├── [프리프로덕션] Sequential Pipeline (5단계)
│   └── Stage 5 실패 시 Loop (최대 2회)
└── [프로덕션] 혼합 패턴
    ├── Stage 1-2: Sequential
    ├── Stage 3-4: Fan-Out (병렬)
    ├── Stage 5: Generator-Critic (FAIL 시만)
    ├── Stage 6: Loop with Validator (최대 2회)
    └── Stage 7-8: Sequential (후처리)
```

---

## 14. Claude Code 에이전트 패턴

Claude Code의 Agent SDK 및 서브에이전트 기능:

**서브에이전트 스포닝**:
```python
# Claude Code: 병렬 서브에이전트
# 리드 에이전트가 조율하고, 서브태스크를 여러 에이전트에 할당
```

**CLAUDE.md 기반 커스터마이징**:
- 팀별 워크플로 패키징 (커스텀 커맨드 `/review-pr`, `/deploy-staging`)
- 세션 간 아키텍처 결정 영속화

**MCP(Model Context Protocol) 통합**:
- Google Drive, Jira, Slack, 커스텀 API와 연동
- 에이전트가 외부 도메인별 도구 사용 가능

---

## 15. 2025-2026 멀티에이전트 트렌드

- Gartner: 2024 Q1~2025 Q2 사이 멀티에이전트 시스템 문의 1,445% 급증
- 2025: AI 에이전트의 해 → 2026: 멀티에이전트 시스템의 해
- 인프라 성숙: 조율된 에이전트를 위한 인프라가 드디어 성숙 단계 진입
- 표준 패턴 7개 (ReAct, Reflection, Tool Use, Planning, Multi-Agent Collaboration, Sequential Workflows, Human-in-the-Loop)가 에이전트 개발의 아키텍처 어휘로 자리잡음

---

## 우리 파이프라인 적용 포인트

### 현재 아키텍처 패턴 매핑

| 파이프라인 구성요소 | 적용 패턴 | 최적화 기회 |
|---|---|---|
| OMC 오케스트레이터 | Coordinator | 단계 실패 시 동적 재라우팅 |
| 프리프로덕션 5단계 | Sequential Pipeline | 현재 최적 (고정 순서) |
| Stage 5 실패 루프 | Iterative Refinement + Loop | 최대 2회 → 명시적 종료 조건 |
| Stage 3+4 병렬 | Fan-Out/Gather | 현재 `ask_gemini + ask_codex` 병렬 실행 |
| Stage 5 수정 | Generator-Critic | FAIL 시만 활성화 (비용 최적) |
| Stage 6 검증 | Loop with Validator | Python 자동 검증 후 루프 |

### 개선 권장: Hierarchical로 전환 검토

현재 OMC가 단순 Coordinator로 동작하지만, 복잡한 배치 생성(EP-01~EP-42)에서는 Hierarchical Decomposition으로 전환해 볼 수 있다:

```
배치 오케스트레이터 (Root)
├── 에피소드 그룹 A (EP-01~EP-14) 에이전트
│   └── 개별 에피소드 에이전트들
├── 에피소드 그룹 B (EP-15~EP-28) 에이전트
└── 에피소드 그룹 C (EP-29~EP-42) 에이전트
```

---

## 추가 참고 자료

- [Google's Eight Multi-Agent Design Patterns - InfoQ](https://www.infoq.com/news/2026/01/multi-agent-design-patterns/)
- [Google Cloud - Choose Design Pattern for Agentic AI](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system)
- [Google ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Claude Code Sub-Agents](https://code.claude.com/docs)
- [Azure AI Agent Orchestration Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [Anthropic Agent SDK](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Designing Effective Multi-Agent Architectures - O'Reilly](https://www.oreilly.com/radar/designing-effective-multi-agent-architectures/)
