import os
import sys
import datetime
from dotenv import load_dotenv
load_dotenv()
from langgraph.graph import StateGraph, END
from state import TeamState
from routers import route_qa_to_next, route_supervisor_to_next
from agents.pm import pm_node
from agents.dev import dev_node
from agents.qa import qa_node
from agents.supervisor import supervisor_node


def build_graph():
    """LangGraph builder"""
    workflow = StateGraph(TeamState)

    # 1. 노드 추가
    workflow.add_node("pm", pm_node)
    workflow.add_node("dev", dev_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("supervisor", supervisor_node)

    # 2. 엣지 연결 (순서 정의)
    workflow.set_entry_point("pm")
    workflow.add_edge("pm", "dev")

    # 3. 조건부 흐름 연결
    workflow.add_conditional_edges("dev", lambda _: "qa")  # 개발 후 무조건 QA로 이동
    workflow.add_conditional_edges(
        "qa", route_qa_to_next, {"supervisor": "supervisor", "dev": "dev"}
    )
    workflow.add_conditional_edges(
        "supervisor", route_supervisor_to_next, {"end": END, "dev": "dev"}
    )

    return workflow.compile()


def main():
    print("=== AI 개발 에이전트 시스템 시작 ===\n")

    # [1단계] 작업 디렉토리 설정
    target_dir = input("작업을 진행할 프로젝트 디렉토리 이름을 입력하세요: ").strip()

    # 현재 스크립트가 실행되는 경로(루트) 아래에 폴더 경로 설정
    workspace_path = os.path.join(os.getcwd(), target_dir)

    if not os.path.exists(workspace_path):
        os.makedirs(workspace_path)
        print(f"📁 새 프로젝트 디렉토리를 생성했습니다: {workspace_path}")
    else:
        print(f"📁 기존 프로젝트 디렉토리를 사용합니다: {workspace_path}")

    # 랭그래프 앱 초기화
    ai_team_app = build_graph()

    # 로그 파일 경로 설정
    log_file_path = os.path.join(workspace_path, "workflow_log.txt")

    # [2단계] 사용자 상호작용 루프
    while True:
        print("\n" + "=" * 40)
        print("1. 작업지시")
        print("2. 작업종료")
        print("=" * 40)

        choice = input("메뉴를 선택하세요 (1 또는 2): ").strip()

        if choice == "1" or choice == "작업지시":
            user_request = input("\n작업을 지시해주세요: ").strip()

            if not user_request:
                print("⚠️ 작업 지시가 비어있습니다. 다시 입력해주세요.")
                continue

            print("\n [시스템] AI 개발팀이 작업을 시작합니다...\n")

            # --- 작업 시작 시 로그 파일에 헤더 기록 ---
            with open(log_file_path, "a", encoding="utf-8") as log_file:
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"\n\n{'='*60}\n")
                log_file.write(f" [새로운 작업 시작] {now_str}\n")
                log_file.write(f" 사용자 지시: {user_request}\n")
                log_file.write(f"{'='*60}\n\n")

            # 상태(State) 초기화: 사용자의 지시와 작업할 폴더 경로를 함께 주입합니다.
            initial_state = TeamState(
                user_request=user_request,
                workspace_dir=workspace_path,
                issue_description="",
                current_code={},
                test_report="",
                qa_passed=False,
                review_feedback="",
                is_approved=False,
                revision_count=0,
            )

            # 랭그래프 실행 및 진행 상황 스트리밍
            for output in ai_team_app.stream(initial_state):
                for node_name, state_update in output.items():
                    print(f"✅ [{node_name.upper()}] 단계 완료")

                    # --- 각 노드 완료 시 로그 파일에 상세 결과 기록 ---
                    with open(log_file_path, "a", encoding="utf-8") as log_file:
                        log_file.write(f"--- [{node_name.upper()}] 단계 실행 결과 ---\n")
                        
                        if node_name == "pm":
                            log_file.write(f" 작성된 지시서:\n{state_update.get('issue_description', '')}\n")
                        
                        elif node_name == "developer":
                            log_file.write(" 생성/수정된 파일 목록:\n")
                            for file_path in state_update.get('current_code', {}).keys():
                                log_file.write(f"  - {file_path}\n")
                            log_file.write(f" 현재 코드 수정(반려) 횟수: {state_update.get('revision_count', 0)}\n")
                        
                        elif node_name == "qa":
                            passed = "✅ 통과" if state_update.get('qa_passed') else "❌ 실패"
                            log_file.write(f" QA 결과: {passed}\n")
                            log_file.write(f" 상세 에러/테스트 리포트:\n{state_update.get('test_report', '')}\n")
                        
                        elif node_name == "supervisor":
                            approved = "✅ 병합 승인" if state_update.get('is_approved') else "❌ 반려 (수정 요청)"
                            log_file.write(f" 최종 검수 결과: {approved}\n")
                            log_file.write(f" 리뷰 코멘트:\n{state_update.get('review_feedback', '')}\n")
                            
                        log_file.write("\n")

            print(f"\n [시스템] 작업 완료! 상세 로그는 '{log_file_path}'에서 확인하실 수 있습니다.")

        elif choice == "2" or choice == "작업종료":
            print("\n에이전트를 종료합니다. 수고하셨습니다!")
            sys.exit(0)  # 프로그램 완전히 종료

        else:
            print("\n⚠️ 잘못된 입력입니다. '1' 또는 '2'를 입력해주세요.")


if __name__ == "__main__":
    main()
