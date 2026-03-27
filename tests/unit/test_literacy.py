import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.literacy_tool import explain_financial_term

def test_explain_term_exact_match_with_risk():
    """정확한 용어 검색 시 구조와 리스크가 모두 포함되는지 확인"""
    # 휴면예금은 glossary 데이터에 있음
    result = explain_financial_term("휴면예금")
    
    # 구조 설명 포함 여부
    assert "수익 및 구조" in result
    assert "휴면예금" in result
    
    # 리스크 설명 포함 여부 (대칭적 해설 원칙)
    assert "최대 리스크" in result
    assert "원금 손실 위험" in result or "손실" in result

def test_explain_term_mock_data_with_risk():
    """목업 데이터(예: ETF) 검색 시 구조와 리스크가 모두 포함되는지 확인"""
    # ETF가 실제 데이터에 없을 수도 있으므로 (부분 일치로 찾거나 목업으로 찾음)
    result = explain_financial_term("ETF")
    
    assert "수익 및 구조" in result
    assert "최대 리스크" in result
    assert "위험" in result

def test_explain_term_not_found_with_warning():
    """존재하지 않는 용어 검색 시 에러 메시지와 함께 리스크 유의사항이 포함되는지 확인"""
    result = explain_financial_term("비트코인추천상품")
    
    assert "사전에서 찾을 수 없습니다" in result
    # 검색 실패 시에도 리스크 공통 문구 포함 여부 확인
    assert "수익과 손실의 가능성이 항상 공존" in result

def test_explain_term_partial_match_with_risk():
    """부분 일치 검색 시에도 대칭적 해설 원칙이 적용되는지 확인"""
    # '퇴직' 키워드로 '퇴직연금' 관련 용어 검색 시도
    result = explain_financial_term("퇴직")
    
    assert "수익 및 구조" in result
    assert "최대 리스크" in result
    assert "퇴직" in result
