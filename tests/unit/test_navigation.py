import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.navigation_tool import navigate_ui


def test_navigate_irp():
    result = navigate_ui("IRP 가입하고 싶어")
    assert result["type"] == "navigation"
    assert "route" in result
    assert "consent_message" in result
    assert "voice_guide" in result


def test_navigate_deposit():
    result = navigate_ui("예금 가입 방법 알려줘")
    assert result["type"] == "suggestion"
    assert "voice_guide" in result


def test_navigate_high_risk_etf():
    """ETF 가입 시 hold 상태와 투자 성향 진단 안내가 반환되는지 확인"""
    result = navigate_ui("ETF 가입하고 싶어요")
    assert result["status"] == "hold"
    assert result["routing"] == "투자 성향 진단 메뉴"
    assert "원금 손실 위험" in result["voice_guide"]
    assert "투자 성향" in result["voice_guide"]


def test_navigate_high_risk_fund():
    """펀드 매수 시 hold 상태가 반환되는지 확인"""
    result = navigate_ui("좋은 펀드 하나 매수해줘")
    assert result["status"] == "hold"
    assert "원금 손실 위험" in result["voice_guide"]


def test_navigate_unknown():
    result = navigate_ui("로또 번호 알려줘")
    assert result["type"] == "error"
