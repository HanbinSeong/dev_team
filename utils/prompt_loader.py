import os
from pathlib import Path

def load_role_prompt(role_name: str, **kwargs) -> str:
    """
    .ai/roles/ 폴더에서 마크다운 템플릿을 읽어와 변수를 치환합니다.
    """
    base_dir = Path(__file__).resolve().parent.parent
    prompt_path = base_dir / ".ai" / "roles" / f"{role_name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {prompt_path}")
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    # kwargs가 제공되면 템플릿 내의 {변수명}을 치환
    if kwargs:
        try:
            template = template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"프롬프트 템플릿 포매팅 에러. 누락된 변수: {e}")
            
    return template