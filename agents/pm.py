# agents/pm.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState

def pm_node(state: TeamState) -> dict:
    print("📋 [PM] 사용자의 요구사항을 분석하여 작업 지시서를 작성 중입니다...")
    
    user_request = state.get("user_request", "")
    workspace_dir = state.get("workspace_dir", "")
    
    # 환경 변수는 이미 main.py에서 로드되었으므로 바로 사용 가능합니다.
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)
    
    system_prompt = f"""당신은 AI 소프트웨어 개발 팀의 수석 Product Manager(PM)입니다.
사용자의 요구사항을 분석하여, 개발자 에이전트가 즉시 코드를 작성할 수 있도록 구체적이고 명확한 [작업 지시서]를 마크다운 형식으로 작성해야 합니다.

[작업 환경 정보]
- 프로젝트 로컬 폴더 경로: {workspace_dir}

[지시서 필수 포함 항목]
1. 목표 및 요구사항 요약
2. 추천 기술 스택 및 필요 패키지
3. 예상 파일 및 디렉토리 구조
4. 핵심 로직, API 명세, 또는 데이터 모델(DB 스키마 등)
5. 개발 시 주의사항 및 예외 처리 (Edge cases)

불필요한 인사말이나 부연 설명 없이, 오직 깔끔한 마크다운 문서 형태의 지시서만 출력하세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"사용자 요구사항: {user_request}")
    ]
    
    response = llm.invoke(messages)
    issue_desc = response.content
    
    print("\n" + "="*50)
    print("📄 [PM 작업 지시서 생성 완료]")
    print("="*50)
    print(issue_desc)
    print("="*50 + "\n")
    
    return {"issue_description": issue_desc}