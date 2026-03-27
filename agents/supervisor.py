import os
import sys
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 상위 폴더의 state.py에서 TeamState 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState
from utils.prompt_loader import load_role_prompt

class SupervisorReview(BaseModel):
    is_approved: bool = Field(description="코드 승인 여부. 기준을 충족하면 True, 리팩토링이나 수정이 필요하면 False")
    review_feedback: str = Field(description="개발자에게 전달할 리뷰 코멘트. 반려 시 구체적인 수정 방향 제시, 승인 시에는 빈 문자열('')을 반환할 것.")

def supervisor_node(state: TeamState) -> dict:
    print(" [총괄감독] QA를 통과한 코드의 품질과 기획 부합 여부를 리뷰 중입니다...")

    issue_description = state.get("issue_description", "")
    current_code = state.get("current_code", {})
    rev_count = state.get("revision_count", 0)

    code_context = ""
    for file_path, code in current_code.items():
        code_context += f"--- {file_path} ---\n{code}\n\n"

    loop_warning = ""
    if rev_count >= 3:
        loop_warning = "\n[ATTENTION] Code has been revised multiple times. Unless there is a critical architectural flaw, please approve (True)."

    system_prompt = load_role_prompt("supervisor", loop_warning=loop_warning)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"[Execution Plan]\n{issue_description}\n\n[QA Passed Source Code]\n{code_context}"
        ),
    ]

    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.1)
    structured_llm = llm.with_structured_output(SupervisorReview)

    response_data = structured_llm.invoke(messages)

    # Pydantic 파싱 보정
    if isinstance(response_data, dict):
        is_approved = response_data.get("is_approved", False)
        review_feedback = response_data.get("review_feedback", "")
    else:
        is_approved = response_data.is_approved
        review_feedback = response_data.review_feedback

    print("\n" + "=" * 50)
    if is_approved:
        print("✅ [총괄감독] 리뷰 결과: 승인 (Merge Approved)")
    else:
        print("❌ [총괄감독] 리뷰 결과: 반려 (Changes Requested)")

    print("-" * 50)
    print(f"💬 코멘트:\n{review_feedback}")
    print("=" * 50 + "\n")

    # 4. 상태 업데이트 후 라우터로 전달
    return {"is_approved": is_approved, "review_feedback": review_feedback}
