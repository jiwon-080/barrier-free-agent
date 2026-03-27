import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가하여 app 모듈을 불러올 수 있게 함
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.guardrail_tool import check_investment_guardrail

def test_guardrail_safe_message():
    """안전한 메시지가 통과되는지 확인"""
    text = "정기예금 금리는 연 3.5%입니다."
    result = check_investment_guardrail(text)
    
    assert result["is_safe"] is True
    assert result["message"] == text

def test_guardrail_prohibited_keyword_recommend():
    """'추천' 키워드 감지 확인"""
    text = "이 상품을 강력 추천합니다."
    result = check_investment_guardrail(text)
    
    assert result["is_safe"] is False
    assert "추천" in result["detected_keywords"]
    assert "투자 권유를 할 수 없으며" in result["message"]

def test_guardrail_prohibited_keyword_guarantee():
    """'수익 보장' 키워드 감지 확인"""
    text = "이 펀드는 원금 보장과 높은 수익 보장을 약속합니다."
    result = check_investment_guardrail(text)
    
    assert result["is_safe"] is False
    assert "원금 보장" in result["detected_keywords"]
    assert "수익 보장" in result["detected_keywords"]
    assert "투자 권유를 할 수 없으며" in result["message"]

def test_guardrail_prohibited_keyword_join():
    """'가입하세요' 키워드 감지 확인"""
    text = "지금 바로 이 보험에 가입하세요!"
    result = check_investment_guardrail(text)
    
    assert result["is_safe"] is False
    assert "가입하세요" in result["detected_keywords"]

def test_guardrail_prohibited_keyword_absolute():
    """'무조건', '확실한' 키워드 감지 확인"""
    text = "무조건 돈을 벌 수 있는 확실한 기회입니다."
    result = check_investment_guardrail(text)
    
    assert result["is_safe"] is False
    assert "무조건" in result["detected_keywords"]
    assert "확실한" in result["detected_keywords"]
