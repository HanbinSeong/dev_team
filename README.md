# AI Development Team Agent

본 프로젝트는 비동기적으로 동작하는 자율 AI 에이전트들로 구성된 소프트웨어 개발 파이프라인입니다.  
요구사항 분석부터 코드 작성, 테스트, 리뷰까지 전 과정을 자동화하여 개발 생산성과 품질을 향상시키는 것을 목표로 합니다.

## Project Purpose

AI 시대의 개발자는 단순 구현자가 아니라, AI를 효과적으로 통제하고 오케스트레이션하는 역할을 수행합니다.  
본 프로젝트는 이러한 역량을 강화하기 위해 에이전트 기반 개발 환경과 워크플로우를 설계하고 실험하는 것을 목표로 합니다.

전통적인 개발 프로세스의 의사결정 및 구현 단계를 AI 협업 시스템으로 대체하고, 
실행 기반 피드백 루프를 통해 지속적으로 결과를 개선하는 구조를 탐구합니다.

## Architecture & Workflow

본 시스템은 LangGraph 기반의 상태 그래프(State Graph) 구조로 동작합니다. 4개의 핵심 에이전트 노드가 순환하며 점진적 개선 과정을 거칩니다.

<img width="2816" height="1536" alt="AI 에이전트 시퀀스 다이어그램" src="https://github.com/user-attachments/assets/ce2af858-8dea-4381-b0f7-2e1afad52eea" />

1. PM Node (Analysis): 사용자의 요구사항을 분석하여 기술 스택, 파일 구조, 핵심 로직이 포함된 작업 지시서를 생성합니다. 기존 코드베이스가 존재하는 경우 이를 분석하여 변경 사항을 기획합니다.
2. Developer Node (Implementation): PM의 지시서와 피드백을 바탕으로 코드를 작성합니다. 신규 생성뿐만 아니라 기존 파일의 수정 및 유지보수를 수행합니다.
3. QA Node (Validation): 작성된 코드를 바탕으로 테스트 코드를 자동 생성하고 실행합니다. 테스트 실패 시 상세 에러 로그를 Developer에게 전달하여 수정을 요구합니다(Self-Healing).
4. Supervisor Node (Review): 최종 코드를 대상으로 스타일, 효율성, 요구사항 충족 여부를 검토합니다. 승인 시 워크플로우를 종료하며, 미달 시 수정 피드백과 함께 반려합니다.

## Tech Stack

- Core Framework: LangGraph, LangChain
- LLM: OpenAI
- Data Validation: Pydantic
- Testing: pytest, Docker
- Language Support: Python, `Java, JavaScript/TypeScript (확장 예정)`

## Usage

### 1. Prerequisites
프로젝트 루트 디렉토리에 .env 파일을 생성하고 OpenAI API 키를 입력합니다.
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Install Dependencies
```
pip install -r requirements.txt
```

### 3. Run the System
```
python main.py
```
실행 후 작업 폴더명을 입력하고 개발 지시를 내리면, 해당 폴더 내에 소스 코드와 전체 작업 과정이 기록된 `workflow_log.txt`가 생성됩니다.

## Roadmap & Future Improvements

### 1. 에이전트 및 프롬프트 고도화
- 기존 코드베이스(Brown-field) 대응: PM 및 Developer 에이전트가 기존 프로젝트를 탐색하고 이해하여 유지보수 작업을 수행하도록 개선.
- PM 서브그래프 확장: PM 노드를 다단계 서브그래프로 분리하여 MCP 기반 지식 검색 및 아키텍처 설계 선행.
- 코드 스타일링 체계화: 클린 코드 원칙 및 프로젝트별 네이밍 컨벤션을 시스템 프롬프트에 내재화.

### 2. 멀티 스택 지원 (Multi-Stack)
- State 확장: TeamState에 language 및 framework 항목을 추가하여 개발 환경 명시적 관리.
- 환경 대응: Java(Spring Boot), React, TypeScript, Next.js 등 다양한 개발 환경에 최적화된 에이전트 및 테스트 환경 구축.

### 3. CI/CD 및 인프라 통합
- Docker 컨테이너 격리: 에이전트가 생성한 코드를 격리된 도커 환경에서 실행 및 테스트하여 안전성 확보.
- GitHub 연동: 최종 승인 시 자동으로 GitHub 브랜치 생성 및 Pull Request 작성 수행.

### 4. 제어 및 지능화
- Human-in-the-Loop (HITL): 주요 의사결정 단계에서 사용자의 승인 및 개입 절차 추가.
- RAG 기반 문맥 유지: 전체 코드베이스 히스토리를 벡터 DB에 색인하여 일관된 컨텍스트 유지 및 할루시네이션 방지.

## Current Progress & Discussion

### 20260327
- 각 노드에 하드코딩된 Prompt를 추후 동적으로 제어하기 위해 전면 리팩토링 -> 프롬프트들은 `.ai/` 디렉토리에서 관리
- `utils/` 에 `prompt_loader.py` 추가
- `utils/` 에 `sandbox.py` 추가 (qa노드: Docker기반 sandbox환경에서 pytest 실행)
- `evaluate.py`: LangSmith로 AI 에이전트 평가 하네스 구축

### 20260328
- `.ai/AGENTS.yaml` 구성: LangGraph에 사용되는 전역 config 설정
- "langchain 라이브러리에서 `creat_agent` 를 지원하는데, langgraph로 직접 agent들을 구현해야할까?"에 대한 의문발생.

    #### `create_agent`와 `LangGraph + State`의 차이
    - `create_agent` (LangChain의 내장 에이전트)
      - 블랙박스(Black-box) 구조
      - 내부 `ReAct(Reasoning and Acting)` 루프, 에이전트가 언제 어떤 도구를 쓸지, 몇 번 재시도할지 LLM 스스로 결정
      - Single agent 구조
    - `LangGraph + State` (현재 방식)
      - 화이트박스(White-box) 구조
      - YAML 파일과 그래프 엣지를 통해 명시적인 업무 흐름을 개발자 직접 통제
    
    #### 각 노드 `create_agent` 할당 장점 및 단점
    1. **장점**
    - 복잡한 도구 사용 위임: 각 에이전트에게 `웹검색`, `DB조회`, `코드실행`, `샌드박스` 등 도구들을 연결하면 LangGraph 단위에서 각 Tool을 분기처리할 필요없이 노드에서 알아서 도구 사용
    - 관심사 분리: 메인 오케스트레이션은 비즈니스 로지만 관리, 각 노드는 자신만의 문제해결 방식 집중
    1. **단점**
    - Token & Latency 증가
    - 통제 불가능성
    - State 연결 복잡성
    
    #### 단점을 극복하기 위한 방법
    - **캡슐화된 `Skill` 할당**: 데이터 검증, 예외 처리, 재시도 로직이 캡슐화된 'Skill'을 에이전트에게 할당하여 에이전트의 행동 반경이 제한되고 예측 가능해져 응답의 정확성과 신뢰성이 크게 상승
    - **agent 통제 및 제어**: `create_agents`로 생성된 agent가 자율적으로 request에 따라 동작을 하는 것이 아닌, 사용자의 의도와 범위 내에서 동작하도록 처리
    => 결국엔 agent가 할루시네이션에 빠지지 않게 하기위해선 또 하나의 langgraph를 만드는 것과 다를바없나?
- 위 의문에 대한 배경은 다양한 상황에서의 `input_request`(ex. "A함수를 직접 구현한건 비효율적이야. 동일한 기능을 하는 B 라이브러리를 사용해."의 경우, pm부터 시작하는건 매우 비효율적), 나아가 `gpt-codex`처럼 AI 에이전트가 스스로 프로그램을 개발할 수 있는 환경이 될 수 있나? 에 대해서 충족시키지 못했기 때문임.

## License

본 프로젝트는 MIT License에 따라 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하십시오.
