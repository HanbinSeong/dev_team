# AI Development Team Agent

본 프로젝트는 비동기적으로 동작하는 자율적인 AI 에이전트들로 구성된 소프트웨어 개발 파이프라인을 구축하는 것을 목적으로 합니다. 사용자의 요구사항 분석부터 코드 작성, 테스트, 그리고 최종 리뷰까지의 전 과정을 자동화하여 개발 업무의 효율성을 극대화합니다.

## Project Purpose

전통적인 소프트웨어 개발 프로세스에서의 의사결정 및 구현 단계를 AI 에이전트 간의 협업 시스템으로 대체합니다. 각 에이전트는 독립적인 페르소나와 책임을 가지며, 단순한 코드 생성을 넘어 실행 결과를 바탕으로 오류를 스스로 수정하는 자가 치유(Self-Healing) 메커니즘을 통해 완성도 높은 결과물을 산출합니다.

## Project Structure

프로젝트의 디렉토리 구조는 에이전트의 역할과 상태 관리, 라우팅 로직을 명확히 분리하여 모듈화되어 있습니다.
```
.
├── agents/
│   ├── pm.py           # 기획자: 요구사항 분석 및 작업 지시서(Markdown) 작성
│   ├── dev.py          # 개발자: 지시서를 기반으로 실제 소스 코드 및 파일 생성/수정
│   ├── qa.py           # 테스터: 단위 테스트(pytest 등) 코드 작성 및 실행
│   └── supervisor.py   # 총괄감독: 코드 품질, 아키텍처, 기획 부합 여부 최종 리뷰 및 승인
├── routers.py          # 노드 간 조건부 전환(분기)을 제어하는 라우팅 로직
├── state.py            # LangGraph에서 공유되는 전역 상태(State) 데이터 구조 정의
├── main.py             # 시스템 진입점, LangGraph 워크플로우 조립 및 사용자 인터랙션 루프
├── requirements.txt    # 프로젝트 구동에 필요한 패키지 목록
└── .env                # 환경 변수 (OpenAI API Key 등)
```

## Architecture & Workflow

본 시스템은 LangGraph 기반의 상태 그래프(State Graph) 구조로 동작합니다. 4개의 핵심 에이전트 노드가 순환하며 점진적 개선 과정을 거칩니다.

<img src='https://drive.google.com/uc?id=1-H1d5umRSelM74cyk_oK8Crs8678utxx' style='width: 100%; height: auto;'>

1. PM Node (Analysis): 사용자의 요구사항을 분석하여 기술 스택, 파일 구조, 핵심 로직이 포함된 작업 지시서를 생성합니다. 기존 코드베이스가 존재하는 경우 이를 분석하여 변경 사항을 기획합니다.
2. Developer Node (Implementation): PM의 지시서와 피드백을 바탕으로 코드를 작성합니다. 신규 생성뿐만 아니라 기존 파일의 수정 및 유지보수를 수행합니다.
3. QA Node (Validation): 작성된 코드를 바탕으로 테스트 코드를 자동 생성하고 실행합니다. 테스트 실패 시 상세 에러 로그를 Developer에게 전달하여 수정을 요구합니다(Self-Healing).
4. Supervisor Node (Review): 최종 코드를 대상으로 스타일, 효율성, 요구사항 충족 여부를 검토합니다. 승인 시 워크플로우를 종료하며, 미달 시 수정 피드백과 함께 반려합니다.

## Tech Stack

- Core Framework: LangGraph, LangChain
- LLM: OpenAI
- Data Validation: Pydantic
- Testing: pytest
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

## License

본 프로젝트는 MIT License에 따라 배포됩니다. 자세한 내용은 LICENSE 파일을 참조하십시오.