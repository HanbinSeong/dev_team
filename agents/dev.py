import os
import sys
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState

# ---------------------------------------------------------
# LLM이 출력할 데이터의 구조를 강제(Formatting)하는 Pydantic 모델
# ---------------------------------------------------------
class CodeFile(BaseModel):
    file_path: str = Field(description="파일의 상대 경로 및 이름 (예: main.py, requirements.txt, src/db.py)")
    code: str = Field(description="작성된 소스 코드 또는 텍스트 내용")

class DeveloperOutput(BaseModel):
    files: List[CodeFile] = Field(description="이번 작업에서 생성하거나 수정할 파일들의 목록")

# ---------------------------------------------------------
# 개발자 노드 로직
# ---------------------------------------------------------
def dev_node(state: TeamState) -> dict:
    print("👨‍💻 [개발자] 코드를 작성/수정 중입니다...")
    
    issue_description = state.get("issue_description", "")
    workspace_dir = state.get("workspace_dir", "")
    review_feedback = state.get("review_feedback", "")
    test_report = state.get("test_report", "")
    qa_passed = state.get("qa_passed", True)
    rev_count = state.get("revision_count", 0)

    # 1. 시스템 프롬프트 구성 (신규 개발 vs 수정 개발 분기)
    system_prompt = f"""당신은 AI 개발팀의 핵심 수석(Senior) 소프트웨어 엔지니어입니다.
PM이 작성한 [작업 지시서]를 바탕으로 실제 실행 가능하고 버그가 없는 완벽한 코드를 작성해야 합니다.

[작업 환경]
- 프로젝트 루트 경로: {workspace_dir}
- 제공하는 모든 파일 경로는 이 루트를 기준으로 한 '상대 경로'로 작성하세요. (예: app.py, models/user.py)"""
    
    # 만약 반려되어 다시 돌아온 경우 (리팩토링 또는 버그 수정 모드)
    if rev_count > 0:
        system_prompt += "\n\n🚨 [주의: 코드가 반려되었습니다! 아래 피드백을 반드시 반영하여 코드를 수정하세요.]\n"
        if not qa_passed:
            system_prompt += f"- 🧪 QA 에러 로그:\n{test_report}\n"
        if review_feedback:
            system_prompt += f"- 🕵️‍♂️ 감독 리뷰:\n{review_feedback}\n"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"[작업 지시서]\n{issue_description}")
    ]

    # 2. LLM 호출 (구조화된 출력 사용)
    # 코딩 작업이므로 temperature를 낮춰 안정성을 높입니다.
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
    print(f"💾 [개발자] {workspace_dir} 에 파일 저장 시작")
    print("="*50)
    
    for file_obj in response.files:
        file_path = file_obj.file_path
        code_content = file_obj.code
        
        # 실제 저장할 절대 경로 조립
        full_path = os.path.join(workspace_dir, file_path)
        
        # 파일이 들어갈 하위 폴더가 아직 없다면 생성 (예: src/api.py 라면 src 폴더 생성)
        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # 파일 쓰기 모드로 저장
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(code_content)
            
        current_code_dict[file_path] = code_content
        print(f"  ✔️ 생성 완료: {file_path}")
    
    print("="*50 + "\n")
    
    # 4. 상태 업데이트 후 다음 노드(QA)로 전달
    return {
        "current_code": current_code_dict,
        "revision_count": rev_count + 1
    }