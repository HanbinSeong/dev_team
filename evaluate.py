import os
from dotenv import load_dotenv
load_dotenv()

from langsmith import Client, evaluate
from main import build_graph
from state import TeamState

# Target Callable: 파이프라인 엔트리 포인트
def run_ai_team(inputs: dict) -> dict:
    """단일 테스트 케이스에 대해 워크플로우를 실행하고 최종 상태 반환"""
    app = build_graph()
    user_request = inputs["user_request"]
    task_id = inputs.get("task_id", "default_task")
    
    # 평가를 위한 격리된 워크스페이스 지정
    workspace_path = os.path.join(os.getcwd(), "eval_workspace", task_id)
    os.makedirs(workspace_path, exist_ok=True)
    
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
    
    # 그래프 실행
    final_state = app.invoke(initial_state)
    return final_state

# 2. Custom Evaluators: 결과를 평가하는 함수들
def qa_pass_evaluator(run, example) -> dict:
    """최종적으로 QA를 통과했는지 평가 (성공 1.0 / 실패 0.0)"""
    final_state = run.outputs
    passed = final_state.get("qa_passed", False)
    return {"key": "qa_pass_rate", "score": 1.0 if passed else 0.0}

def revision_efficiency_evaluator(run, example) -> dict:
    """수정(반려) 횟수가 적을수록 높은 점수 부여 (3회 이상 반려 시 0점)"""
    final_state = run.outputs
    rev_count = final_state.get("revision_count", 0)
    
    # 0회=1.0, 1회=0.66, 2회=0.33, 3회이상=0.0
    score = max(0.0, 1.0 - (rev_count / 3.0))
    return {"key": "efficiency_score", "score": score}

def final_approval_evaluator(run, example) -> dict:
    """총괄감독(Supervisor)의 최종 병합 승인을 받았는지 평가"""
    final_state = run.outputs
    approved = final_state.get("is_approved", False)
    return {"key": "final_approval_rate", "score": 1.0 if approved else 0.0}

# 3. Main 실행부: 데이터셋 생성 및 평가 가동
def main():
    client = Client()
    dataset_name = "AI_Dev_Team_Golden_Dataset"
    
    # 데이터셋이 존재하지 않으면 초기 샘플 데이터 생성
    if not client.has_dataset(dataset_name=dataset_name):
        print(f"'{dataset_name}' 데이터셋을 생성...")
        dataset = client.create_dataset(
            dataset_name=dataset_name, 
            description="AI 에이전트 팀의 코드 작성 및 자가 치유 능력 평가 데이터셋"
        )
        # 샘플 1: 파일 입출력 및 로직 구현
        client.create_example(
            inputs={
                "task_id": "task_top_words",
                "user_request": "사용자가 입력한 영어 텍스트 문서에서 가장 많이 등장하는 단어 TOP 5를 추출하고, 그 결과를 result.json 파일로 저장하는 파이썬 유틸리티 모듈을 만들어줘. 빈 텍스트 예외처리도 포함해."
            },
            dataset_id=dataset.id,
        )
        # 샘플 2: 간단한 알고리즘 (비교용)
        client.create_example(
            inputs={
                "task_id": "task_fibonacci",
                "user_request": "주어진 숫자 n에 대해 피보나치 수열의 n번째 값을 반환하는 파이썬 함수를 작성해줘. 0보다 작은 값이 들어오면 ValueError를 발생시켜야 해."
            },
            dataset_id=dataset.id,
        )

    print(f"🚀 '{dataset_name}' 데이터셋에 대한 평가 하네스 실행...")
    
    # LangSmith evaluate 실행
    experiment_results = evaluate(
        run_ai_team,
        data=dataset_name,
        evaluators=[qa_pass_evaluator, revision_efficiency_evaluator, final_approval_evaluator],
        experiment_prefix="ai-team-eval", # LangSmith UI에 표시될 실험 접두사
    )

if __name__ == "__main__":
    main()