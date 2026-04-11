import json
from pathlib import Path
from typing import Optional

# 프로젝트 루트 디렉토리를 기준으로 데이터 파일 경로 설정
BASE_DIR = Path(__file__).parent.parent
GLOSSARY_PATH = BASE_DIR / "data" / "rag" / "fss_bok_glossary.json"
KRX_ETF_PATH  = BASE_DIR / "data" / "rag" / "krx_etf_info.json"  # scrap_krx.py가 생성

def _load_glossary():
    # 기본 목업 데이터
    mock_data = [
        {"term": "ETF", "official_definition": "주식처럼 거래소에 상장되어 거래되는 펀드입니다."},
        {"term": "정기예금", "official_definition": "일정 기간 돈을 맡기고 이자를 받는 예금입니다."},
        {"term": "RP", "official_definition": "환매조건부채권으로, 일정 기간 후 다시 사는 조건으로 발행하는 채권입니다."}
    ]

    # 1) 금융감독원 파인 사전
    try:
        with open(GLOSSARY_PATH, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
            fss_data = [item for item in data if isinstance(item, dict) and "term" in item]
    except (FileNotFoundError, json.JSONDecodeError):
        fss_data = []

    # 2) KRX ETF 종목 사전 (scrap_krx.py 실행 후 생성)
    try:
        with open(KRX_ETF_PATH, "r", encoding="utf-8") as f:
            krx_data = json.load(f)
            krx_data = [item for item in krx_data if isinstance(item, dict) and "term" in item]
    except (FileNotFoundError, json.JSONDecodeError):
        krx_data = []

    # 우선순위: FSS 용어 > KRX ETF > 목업
    # FSS에 동일 term이 있으면 KRX 항목은 건너뜀 (금융용어 정의가 우선)
    fss_terms = {item["term"] for item in fss_data}
    krx_unique = [item for item in krx_data if item["term"] not in fss_terms]

    return fss_data + krx_unique + mock_data

GLOSSARY_DATA = _load_glossary()

def explain_financial_term(term: str) -> str:
    """주린이(초보 투자자)를 위해 어려운 금융 용어를 '대칭적 해설 원칙'에 따라 설명합니다.
    
    Args:
        term: 설명을 원하는 금융 용어
        
    Returns:
        수익/구조와 리스크가 5:5 비율로 포함된 설명 문자열
    """
    # 정확히 일치하는 용어 검색
    match = next((item for item in GLOSSARY_DATA if item.get("term") == term), None)
    
    # 일치하는 용어가 없으면 부분 검색 시도
    if not match:
        match = next((item for item in GLOSSARY_DATA if term in item.get("term", "")), None)
        
    if match:
        found_term  = match["term"]
        definition  = match.get("official_definition", "정의를 찾을 수 없습니다.")
        risk_level  = match.get("risk_level", "")   # KRX ETF 항목에만 존재
        source      = match.get("source", "")

        # KRX ETF 항목이면 위험등급을 헤더에 표시
        risk_header = f" — 위험등급: {risk_level}" if risk_level else ""

        # '대칭적 해설 원칙' 적용 (수익/구조 5 : 리스크 5)
        # 실제 운영 환경에서는 LLM이 이 가이드를 바탕으로 문장을 생성하게 되며,
        # 도구 레벨에서는 핵심 구조와 리스크 경고를 명시적으로 포함합니다.

        explanation = (
            f"### [{found_term}]{risk_header} 에 대한 설명\n\n"
            f"**1. 수익 및 구조 (수익성):**\n"
            f"{definition}\n\n"
            f"**2. 최대 리스크 (위험성):**\n"
            f"모든 금융 상품은 수익의 기회와 함께 손실의 위험도 가지고 있습니다. "
            f"시장의 변동이나 예상치 못한 경제 상황에 따라 원금의 일부 또는 전부를 잃을 수 있는 '원금 손실 위험(Risk)'이 존재함을 반드시 기억하셔야 합니다. "
            f"특히 '{found_term}' 관련 투자를 결정하시기 전에는 본인의 투자 성향과 손실 감내 수준을 꼭 확인해 보세요."
        )
        return explanation
    
    return f"죄송합니다. '{term}'에 대한 정보를 사전에서 찾을 수 없습니다. 하지만 모든 금융 거래는 수익과 손실의 가능성이 항상 공존한다는 점을 유의해 주세요."
