# AI Development Team Agent - 로드맵

**프로젝트 개요**  
비동기 자율 AI 에이전트들로 구성된 소프트웨어 개발 파이프라인.  
요구사항 분석 → 설계 → 코드 작성(Span Edit) → 테스트 → 리뷰 → 자가 치유까지 **전 과정을 자동화**하고,  
개발자는 “AI를 오케스트레이션”하는 역할에 집중할 수 있는 환경을 목표로 합니다.

**현재 브랜치 상태 (dynamic-routing, 2026.3.28)**  
- `workflow.yaml` 기반 동적 라우팅 구현 중  
- `.ai/` 디렉토리 + `utils/prompt_loader.py` + `state.py` + `routers.py` + `sandbox.py` (Docker 기반)  
- LangGraph + LangSmith 평가 하네스 적용  
- QA 에이전트: subprocess → Docker sandbox 전환 완료

---

## 전체 설계 원칙 (2026년 최신 트렌드 반영)
- **Orchestration**: LangGraph (StateGraph + conditional edge + checkpoint + subgraph)
- **Context & Skill Layer**: Harness Engineering (AGENTS.md + 역할별 SKILL.md + create_agent factory)
- **Core Philosophy**: Prompt Engineering → Harness Engineering으로 진화 (토큰 60~75% 절감, 선언형 유지보수)

---

## [Phase 0] 준비 (Completed)
- [x] LangGraph 기본 파이프라인 구축 (PM → Dev → QA)
- [x] Docker sandbox + evaluate.py (LangSmith)
- [x] workflow.yaml 도입 (AGENTS.yaml → workflow.yaml 리네임 완료)
- [x] state.py 확장 및 routers.py

**Success Criteria**: `main.py` 실행 시 YAML 기반 동적 그래프 조립 성공

---

## [Phase 1] 동적 라우팅 및 의도 분석(Triage) 체계 확립 (현재 진행 단계)
**Fact**: 기존 파이프라인이 일직선으로 고정되어 있어 단순 수정 요청에도 PM부터 다시 시작하는 비효율 발생.

**작업 계획**
1. Triage 노드 완성 (의도 분류: new_feature, code_fix, bugfix, refactor, documentation, research)
2. `state.py`에 `triage_destination`, `confidence_score` 추가
3. `utils/graph_builder.py`로 YAML → LangGraph 동적 조립 완성
4. PoC 데모: `tests/triage_test.py` 작성

**Success Criteria**
- 사용자 지시 1개 입력 → 정확한 triage_destination 결정 (LangSmith 평가 4.5/5.0 이상)
- confidence < 0.7 시 Supervisor 또는 Human-in-the-loop 전환

**예상 기간**: 3~5일 (현재 70% 완료)

---

## [Phase 2] Harness Engineering + agents/ 리팩토링 (최우선 다음 단계)
**Fact**: 현재 agents/ 폴더가 flat 구조이며 prompt가 하드코딩/단일 파일에 집중되어 있음.

**작업 계획**
1. **Harness Engineering 도입**
   - Root에 `AGENTS.md` 작성 (선언형 가이드)
   - `skills/` 디렉토리 신설 (pm/, architect/, coder/, reviewer/, self-healing/)
   - 각 skill 폴더에 `SKILL.md` (YAML frontmatter + step-by-step) 작성
2. **agents/ 리팩토링**
   - `agents/harness_loader.py` (기존 prompt_loader.py 업그레이드)
   - `agents/factory.py` (`create_agent(role, skills=...)` factory 추가)
   - 각 노드(`pm.py`, `dev.py`, `qa.py` 등)를 **thin wrapper**로 변경 (10줄 이하)
3. Prompt decoupling: `.ai/roles/`, `.ai/conventions/`, `.ai/rules/` 활용
4. Self-Healing 서브루프: QA 내부에서 최대 3회 retry + exponential backoff

**Success Criteria**
- `create_agent("coder", skills=["span-edit"])` 호출로 에이전트 생성 가능
- Skill Loader가 SKILL.md를 on-demand로 로드하여 토큰 사용량 60% 이상 감소

**예상 기간**: 5~7일

---

## [Phase 3] 에이전트 도구화(Tooling) 및 서브그래프 확장
**Fact**: Dev 에이전트는 전체 파일 재작성, PM은 컨텍스트 검색 불가.

**작업 계획**
1. **Skill 구현**
   - Coder: Span-Edit Skill (tree-sitter 또는 diff 기반)
   - PM: Context Retrieval Skill (RAG + workspace/GitHub)
   - QA: Sandbox Execution & Parsing Skill (structured error JSON)
2. PM Subgraph 구축 (Context Retriever → Architect → Lead PM)
3. GitHub API 연동 (githubkit) → 자동 PR 생성
4. Supervisor에 Skill-aware routing 강화

**Success Criteria**
- Span-Edit만으로 코드 수정 성공률 90% 이상
- PM Subgraph가 독립적으로 실행 가능

**예상 기간**: 7~10일

---

## [Phase 4] 프로덕션 UI/UX 및 비동기 처리 환경 통합
**Fact**: 현재 CLI 중심으로 HITL과 병렬 처리가 제한적.

**작업 계획**
1. Streamlit 대시보드 (demo mode / team mode)
2. Celery + Redis를 활용한 완전 비동기 task queue
3. LangGraph Persistence (PostgreSQL checkpoint) + `astream_events`
4. HITL 지점 명확화 (`interrupt_before` + UI 승인 버튼)

**Success Criteria**
- 다중 사용자 요청 동시 처리
- 워크플로우 재시작/복구 가능

**예상 기간**: 7~10일

---

## [Phase 5] 확장성 및 멀티-스택 지원 (Future)
- Multi-language/framework 지원 (Python → TS, Go, Java)
- Vector DB (PGVector) + 장기 메모리 RAG
- GitHub App 연동 (실제 repo에 PR 자동 생성)
- Multi-repo / Organization-level 에이전트 팀

---

## Success Metrics (프로젝트 완료 기준)
- 10개 이상의 실제 GitHub Issue를 80% 이상 자동 해결
- 평균 LLM 토큰 비용 30% 이하 절감 (Harness + Span-Edit + Caching)
- LangSmith 평가 점수 4.5/5.0 이상
- Human-in-the-loop 개입률 20% 이하

## 위험 요소 & 대안
- LLM 비용 폭발 → Skill on-demand + Prompt Caching + max_retry 제한
- 환각 → Structured Output (Pydantic v2 strict) + Self-Healing loop