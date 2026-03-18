import os
import sys
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 상위 폴더의 state.py에서 TeamState 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState


# ---------------------------------------------------------
# LLM이 출력할 리뷰 결과 구조를 강제하는 Pydantic 모델
# ---------------------------------------------------------
class SupervisorReview(BaseModel):
    is_approved: bool = Field(
        description="코드 승인 여부. 기준을 충족하면 True, 리팩토링이나 수정이 필요하면 False"
    )
    review_feedback: str = Field(
        description="개발자에게 전달할 리뷰 코멘트. 반려 시 구체적인 수정 방향 제시, 승인 시 격려의 말"
    )


# ---------------------------------------------------------
# 총괄감독 노드 로직
# ---------------------------------------------------------
def supervisor_node(state: TeamState) -> dict:
    print("🕵️‍♂️ [총괄감독] QA를 통과한 코드의 품질과 기획 부합 여부를 리뷰 중입니다...")

    issue_description = state.get("issue_description", "")
    current_code = state.get("current_code", {})
    rev_count = state.get("revision_count", 0)

    # 여러 파일로 나뉜 코드를 하나의 문자열로 병합하여 LLM에게 제공
    code_context = ""
    for file_path, code in current_code.items():
        code_context += f"--- {file_path} ---\n{code}\n\n"

    # 무한 루프(핑퐁)를 방지하기 위해, 수정 횟수가 많아지면 승인 기준을 낮추도록 지시합니다.
    loop_warning = ""
    if rev_count >= 3:
        loop_warning = "\n[주의] 이미 여러 번 수정이 진행되었습니다. 치명적인 아키텍처 결함이 아니라면 가급적 승인(True) 처리하세요."

    # 1. 총괄감독 시스템 프롬프트
    system_prompt = f"""당신은 AI 소프트웨어 개발 팀의 수석 아키텍트이자 총괄감독(Tech Lead)입니다.
QA 테스트를 무사히 통과한 코드가 올라왔습니다. 이제 아래 제공된 [원본 작업 지시서]와 [소스 코드]를 비교하여 최종 병합(Merge) 여부를 결정하세요.

[리뷰 기준]
1. PM의 요구사항을 모두 충족했는가? (기능 누락 확인)
2. 변수명, 함수명 등 네이밍 컨벤션이 깔끔한가?
3. 불필요한 하드코딩이나 비효율적인 로직(예: N+1 문제, 과도한 루프 등)이 없는가?
4. 주석이나 예외 처리가 적절히 되어 있는가?

위 기준에 미달한다면 `is_approved`를 False로 설정하고, 구체적으로 어떤 파일의 어떤 라인을 고쳐야 할지 `review_feedback`에 작성하여 반려하세요.
완벽하다면 `is_approved`를 True로 설정하고 격려의 메시지를 남기세요.{loop_warning}"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"[원본 작업 지시서]\n{issue_description}\n\n[QA 통과 소스 코드]\n{code_context}"
        ),
    ]

    # 2. LLM 호출 (구조화된 출력 사용)
    # 평가를 내리는 작업이므로 일관성을 위해 temperature를 낮춥니다.
    llm = ChatOpenAI(
        model="gpt-5-nano", temperature=0.1
    )  # 평가의 질을 높이기 위해 감독은 더 똑똑한 모델을 쓰면 좋습니다.
    structured_llm = llm.with_structured_output(SupervisorReview)

    response_data = structured_llm.invoke(messages)

    # Pydantic 파싱 보정
    if isinstance(response_data, dict):
        is_approved = response_data.get("is_approved", False)
        review_feedback = response_data.get("review_feedback", "")
    else:
        is_approved = response_data.is_approved
        review_feedback = response_data.review_feedback

    # 3. 터미널 출력용 UI
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
