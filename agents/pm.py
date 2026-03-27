# agents/pm.py
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState
from utils.prompt_loader import load_role_prompt

def pm_node(state: TeamState) -> dict:
    print(" [PM] 사용자의 요구사항을 분석하여 작업 지시서를 작성 중입니다...")
    
    user_request = state.get("user_request", "")
    workspace_dir = state.get("workspace_dir", "")

    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)
    
    system_prompt = load_role_prompt("pm", workspace_dir=workspace_dir)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User request: {user_request}")
    ]
    
    response = llm.invoke(messages)
    issue_desc = response.content
    
    print("\n" + "="*50)
    print(" [PM 작업 지시서 생성 완료]")
    print("="*50)
    print(issue_desc)
    print("="*50 + "\n")
    
    return {"issue_description": issue_desc}