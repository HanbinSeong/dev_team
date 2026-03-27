import os
import sys
import subprocess
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 상위 폴더의 state.py에서 TeamState 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState
from utils.prompt_loader import load_role_prompt

class QATestCode(BaseModel):
    test_code: str = Field(description="pytest로 실행 가능한 완벽한 테스트 파이썬 코드")

def qa_node(state: TeamState) -> dict:
    print(" [QA] 개발된 코드를 분석하고 테스트 코드를 작성 중입니다...")

    workspace_dir = state.get("workspace_dir", "")
    issue_description = state.get("issue_description", "")
    current_code = state.get("current_code", {})

    code_context = ""
    for file_path, code in current_code.items():
        code_context += f"--- {file_path} ---\n{code}\n\n"

    system_prompt = load_role_prompt("qa")

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"[Execution Plan]\n{issue_description}\n\n[Source Code]\n{code_context}"
        ),
    ]

    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.1)
    structured_llm = llm.with_structured_output(QATestCode)

    response_data = structured_llm.invoke(messages)

    # Pydantic 파싱 보정
    if isinstance(response_data, dict):
        test_content = response_data.get("test_code", "")
    else:
        test_content = response_data.test_code

    # 테스트 코드를 로컬 작업 폴더에 저장
    test_file_path = os.path.join(workspace_dir, "test_ai_qa.py")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"   ✔️ 테스트 코드 생성 완료: {test_file_path}")
    print(" [QA] 터미널에서 pytest를 실행하여 코드를 검증합니다...")

    # 파이썬 subprocess를 사용하여 실제로 pytest 실행
    try:
        result = subprocess.run(
            ["pytest", "test_ai_qa.py", "-v"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 무한 루프 방지
        )

        # exit code가 0이면 테스트 통과, 아니면 실패
        if result.returncode == 0:
            qa_passed = True
            test_report = (
                "✅ [QA Success] All tests passed.\n\n" + result.stdout
            )
            print("   -> ✅ QA 테스트 통과!")
        else:
            qa_passed = False
            test_report = "[QA Failed] Errors occurred during testing. Please check the logs below and fix the code.\n\n" + result.stdout + "\n" + result.stderr
            print("   -> ❌ QA 테스트 실패")

    except subprocess.TimeoutExpired:
        qa_passed = False
        test_report = "❌ [QA Failed] Test execution exceeded 30 seconds and was terminated. (Possible infinite loop or deadlock)"
        print("   -> ❌ 타임아웃 에러 발생")
    except Exception as e:
        qa_passed = False
        test_report = f"❌ [QA System Error] Unknown error occurred during test execution: {str(e)}"
        print(f"   -> ❌ 시스템 에러 발생: {e}")

    print("\n" + "=" * 50)
    print("📊 [QA 리포트 요약]")
    print(test_report[:500] + ("..." if len(test_report) > 500 else ""))
    print("=" * 50 + "\n")

    return {"test_report": test_report, "qa_passed": qa_passed}
