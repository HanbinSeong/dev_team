from state import TeamState

def route_qa_to_next(state: TeamState) -> str:
    """
    QA 에이전트의 테스트 결과에 따라 다음 노드를 결정합니다.
    """
    # qa_passed가 True이면 총괄감독에게, False이면 다시 개발자에게 반려
    if state.get("qa_passed"):
        print("   🔀 [라우터] QA 통과! 총괄감독에게 코드를 전달합니다.")
        return "supervisor"
    
    print("   🔀 [라우터] QA 실패! 개발자에게 코드를 돌려보냅니다.")
    return "dev"


def route_supervisor_to_next(state: TeamState) -> str:
    """
    총괄감독 에이전트의 최종 리뷰 결과에 따라 워크플로우를 종료할지 결정합니다.
    """
    # is_approved가 True이면 워크플로우 종료(end), False이면 다시 개발자에게 반려
    if state.get("is_approved"):
        print("   🔀 [라우터] 최종 승인! 워크플로우를 종료합니다.")
        return "end"
    
    print("   🔀 [라우터] 리뷰 반려! 개발자에게 코드를 돌려보냅니다.")
    return "dev"