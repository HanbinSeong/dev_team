import os
import sys
import subprocess
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# 상위 폴더의 state.py에서 TeamState 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import TeamState


# ---------------------------------------------------------
# LLM이 출력할 테스트 코드의 구조를 강제하는 Pydantic 모델
# ---------------------------------------------------------
class QATestCode(BaseModel):
    test_code: str = Field(description="pytest로 실행 가능한 완벽한 테스트 파이썬 코드")


# ---------------------------------------------------------
# QA 노드 로직
# ---------------------------------------------------------
def qa_node(state: TeamState) -> dict:
    print("🧪 [QA] 개발된 코드를 분석하고 테스트 코드를 작성 중입니다...")

    workspace_dir = state.get("workspace_dir", "")
    issue_description = state.get("issue_description", "")
    current_code = state.get("current_code", {})

    # 현재까지 작성된 코드들을 문자열로 합쳐서 LLM에게 보여줍니다.
    code_context = ""
    for file_path, code in current_code.items():
        code_context += f"--- {file_path} ---\n{code}\n\n"

    # 1. QA 에이전트 시스템 프롬프트 (Mocking 강조)
    system_prompt = """ 당신은 AI 개발팀의 꼼꼼하고 엄격한 수석 QA 엔지니어입니다.
아래 제공된 [작업 지시서]와 개발자가 작성한 [소스 코드]를 분석하여, 버그를 찾아내는 `pytest` 기반의 테스트 코드를 작성하세요.

[🚨 매우 중요한 규칙 🚨]
- 코드가 실제 DB(MongoDB 등)나 외부 API에 연결을 시도하면 테스트가 멈출 수 있습니다.
- 반드시 파이썬의 `unittest.mock` (또는 `MagicMock`, `patch`)을 사용하여 모든 외부 네트워크, DB 연결, 파일 I/O를 완벽하게 모킹(Mocking)하세요.
- 오직 로직의 정확성, 예외 처리, 데이터 파싱 등에만 집중해서 테스트해야 합니다.
- 테스트 코드는 파일 하나로 실행 가능해야 합니다. """

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(
            content=f"[작업 지시서]\n{issue_description}\n\n[개발된 소스 코드]\n{code_context}"
        ),
    ]

    # 2. LLM 호출하여 테스트 코드 생성
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.1)
    structured_llm = llm.with_structured_output(QATestCode)

    response_data = structured_llm.invoke(messages)

    # Pydantic 파싱 보정 (버전 호환)
    if isinstance(response_data, dict):
        test_content = response_data.get("test_code", "")
    else:
        test_content = response_data.test_code

    # 3. 테스트 코드를 로컬 작업 폴더에 저장
    test_file_path = os.path.join(workspace_dir, "test_ai_qa.py")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print(f"   ✔️ 테스트 코드 생성 완료: {test_file_path}")
    print("🏃‍♂️ [QA] 터미널에서 pytest를 실행하여 코드를 검증합니다...")

    # 4. 파이썬 subprocess를 사용하여 실제로 pytest 실행
    try:
        # pytest 샐행 (현재 작업 디렉토리를 workspace_dir로 설정)
        result = subprocess.run(
            ["pytest", "test_ai_qa.py", "-v"],
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=30,  # 무한 루프 방지를 위해 30초 타임아웃 설정
        )

        # exit code가 0이면 테스트 통과, 아니면 실패
        if result.returncode == 0:
            qa_passed = True
            test_report = (
                "✅ [QA 성공] 모든 테스트를 무사히 통과했습니다.\n\n" + result.stdout
            )
            print("   -> 🎉 QA 테스트 통과!")
        else:
            qa_passed = False
            test_report = (
                "❌ [QA 실패] 테스트 중 에러가 발생했습니다. 아래 로그를 확인하고 코드를 수정하세요.\n\n"
                + result.stdout
                + "\n"
                + result.stderr
            )
            print("   -> 🚨 QA 테스트 실패 (개발자에게 반려합니다)")

    except subprocess.TimeoutExpired:
        qa_passed = False
        test_report = "❌ [QA 실패] 테스트 실행 시간이 30초를 초과하여 강제 종료되었습니다. (무한 루프 또는 데드락 의심)"
        print("   -> ⏰ 타임아웃 에러 발생")
    except Exception as e:
        qa_passed = False
        test_report = (
            f"❌ [QA 시스템 에러] 테스트 실행 중 알 수 없는 오류 발생: {str(e)}"
        )
        print(f"   -> ⚠️ 시스템 에러 발생: {e}")

    print("\n" + "=" * 50)
    print("📊 [QA 리포트 요약]")
    # 로그가 너무 길면 콘솔이 지저분해지므로 500자만 잘라서 보여줍니다.
    print(test_report[:500] + ("..." if len(test_report) > 500 else ""))
    print("=" * 50 + "\n")

    # 5. 상태 업데이트
    return {"test_report": test_report, "qa_passed": qa_passed}
