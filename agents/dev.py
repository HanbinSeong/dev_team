import os
import sys
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState
from utils.prompt_loader import load_role_prompt

class CodeFile(BaseModel):
    file_path: str = Field(description="파일의 상대 경로 및 이름 (예: main.py, requirements.txt, src/db.py)")
    code: str = Field(description="작성된 소스 코드 또는 텍스트 내용")

class DeveloperOutput(BaseModel):
    files: List[CodeFile] = Field(description="이번 작업에서 생성하거나 수정할 파일들의 목록")

def dev_node(state: TeamState) -> dict:
    print(" [개발자] 코드를 작성/수정 중입니다...")
    
    issue_description = state.get("issue_description", "")
    workspace_dir = state.get("workspace_dir", "")
    review_feedback = state.get("review_feedback", "")
    test_report = state.get("test_report", "")
    qa_passed = state.get("qa_passed", True)
    rev_count = state.get("revision_count", 0)

    feedback_section = ""
    if rev_count > 0:
        feedback_section += "\n\n [ATTENTION: The code was rejected. You MUST apply the following feedback to fix the code.]\n"
        if not qa_passed:
            feedback_section += f"- QA Error Log:\n{test_report}\n"
        if review_feedback:
            feedback_section += f"- Supervisor Review:\n{review_feedback}\n"

    system_prompt = load_role_prompt("dev", workspace_dir=workspace_dir, feedback_section=feedback_section)    

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"[Execution Plan]\n{issue_description}")
    ]

    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)
    structured_llm = llm.with_structured_output(DeveloperOutput)
    
    response_data = structured_llm.invoke(messages)

    if isinstance(response_data, dict):
        response = DeveloperOutput(**response_data)
    else:
        response = response_data
    
    # 3. 반환받은 코드를 실제 파일 시스템에 저장
    current_code_dict = {}
    
    print("\n" + "="*50)
    print(f" [개발자] {workspace_dir} 에 파일 저장 시작")
    print("="*50)
    
    for file_obj in response.files:
        file_path = file_obj.file_path
        code_content = file_obj.code
        
        full_path = os.path.join(workspace_dir, file_path)
        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        current_code_dict[file_path] = code_content
        print(f"  ✔️ 생성 완료: {file_path}")
    
    print("="*50 + "\n")
    
    return {
        "current_code": current_code_dict,
        "revision_count": rev_count + 1
    }