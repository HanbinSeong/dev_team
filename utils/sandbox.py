import os
import docker
from docker.errors import ContainerError, ImageNotFound, APIError

def run_tests_in_sandbox(workspace_dir: str, timeout_seconds: int = 30) -> tuple[int, str]:
    """
    격리된 Docker 컨테이너 내에서 pytest를 실행하고 결과를 반환합니다.
    """
    try:
        client = docker.from_env()
    except Exception as e:
        return 1, f"[Sandbox Error] Docker 데몬 연결 실패:\n{e}"

    abs_workspace = os.path.abspath(workspace_dir)

    try:
        container = client.containers.run(
            image="python:3.11-slim",
            command="sh -c 'pip install pytest pytest-mock && pytest test_ai_qa.py -v'",
            volumes={abs_workspace: {'bind': '/workspace', 'mode': 'rw'}},
            working_dir="/workspace",
            detach=True,
            network_mode="none",
            mem_limit="256m",
            cpu_quota=50000,
            cpu_period=100000
        )

        result = container.wait(timeout=timeout_seconds)
        logs = container.logs().decode('utf-8')
        exit_code = result.get('StatusCode', 1)

        container.remove(force=True)
        return exit_code, logs

    except ImageNotFound as e:
        return 1, f"[Sandbox Error] 지정된 Docker 이미지를 찾을 수 없습니다: {e}"
    
    except ContainerError as e:
        return 1, f"[Sandbox Error] 컨테이너가 비정상 종료되었습니다: {e}"
        
    except APIError as e:
        return 1, f"[Sandbox Error] Docker API 서버 통신 중 오류가 발생했습니다: {e}"
        
    except Exception as e:
        # 타임아웃(ReadTimeout) 또는 기타 예기치 않은 오류 처리
        if 'container' in locals():
            try:
                container.remove(force=True)
            except Exception:
                pass
        return 1, f"[Sandbox Error] 샌드박스 실행 중 타임아웃 또는 알 수 없는 오류 발생:\n{str(e)}"