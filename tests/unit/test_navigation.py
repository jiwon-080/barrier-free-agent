import pytest
import sys
import os

# app 폴더를 경로에 추가하고, 불필요한 agent 임포트를 피하기 위해
# 모듈을 직접 로드하거나 mocking을 고려합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_navigate_irp():
    from app.navigation_tool import navigate_ui
    result = navigate_ui("IRP 가입하고 싶어")
    assert result["type"] == "navigation"
    assert len(result["path"]) == 5
    assert "visual_instructions" in result
    assert "voice_guide" in result
    assert "어르신" in result["voice_guide"]
    assert "IRP" in result["voice_guide"]

def test_navigate_deposit():
    from app.navigation_tool import navigate_ui
    result = navigate_ui("예금 가입 방법 알려줘")
    assert result["type"] == "suggestion"
    assert result["suggestion_action"] == "큰글 모드 전환"
    assert "voice_guide" in result
    assert "큰글 모드" in result["voice_guide"]

def test_navigate_unknown():
    from app.navigation_tool import navigate_ui
    result = navigate_ui("로또 번호 알려줘")
    assert result["type"] == "error"
    assert "message" in result
