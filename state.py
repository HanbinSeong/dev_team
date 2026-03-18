from typing import TypedDict, Dict

class TeamState(TypedDict):
    # 1. 메타 데이터 및 초기 입력
    workspace_dir: str       # 작업을 수행할 로컬 폴더 경로 (예: "/Users/name/ai_workspace/my_project")
    user_request: str        # 사용자가 입력한 자연어 작업 지시

    # 2. PM 에이전트 산출물
    issue_description: str   # PM이 구체화한 개발 명세서 (JSON 스키마, 요구사항, 구조 등)

    # 3. 개발자 에이전트 산출물
    # 단일 문자열이 아닌 딕셔너리로 관리하여 여러 파일을 동시에 다룰 수 있게 합니다.
    # 예: {"main.py": "print('hello')", "models/user.py": "class User: ..."}
    current_code: Dict[str, str] 

    # 4. QA 에이전트 산출물
    test_report: str         # 테스트 실행 결과 로그 (에러 메시지 포함)
    qa_passed: bool          # 테스트 통과 여부 (True면 감독에게, False면 개발자에게)

    # 5. 총괄감독 에이전트 산출물
    review_feedback: str     # 코드 스타일, 구조 등에 대한 리뷰 코멘트
    is_approved: bool        # 최종 병합 승인 여부 (True면 워크플로우 종료)

    # 6. 시스템 제어
    revision_count: int      # 반려 횟수 카운터 (무한 피드백 루프 방지용)