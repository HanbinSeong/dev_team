# AI Development Team Agent — 로드맵

**프로젝트 개요**
비동기 자율 AI 에이전트들로 구성된 소프트웨어 개발 파이프라인.
요구사항 분석 → 설계 → 코드 작성(Span Edit) → 테스트 → 리뷰 → 자가 치유까지 **전 과정을 자동화**하고,
개발자는 "AI를 오케스트레이션"하는 역할에 집중할 수 있는 환경을 목표로 합니다.

**현재 브랜치 상태 (dynamic-routing, 2026.03.28)**
- `workflow.yaml` 선언 완료, 그러나 실제 `build_graph()`에서 파싱되지 않는 미완성 상태
- `.ai/` 디렉토리 + `utils/prompt_loader.py` + `state.py` + `routers.py` 존재
- `utils/sandbox.py` Docker 기반 QA 실행 구현 완료 (단, network_mode="none" 비활성화 상태)
- LangSmith 평가 하네스(`evaluate.py`) 초안 작성 완료
- 핵심 버그: `main.py` 로그 블록에서 `node_name == "developer"` 오타 존재 (실제 노드명은 `"dev"`)

---

## 전체 설계 원칙

- **Orchestration**: LangGraph (StateGraph + conditional edge + checkpoint + subgraph)
- **Context & Skill Layer**: Harness Engineering (AGENTS.md + 역할별 SKILL.md + create_agent factory)
- **Core Philosophy**: Prompt Engineering → Harness Engineering으로 진화 (토큰 60~75% 절감, 선언형 유지보수)
- **Phase 진입 원칙**: 각 Phase의 **모든 Success Criteria가 실제 코드로 검증**되어야 다음 Phase로 진입한다. 설계 문서 완성은 진입 조건이 아니며, 동작하는 코드가 기준이다.

---

## Phase 간 의존성 맵

아래 의존성을 이해하는 것이 로드맵 전체를 파악하는 핵심입니다.
각 Phase는 독립적으로 보이지만, 실제로는 아래와 같은 선후 관계를 가집니다.

```
[Phase 0] YAML → LangGraph 동적 조립
    └─▶ [Phase 1] Triage 노드 (의도 분류 + 동적 진입점 선택)
            └─▶ [Phase 2] Harness Engineering (Skill on-demand 로딩)
                    ├─▶ [Phase 3-A] Span-Edit Skill (Dev 에이전트 정밀 수정)
                    └─▶ [Phase 3-B] Context Retrieval Skill (RAG, PM 에이전트)
                            └─▶ [Phase 4] 비동기 처리 + UI + HITL
                                    └─▶ [Phase 5] 멀티스택 + 멀티레포 확장
```

**핵심 의존성 주의사항**:
Phase 1의 "confidence < 0.7 시 HITL 전환" 기능은 Phase 4의 인프라를 필요로 합니다.
따라서 Phase 1에서는 HITL을 CLI 인터럽트(`input()`)로 임시 구현하고, Phase 4에서 UI 기반으로 교체하는 방식으로 의존성 사이클을 끊어야 합니다.
Span-Edit(Phase 3-A)은 코드베이스 전체 구조 파악 없이는 정밀 수정이 불가능하므로, Context Retrieval(Phase 3-B)과 동시에 설계되어야 합니다.

---

## [Phase 0] 기반 완성 및 버그 수정 (재정의)

> **상태**: 부분 완료 — "YAML 기반 동적 그래프 조립"이 코드에 반영되지 않아 완료로 볼 수 없음.
> **목표**: 현재 코드베이스의 알려진 버그를 수정하고, `workflow.yaml`이 실제로 그래프 조립을 제어하도록 구현하여 Phase 0를 진정한 의미에서 닫는다.

### 작업 1: 알려진 버그 수정

`main.py`의 로그 기록 블록에서 `node_name == "developer"` 조건을 `node_name == "dev"`로 수정합니다. 이 버그로 인해 현재 Dev 에이전트의 실행 결과가 `workflow_log.txt`에 전혀 기록되지 않는 상태입니다.

`sandbox.py`의 `network_mode="none"` 주석 처리 문제를 해결합니다. 현재는 매번 컨테이너 시작 시 `pip install pytest pytest-mock`을 실행하는데, `network_mode="none"` 활성화 시 pip이 동작하지 않습니다. 해결책은 `pytest`와 `pytest-mock`이 사전 설치된 커스텀 Docker 이미지(`Dockerfile.qa`)를 프로젝트 루트에 작성하고, `sandbox.py`에서 해당 이미지를 참조하도록 수정하는 것입니다. 이로써 격리 수준과 실행 속도를 동시에 높입니다.

### 작업 2: `utils/graph_builder.py` 신설 — YAML → LangGraph 동적 조립

이것이 Phase 0의 핵심 미완성 항목입니다. `workflow.yaml`을 파싱하여 LangGraph `StateGraph`를 동적으로 조립하는 `build_graph_from_yaml(yaml_path)` 함수를 `utils/graph_builder.py`에 구현합니다.

구현 시 다음 사항을 처리해야 합니다. `transitions.type: "direct"`인 노드는 `add_edge`로 연결하고, `transitions.type: "conditional"`인 노드는 `condition_field`를 읽어서 `add_conditional_edges`로 연결합니다. `on_true: "__end__"`는 LangGraph의 `END` 상수로 매핑합니다. `start_node` 필드를 읽어 `set_entry_point`를 자동으로 설정합니다. YAML의 `llm` 섹션(provider, model, temperature)을 읽어 각 노드의 LLM 설정을 동적으로 주입하는 구조를 설계합니다. 단, 현재 단계에서 실제 LLM 주입은 각 에이전트 내부에서 직접 읽는 방식으로 우선 구현하고, Phase 2의 factory 패턴 도입 시 완전히 분리합니다.

이후 `main.py`의 `build_graph()` 함수가 하드코딩된 노드 연결 대신 `build_graph_from_yaml(".ai/workflow.yaml")`을 호출하도록 교체합니다.

### 작업 3: Phase 0 완료 검증

`tests/test_graph_builder.py`를 작성하여 `build_graph_from_yaml()`이 YAML 파일을 올바르게 해석하는지 단위 테스트합니다. 검증 항목은 노드 목록이 YAML의 `agents` 키와 일치하는지, 엣지 연결이 `transitions` 정의와 일치하는지, 잘못된 YAML이 입력될 때 명확한 오류 메시지를 반환하는지입니다.

### 추가 파일 및 디렉토리 구조

```
(신설)
utils/graph_builder.py        # YAML → LangGraph 동적 조립
Dockerfile.qa                 # pytest 사전 설치된 QA 전용 이미지
tests/
  test_graph_builder.py       # graph_builder 단위 테스트

(수정)
main.py                       # build_graph() → build_graph_from_yaml() 교체, 로그 버그 수정
utils/sandbox.py              # 커스텀 이미지 참조, network_mode="none" 활성화
```

### Success Criteria

`python main.py` 실행 시 `workflow.yaml`만 수정해도 그래프 흐름이 바뀌는 것이 동작으로 확인되어야 합니다. `test_graph_builder.py`의 모든 테스트가 통과되어야 합니다. Docker sandbox가 `network_mode="none"` 상태에서도 pytest를 정상 실행해야 합니다.

---

## [Phase 1] 동적 라우팅 및 Triage 체계 확립

> **진입 조건**: Phase 0의 모든 Success Criteria 달성.
> **목표**: 사용자의 지시 의도를 분류하여, 단순 수정 요청이 PM부터 다시 시작하는 비효율을 제거한다.
> **예상 기간**: 4~6일

### 배경 및 문제 인식

현재 파이프라인은 입력의 종류와 무관하게 항상 `pm → dev → qa → supervisor` 전체 사이클을 실행합니다. "A 함수를 B 라이브러리로 교체해줘"라는 수정 지시에도 PM이 전체 설계서를 새로 작성하는 낭비가 발생합니다. Triage 노드는 이를 해결하는 의도 분류기로, 워크플로우의 새로운 진입점이 됩니다.

### 작업 1: `state.py` 확장

`TeamState`에 아래 두 필드를 추가합니다.

`triage_destination`은 Triage 노드가 결정한 다음 진입 노드 이름을 담는 `str` 타입 필드입니다. 가능한 값은 `"pm"`, `"dev"`, `"supervisor"` 등입니다. `confidence_score`는 Triage 분류 결과의 신뢰도를 나타내는 `float` 타입 필드로, 0.0에서 1.0 사이의 값을 가집니다. 이 값이 임계치(0.7) 미만일 때 사람의 개입을 요청하는 분기 조건으로 사용됩니다.

### 작업 2: `agents/triage.py` 구현

Triage 에이전트가 분류해야 하는 의도 카테고리는 여섯 가지입니다. `new_feature`는 신규 기능 구현으로 `pm`에서 시작합니다. `code_fix`는 기존 코드의 특정 수정으로 `dev`에서 시작합니다. `bugfix`는 QA 리포트 기반 버그 수정으로 `dev`에서 시작합니다. `refactor`는 구조 개선으로 `dev`에서 시작합니다. `documentation`은 문서 작성으로 `pm`에서 시작합니다. `review_only`는 코드 검토만 요청하는 경우로 `supervisor`에서 시작합니다.

Pydantic 모델로 구조화된 출력을 받습니다. 반환값은 `intent` (위 카테고리 중 하나), `triage_destination` (다음 노드 이름), `confidence_score` (float), `reasoning` (분류 근거 한 줄 요약)을 포함합니다.

### 작업 3: `workflow.yaml` 업데이트

`start_node`를 `"triage"`로 변경합니다. `triage` 에이전트 항목을 추가하고, 전환 타입을 `"conditional"`로 설정하되, `condition_field`를 `"triage_destination"`으로 지정하고, `on_values` (혹은 `on_map`) 방식으로 `new_feature/documentation → pm`, `code_fix/bugfix/refactor → dev`, `review_only → supervisor`를 매핑합니다. `graph_builder.py`가 이 새로운 다중 조건 전환 방식을 파싱할 수 있도록 함께 업데이트합니다.

### 작업 4: 저신뢰도 처리 — CLI 기반 HITL (임시)

`confidence_score < 0.7`일 때 현재 단계에서는 CLI `input()`으로 사용자에게 확인을 요청하는 방식으로 구현합니다. "Triage 에이전트가 의도를 확신하지 못합니다. [code_fix / new_feature] 중 선택하세요:" 형태의 인터럽트입니다. 이 임시 구현은 Phase 4에서 UI 기반 HITL로 교체됩니다. 코드 내에 `# TODO(Phase4): Replace with UI-based HITL` 주석을 명시합니다.

### 작업 5: `tests/test_triage.py` 작성 및 LangSmith 평가

핵심 의도 카테고리별 대표 입력 샘플 10개 이상에 대해 분류 정확도를 측정합니다. LangSmith 데이터셋에 `triage_accuracy` 평가 항목을 추가하고, 목표 점수 4.5/5.0 이상을 확인합니다.

### 추가 파일 및 디렉토리 구조

```
(신설)
agents/triage.py              # Triage 에이전트 구현
tests/test_triage.py          # Triage 단위/통합 테스트

(수정)
state.py                      # triage_destination, confidence_score 필드 추가
.ai/workflow.yaml             # start_node 변경, triage 에이전트 항목 추가
utils/graph_builder.py        # 다중 조건 전환 파싱 지원
.ai/roles/triage.md           # Triage 에이전트 시스템 프롬프트
```

### Success Criteria

사용자 입력 "A 함수를 B 라이브러리로 교체해줘"가 `code_fix`로 분류되어 `dev`에서 직접 시작되어야 합니다. LangSmith Triage 정확도 평가 4.5/5.0 이상을 달성해야 합니다. `confidence_score < 0.7`인 경우 CLI 인터럽트가 발생해야 합니다.

---

## [Phase 2] Harness Engineering + 에이전트 리팩토링

> **진입 조건**: Phase 1의 모든 Success Criteria 달성.
> **목표**: 프롬프트를 하드코딩하는 방식에서 벗어나, 에이전트가 필요한 Skill을 동적으로 조합하는 Harness 구조로 전환하여 토큰 사용량을 60% 이상 절감한다.
> **예상 기간**: 6~8일

### 배경 및 핵심 개념

현재 `utils/prompt_loader.py`는 마크다운 파일의 `{변수명}`을 치환하는 단순 텍플릿 엔진입니다. 모든 에이전트가 매 호출마다 전체 역할 프롬프트를 받습니다. Harness Engineering이 지향하는 것은, 에이전트가 **지금 이 작업에 필요한 Skill 단위의 프롬프트만 조합**하는 구조입니다.

예를 들어 Dev 에이전트가 Python 신규 기능을 구현할 때는 `skills/coder/SKILL.md`와 `skills/conventions/python.md`만 로드하지만, 기존 코드를 수정할 때는 여기에 `skills/span-edit/SKILL.md`가 추가됩니다. 이 "필요한 것만 로드"하는 원칙이 토큰 절감의 핵심입니다.

또한 이 Phase에서 README의 `create_agent` vs LangGraph 딜레마에 대한 설계 답을 확정합니다. 결론은, 에이전트 내부의 ReAct 루프를 허용하되 **행동 반경을 YAML로 선언적으로 제한**하는 방향입니다. `factory.py`의 `create_agent()`는 LangGraph를 대체하는 것이 아니라, **각 노드 함수를 조립하는 팩토리**로서 동작합니다.

### 작업 1: `skills/` 디렉토리 신설 및 SKILL.md 작성

프로젝트 루트에 `skills/` 디렉토리를 만들고, 각 역할에 특화된 Skill 단위로 서브폴더를 구성합니다.

`skills/pm/SKILL.md`에는 PM 역할의 핵심 행동 지침, 산출물(실행 계획서) 형식 명세, 기존 코드베이스가 있을 때와 없을 때의 분기 처리 방식을 기술합니다. `skills/coder/SKILL.md`에는 코드 작성 시 지켜야 할 원칙, `DeveloperOutput` Pydantic 스키마 명세, 파일 경로 규칙을 기술합니다. `skills/span-edit/SKILL.md`에는 전체 파일 재작성 대신 변경 부분만 지정하는 Span-Edit 형식 명세를 기술합니다. 이 Skill은 Phase 3에서 실제 구현되지만 명세 자체는 이 단계에서 확정합니다. `skills/reviewer/SKILL.md`에는 Supervisor 검토 기준(4가지 Review Criteria)을 기술합니다. `skills/self-healing/SKILL.md`에는 QA 실패 시 에러 로그 분석 및 수정 전략을 기술합니다.

각 SKILL.md는 YAML frontmatter(`name`, `version`, `token_estimate`)를 포함하여 로더가 선택적으로 로드할 수 있도록 합니다.

### 작업 2: `AGENTS.md` 루트 파일 작성

프로젝트 루트에 `AGENTS.md`를 작성합니다. 이 파일은 전체 에이전트 팀의 역할 정의, Skill 디렉토리 구조, 각 노드가 어떤 Skill을 사용하는지의 매핑 테이블을 선언적으로 기술하는 마스터 문서입니다. 새 에이전트를 추가할 때 이 파일을 먼저 수정하는 것이 규칙입니다.

### 작업 3: `agents/harness_loader.py` 구현

기존 `utils/prompt_loader.py`를 대체하는 `HarnessLoader` 클래스를 구현합니다. `load_skills(role, skill_names: list[str])` 메서드는 지정된 Skill들의 SKILL.md를 읽어 하나의 시스템 프롬프트로 조립합니다. `get_token_estimate(skill_names)` 메서드는 각 Skill의 frontmatter에서 `token_estimate`를 읽어 전체 예상 토큰을 반환합니다. Skill 파일이 없거나 잘못된 경로가 들어올 때 명확한 오류를 발생시킵니다. 결과 프롬프트를 캐싱하여 동일한 Skill 조합을 재요청할 때 파일 I/O를 생략합니다.

### 작업 4: `agents/factory.py` 구현

`create_agent(role: str, skills: list[str], llm_config: dict)` 팩토리 함수를 구현합니다. 이 함수는 `HarnessLoader`로 시스템 프롬프트를 조립하고, `llm_config`에 따라 LLM 인스턴스를 생성하고, Pydantic 구조화 출력을 설정한 뒤 **호출 가능한 노드 함수**를 반환합니다. 반환된 함수는 `TeamState`를 받아 상태 업데이트 딕셔너리를 반환하는 LangGraph 노드 인터페이스를 따릅니다.

### 작업 5: 각 에이전트 노드를 thin wrapper로 리팩토링

`agents/pm.py`, `agents/dev.py`, `agents/qa.py`, `agents/supervisor.py`를 각각 10줄 이하의 thin wrapper로 줄입니다. 각 파일은 `factory.py`의 `create_agent()`를 호출하여 노드 함수를 생성하는 역할만 담당하고, 실제 비즈니스 로직은 SKILL.md와 factory에 위임합니다.

### 작업 6: 토큰 사용량 측정 및 검증

리팩토링 전후의 평균 토큰 사용량을 LangSmith로 측정합니다. 동일한 5개 입력 케이스에 대해 이전 방식과 Harness 방식의 토큰 비용을 비교하여 60% 이상 절감 목표를 검증합니다.

### 추가 파일 및 디렉토리 구조

```
(신설)
AGENTS.md                         # 마스터 에이전트 선언 문서
skills/
  pm/SKILL.md
  coder/SKILL.md
  span-edit/SKILL.md              # 명세만, 실제 구현은 Phase 3
  reviewer/SKILL.md
  self-healing/SKILL.md
agents/harness_loader.py          # Skill on-demand 로더
agents/factory.py                 # create_agent() 팩토리

(수정)
agents/pm.py                      # thin wrapper로 리팩토링
agents/dev.py                     # thin wrapper로 리팩토링
agents/qa.py                      # thin wrapper로 리팩토링
agents/supervisor.py              # thin wrapper로 리팩토링
utils/prompt_loader.py            # harness_loader로 대체(deprecated 처리)
```

### Success Criteria

`create_agent("coder", skills=["coder", "self-healing"])` 호출로 에이전트가 정상 생성되어야 합니다. 동일 Skill 조합 재요청 시 캐싱이 동작해야 합니다. LangSmith 측정 기준 토큰 사용량 60% 이상 절감이 수치로 확인되어야 합니다. 각 에이전트 파일이 10줄 이하의 thin wrapper여야 합니다.

---

## [Phase 3] 에이전트 도구화(Tooling) — Span-Edit 및 Context Retrieval

> **진입 조건**: Phase 2의 모든 Success Criteria 달성.
> **목표**: Dev 에이전트의 전체 파일 재작성을 Span-Edit으로 대체하고, PM 에이전트에 RAG 기반 컨텍스트 검색을 부여하여 기존 코드베이스(Brown-field) 대응 능력을 확보한다.
> **예상 기간**: 8~12일

### 배경 및 핵심 의존성

이 Phase의 두 작업(Span-Edit, Context Retrieval)은 서로 강하게 결합되어 있습니다. Span-Edit이 올바르게 동작하려면 Dev 에이전트가 수정 대상 파일의 전체 구조를 이해해야 하고, 이 이해를 제공하는 것이 Context Retrieval입니다. 따라서 두 Sub-task를 동시에 설계하고, Context Retrieval을 먼저 구현한 뒤 Span-Edit을 그 위에 올리는 순서로 진행합니다.

### 작업 1 (3-B): PM — Context Retrieval Skill 구현

`skills/context-retrieval/SKILL.md`를 작성합니다. `utils/context_retriever.py`를 구현합니다. 이 모듈은 `workspace_dir` 하위의 모든 소스 파일을 인덱싱하고, 관련도 높은 코드 청크를 검색하여 반환합니다. 초기 구현은 간단한 키워드 기반 검색으로 시작하고, 이후 벡터 임베딩(Phase 5)으로 업그레이드합니다. `TeamState`에 `context_chunks: list[str]` 필드를 추가하여 검색된 컨텍스트를 파이프라인 전반에 전달합니다. PM과 Dev 에이전트가 이 컨텍스트를 시스템 프롬프트에 포함하도록 `HarnessLoader`를 업데이트합니다.

### 작업 2 (3-A): Dev — Span-Edit Skill 구현

`utils/span_editor.py`를 구현합니다. 초기 구현은 LLM이 반환한 diff 포맷(`--- original +++ modified`) 혹은 `(start_line, end_line, new_content)` 형식의 지시를 파싱하여 파일에 적용하는 방식으로 시작합니다. 이후 tree-sitter 기반 AST 파싱으로 업그레이드하여 함수/클래스 단위의 정밀 수정을 지원합니다. `DeveloperOutput` Pydantic 모델을 확장하여 전체 파일 재작성(`full_rewrite`)과 Span-Edit(`span_edits`) 두 가지 모드를 지원하도록 합니다. 신규 파일 생성 시에는 `full_rewrite`, 기존 파일 수정 시에는 `span_edits`를 사용하는 것이 기본 전략입니다.

### 작업 3: GitHub API 연동

`utils/github_client.py`를 구현합니다. Supervisor 최종 승인 시 자동으로 feature 브랜치를 생성하고 PR을 생성하는 기능을 추가합니다. `workflow.yaml`에 `github_integration: true/false` 설정을 추가하여 선택적으로 활성화합니다.

### 작업 4: Supervisor의 Skill-aware Routing 강화

Supervisor가 반려 시 단순히 `dev`로 되돌리는 것이 아니라, 피드백의 성격에 따라 `pm` 또는 `dev`로 라우팅을 분기하도록 개선합니다. "요구사항 자체가 잘못됨" → `pm`, "구현 품질 문제" → `dev`로 구분하고, `review_feedback` 외에 `rejection_target: "pm" | "dev"` 필드를 `TeamState`에 추가합니다.

### 추가 파일 및 디렉토리 구조

```
(신설)
skills/context-retrieval/SKILL.md
utils/context_retriever.py         # 코드베이스 인덱싱 및 검색
utils/span_editor.py               # Span-Edit diff 적용 엔진
utils/github_client.py             # GitHub PR 자동 생성

(수정)
state.py                           # context_chunks, rejection_target 필드 추가
agents/factory.py                  # context_retriever 연동
routers.py                         # rejection_target 기반 분기 추가
.ai/workflow.yaml                  # github_integration 설정 추가
```

### Success Criteria

Span-Edit만으로 단일 함수 수정 성공률 90% 이상(10개 케이스 기준)을 달성해야 합니다. Brown-field 시나리오(기존 파일이 있는 workspace)에서 PM이 올바른 컨텍스트를 참조하여 설계서를 작성해야 합니다. GitHub PR이 Supervisor 승인 시 자동 생성되어야 합니다(연동 활성화 시).

---

## [Phase 4] 비동기 처리, UI, HITL 통합

> **진입 조건**: Phase 3의 모든 Success Criteria 달성.
> **목표**: CLI 기반 단일 사용자 인터페이스에서 벗어나 다중 사용자 요청을 비동기 처리하고, Phase 1에서 임시 구현된 CLI HITL을 UI 기반으로 교체한다.
> **예상 기간**: 8~12일

### 작업 1: Streamlit 대시보드 구축

워크플로우 진행 상황을 실시간으로 시각화하는 Streamlit 앱을 구현합니다. 각 에이전트 노드의 상태(대기/실행 중/완료/실패)를 표시하고, `workflow_log.txt` 대신 UI 내에서 단계별 로그를 확인할 수 있도록 합니다. `astream_events`를 활용하여 LangGraph의 이벤트 스트림을 Streamlit에 실시간으로 연결합니다.

### 작업 2: Celery + Redis 기반 비동기 태스크 큐

다중 사용자 요청을 동시에 처리하기 위해 Celery 워커와 Redis 브로커를 도입합니다. `main.py`의 동기 실행 루프를 Celery 태스크로 래핑합니다. 태스크 상태 추적(PENDING/STARTED/SUCCESS/FAILURE)을 Streamlit 대시보드에 연동합니다.

### 작업 3: LangGraph Checkpoint — PostgreSQL 기반 영속성

`langgraph.checkpoint.postgres`를 적용하여 각 그래프 실행의 상태를 PostgreSQL에 저장합니다. 이를 통해 실행 중 실패한 워크플로우를 정확한 단계부터 재시작할 수 있게 됩니다. `workflow_log.txt` 파일 기반 로깅을 DB 기반으로 전환합니다.

### 작업 4: UI 기반 HITL 구현 (Phase 1 임시 구현 교체)

Phase 1에서 `# TODO(Phase4)`로 표시해둔 CLI HITL 지점을 Streamlit UI의 승인 버튼으로 교체합니다. `confidence_score < 0.7`인 경우 대시보드에 알림이 표시되고, 사용자가 올바른 의도를 선택하면 워크플로우가 재개됩니다. LangGraph의 `interrupt_before` 기능을 활용합니다.

### 추가 파일 및 디렉토리 구조

```
(신설)
app/
  streamlit_app.py               # 메인 Streamlit 대시보드
  tasks.py                       # Celery 태스크 정의
docker-compose.yml               # Redis + PostgreSQL + Celery Worker 환경
```

### Success Criteria

5개의 동시 요청이 각각 격리된 워크스페이스에서 병렬 처리되어야 합니다. 실행 중 강제 종료 후 재시작 시 마지막 완료 노드 이후부터 이어서 실행되어야 합니다. UI에서 HITL 승인이 동작해야 합니다.

---

## [Phase 5] 확장성 및 멀티-스택 지원 (Future)

> **진입 조건**: Phase 4의 모든 Success Criteria 달성.
> **목표**: Python 단일 스택에서 벗어나 다양한 언어와 프레임워크를 지원하고, 장기 메모리와 멀티-레포 환경으로 확장한다.

### 주요 작업 방향

`TeamState`에 `language`와 `framework` 필드를 추가하고, Triage 단계에서 언어/프레임워크를 자동 감지합니다. 언어별 전용 Docker 이미지(Java/Maven, Node/Jest 등)를 Dockerfile로 관리합니다. `context_retriever.py`의 검색 백엔드를 키워드 기반에서 PGVector 기반 임베딩 검색으로 업그레이드하여 대규모 코드베이스도 정확히 처리합니다. Organization 수준에서 여러 레포를 동시에 다루는 멀티-레포 에이전트 팀 구조를 설계합니다.

---

## 전체 Success Metrics (프로젝트 완료 기준)

실제 GitHub Issue 10개 이상을 80% 이상 자동 해결해야 합니다. 평균 LLM 토큰 비용을 Phase 2 이전 대비 60% 이하로 절감해야 합니다. LangSmith 평가 점수 4.5/5.0 이상을 달성해야 합니다. Human-in-the-loop 개입률이 20% 이하여야 합니다. 모든 QA 테스트가 `network_mode="none"` 격리 환경에서 통과되어야 합니다.

---

## 위험 요소 & 대안

LLM 비용 폭발의 위험이 있습니다. 대안으로 Skill on-demand 캐싱, Prompt Caching(Anthropic/OpenAI), `max_revision_count` 상한 설정을 적용합니다. 환각의 위험이 있습니다. 대안으로 Structured Output(Pydantic v2 strict 모드), Self-Healing loop 내 에러 로그 구조화를 적용합니다. Span-Edit 오작동의 위험이 있습니다. 대안으로 수정 전 파일을 `.bak`으로 백업하고, 적용 후 Diff를 검증하는 안전장치를 구현합니다. Docker 환경 의존성의 위험이 있습니다. 대안으로 Docker 없이 동작하는 subprocess 기반 fallback 모드를 유지합니다.

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026.03.27 | `.ai/` 디렉토리 구조, `sandbox.py`, `evaluate.py` 초안 |
| 2026.03.28 | `workflow.yaml` 도입, create_agent vs LangGraph 설계 논의 |
| 2026.03.28 | 로드맵 전면 재작성 — Phase 0 완료 기준 재정의, Phase 간 의존성 맵 추가, 각 Phase 작업 구체화, 알려진 버그 목록 추가 |