import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.literacy_tool import explain_financial_term


def test_explain_term_found_glossary():
    """glossary 도메인에 있는 용어(ETF) 검색 시 wiki 페이지 내용이 반환되는지 확인"""
    result = explain_financial_term("ETF")
    assert "ETF" in result
    assert "상장지수펀드" in result


def test_explain_term_found_partial():
    """부분 매칭으로 glossary 용어(기준금리 ← '금리') 검색 시 페이지가 반환되는지 확인"""
    result = explain_financial_term("금리")
    assert "기준금리" in result


def test_explain_term_found_investment_domain():
    """investment 도메인에 있는 용어(채권) 검색 시 wiki 페이지 내용이 반환되는지 확인"""
    result = explain_financial_term("채권")
    assert "채권" in result
    assert "국채" in result


def test_explain_term_not_found():
    """wiki에 없는 용어 검색 시 안내 메시지가 반환되는지 확인"""
    result = explain_financial_term("비트코인추천상품")
    assert "등록된 사전에" in result
    assert "정보가 없습니다" in result


def test_explain_term_not_found_unknown():
    """wiki에 없는 용어(휴면예금)는 not-found 메시지가 반환되는지 확인"""
    result = explain_financial_term("휴면예금")
    assert "등록된 사전에" in result
    assert "정보가 없습니다" in result
