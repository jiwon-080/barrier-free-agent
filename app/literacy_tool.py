import json
from pathlib import Path
from typing import Optional

from google.adk.tools.tool_context import ToolContext

# 프로젝트 루트 디렉토리를 기준으로 데이터 파일 경로 설정
BASE_DIR = Path(__file__).parent.parent
GLOSSARY_PATH = BASE_DIR / "data" / "rag" / "fss_bok_glossary.json"
KRX_ETF_PATH  = BASE_DIR / "data" / "rag" / "krx_etf_info.json"  # scrap_krx.py가 생성

# GraphRAG 사용 가능 여부 (knowledge_graph.pkl 존재 시 활성화)
_GRAPH_AVAILABLE = (BASE_DIR / "data" / "rag" / "knowledge_graph.pkl").exists()

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

def explain_financial_term(term: str, tool_context: ToolContext) -> str:
    """사용자의 금융이해도(literacy_level)에 맞춰 금융 용어를 설명합니다.

    GraphRAG가 활성화된 경우 지식 그래프 기반 multi-hop 탐색 결과를 우선 사용하고,
    없을 경우 기존 키워드 매칭 방식으로 폴백합니다.

    Args:
        term: 설명을 원하는 금융 용어

    Returns:
        수익/구조와 리스크가 5:5 비율로 포함된 설명 문자열
    """
    literacy_level = tool_context.state.get("user:literacy_level", "일반")

    # ── 1) GraphRAG 우선 탐색 ──────────────────────────────────────────────
    if _GRAPH_AVAILABLE:
        try:
            from app.graph_rag_tool import graph_search
            gr = graph_search(term, literacy_level=literacy_level)
            if gr.get("matched_term"):
                return _format_graph_result(gr, literacy_level)
        except Exception:
            pass  # 그래프 오류 시 폴백

    # ── 2) 폴백: 기존 키워드 매칭 ─────────────────────────────────────────
    return _legacy_keyword_search(term, literacy_level)


def _format_graph_result(gr: dict, literacy_level: str = "일반") -> str:
    """GraphRAG 탐색 결과를 literacy_level에 맞게 포맷합니다."""
    found_term = gr["matched_term"]
    definition = gr["definition"] or "정의를 찾을 수 없습니다."
    related = ", ".join(gr["related_terms"]) if gr["related_terms"] else ""
    reg_hint = gr["regulation_hint"] or ""
    route = gr["suggested_route"] or ""
    guardrail = gr["guardrail"]

    # 기초: 정의 앞 150자만, 전문가: 전체
    if literacy_level == "기초":
        definition = definition[:150] + ("..." if len(definition) > 150 else "")

    lines = [
        f"### [{found_term}] 에 대한 설명\n",
        f"**1. 수익 및 구조 (수익성):**\n{definition}\n",
    ]

    # 전문가에게만 규정 힌트 표시
    if reg_hint and literacy_level == "전문가":
        lines.append(f"**관련 규정:** {reg_hint}\n")
    elif reg_hint and literacy_level == "일반":
        short_hint = reg_hint[:200] + ("..." if len(reg_hint) > 200 else "")
        lines.append(f"**관련 규정:** {short_hint}\n")

    if related:
        lines.append(f"**연관 개념:** {related}\n")

    if route:
        lines.append(f"**앱 화면 안내:** '{route}' 화면에서 확인하실 수 있습니다.\n")

    if guardrail:
        risk_msg = "⚠️ 이 상품은 투자 성향 진단이 필요한 고위험 상품입니다. 투자 전 반드시 성향 진단을 받으시기 바랍니다."
    elif literacy_level == "기초":
        risk_msg = f"'{found_term}'은(는) 잘못하면 원금을 잃을 수 있는 상품입니다. 가입 전 충분히 알아보시기 바랍니다."
    else:
        risk_msg = (
            f"모든 금융 상품은 수익의 기회와 함께 손실의 위험도 가지고 있습니다. "
            f"시장의 변동이나 예상치 못한 경제 상황에 따라 원금의 일부 또는 전부를 잃을 수 있는 "
            f"'원금 손실 위험(Risk)'이 존재함을 반드시 기억하셔야 합니다. "
            f"특히 '{found_term}' 관련 투자를 결정하시기 전에는 본인의 투자 성향과 손실 감내 수준을 꼭 확인하시기 바랍니다."
        )
    lines.append(f"**2. 최대 리스크 (위험성):**\n{risk_msg}")

    return "\n".join(lines)


def _legacy_keyword_search(term: str, literacy_level: str = "일반") -> str:
    """기존 키워드 매칭 방식 (GraphRAG 폴백)"""
    match = next((item for item in GLOSSARY_DATA if item.get("term") == term), None)
    if not match:
        match = next((item for item in GLOSSARY_DATA if term in item.get("term", "")), None)

    if match:
        found_term = match["term"]
        definition = match.get("official_definition", "정의를 찾을 수 없습니다.")
        risk_level = match.get("risk_level", "")
        risk_header = f" — 위험등급: {risk_level}" if risk_level else ""

        if literacy_level == "기초":
            definition = definition[:150] + ("..." if len(definition) > 150 else "")
            risk_msg = f"'{found_term}'은(는) 잘못하면 원금을 잃을 수 있는 상품입니다. 가입 전 충분히 알아보시기 바랍니다."
        else:
            risk_msg = (
                f"모든 금융 상품은 수익의 기회와 함께 손실의 위험도 가지고 있습니다. "
                f"시장의 변동이나 예상치 못한 경제 상황에 따라 원금의 일부 또는 전부를 잃을 수 있는 "
                f"'원금 손실 위험(Risk)'이 존재함을 반드시 기억하셔야 합니다. "
                f"특히 '{found_term}' 관련 투자를 결정하시기 전에는 본인의 투자 성향과 손실 감내 수준을 꼭 확인하시기 바랍니다."
            )

        return (
            f"### [{found_term}]{risk_header} 에 대한 설명\n\n"
            f"**1. 수익 및 구조 (수익성):**\n"
            f"{definition}\n\n"
            f"**2. 최대 리스크 (위험성):**\n"
            f"{risk_msg}"
        )

    return (
        f"죄송합니다. '{term}'에 대한 정보를 사전에서 찾을 수 없습니다. "
        f"하지만 모든 금융 거래는 수익과 손실의 가능성이 항상 공존한다는 점을 유의하시기 바랍니다."
    )
