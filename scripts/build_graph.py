"""
GraphRAG 지식 그래프 빌드 스크립트

노드 5종:
  TermNode    - fss_bok_glossary.json (1,191개 금융 용어)
  ProductNode - fss_product.json (예금/적금 상품)
  RouteNode   - navigation_tool.py navigation_map
  RegNode     - data/regulations.json
  MacroNode   - 거시경제 지표 (기준금리/환율/CPI) — 관계만 저장, 수치는 실시간 API

출력: data/rag/knowledge_graph.pkl
"""

import json
import pickle
import sys
from pathlib import Path

import networkx as nx

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GRAPH_PATH = DATA_DIR / "rag" / "knowledge_graph.pkl"


# ── navigation_tool.py의 navigation_map을 그대로 복사 (RouteNode 원천) ──────
# 각 route_key → trigger_terms: 이 용어들이 해당 화면으로 이어짐
ROUTE_META = {
    "financial_products/demand_deposit": {
        "label": "입출금 상품 화면",
        "trigger_terms": ["입출금", "보통예금", "자유입출금"],
    },
    "financial_products/deposit": {
        "label": "예금 상품 화면",
        "trigger_terms": ["예금", "정기예금", "정기적금"],
    },
    "financial_products/saving": {
        "label": "적금 상품 화면",
        "trigger_terms": ["적금", "자유적금", "정액적금"],
    },
    "financial_products/housing_subscription": {
        "label": "주택청약 화면",
        "trigger_terms": ["주택청약", "청약", "청약저축"],
    },
    "financial_products/fund": {
        "label": "펀드 상품 화면",
        "trigger_terms": ["펀드", "공모펀드", "사모펀드"],
    },
    "financial_products/fund/investment_profile": {
        "label": "투자자 성향 진단 화면",
        "trigger_terms": ["투자자성향", "투자성향", "적합성"],
        "guardrail": True,
    },
    "financial_products/fund/trust/etf": {
        "label": "ETF 화면",
        "trigger_terms": ["ETF", "상장지수펀드", "이티에프"],
        "guardrail": True,
    },
    "financial_products/loan": {
        "label": "대출 상품 화면",
        "trigger_terms": ["대출", "신용대출", "담보대출", "주택담보대출"],
    },
    "financial_products/foreign_exchange": {
        "label": "외환 화면",
        "trigger_terms": ["외환", "환전", "외화"],
    },
    "financial_products/retirement_pension": {
        "label": "퇴직연금 화면",
        "trigger_terms": ["퇴직연금", "IRP", "DC형", "DB형", "개인형퇴직연금", "아이알피"],
    },
    "financial_products/trust": {
        "label": "신탁 상품 화면",
        "trigger_terms": ["신탁", "금전신탁"],
    },
    "financial_products/isa": {
        "label": "ISA 화면",
        "trigger_terms": ["ISA", "개인종합자산관리계좌"],
    },
    "financial_products/insurance": {
        "label": "보험 상품 화면",
        "trigger_terms": ["보험", "생명보험", "손해보험"],
    },
    "financial_products/gold_silver": {
        "label": "골드/실버 화면",
        "trigger_terms": ["골드", "금", "실버", "은"],
    },
    "my_assets": {
        "label": "내 자산 현황 화면",
        "trigger_terms": ["내자산", "자산현황", "포트폴리오"],
    },
    "inquiry/all_accounts": {
        "label": "전체 계좌 조회 화면",
        "trigger_terms": ["전체계좌조회", "계좌조회"],
    },
    "transfer/account": {
        "label": "계좌이체 화면",
        "trigger_terms": ["이체", "계좌이체", "송금"],
    },
}

# ── 약어·음독 alias → 사전 풀네임 매핑 ─────────────────────────────────────
# alias 노드는 target 노드의 definition + 모든 엣지를 그대로 상속받음
ALIAS_MAP: dict[str, str] = {
    # 영문 약어 → 사전 풀네임 (사전 키 띄어쓰기 그대로)
    "IRP":  "개인퇴직계좌",
    "ETF":  "상장지수펀드(ETF)",
    "DC형": "확정기여형 퇴직연금",
    "DB형": "확정급여형 퇴직연금",
    "ISA":  "개인종합자산관리계좌",
    "MMF":  "머니마켓펀드(MMF)",
    # 음독 alias → 사전 풀네임 (직접 매핑, 체인 없음)
    "아이알피":    "개인퇴직계좌",
    "이티에프":    "상장지수펀드(ETF)",
    "아이에스에이": "개인종합자산관리계좌",
}

# 거시경제 지표 노드 (수치 없음, 관계만)
MACRO_NODES = [
    {
        "id": "macro_기준금리",
        "name": "기준금리",
        "description": "한국은행이 결정하는 정책금리. 예금/대출 금리에 영향.",
        "affects": ["예금", "적금", "대출", "채권"],
    },
    {
        "id": "macro_환율",
        "name": "환율",
        "description": "원화와 외국 통화의 교환 비율.",
        "affects": ["외환", "ETF", "상장지수펀드(ETF)", "펀드"],
    },
    {
        "id": "macro_CPI",
        "name": "소비자물가지수",
        "description": "가계가 구입하는 상품과 서비스의 가격 변동을 측정하는 지수.",
        "affects": ["기준금리", "채권"],
    },
]


def _add_term_nodes(G: nx.DiGraph, glossary_path: Path) -> None:
    with open(glossary_path, encoding="utf-8-sig") as f:
        glossary = [item for item in json.load(f) if isinstance(item, dict) and "term" in item]

    for item in glossary:
        node_id = f"term_{item['term']}"
        G.add_node(
            node_id,
            node_type="TermNode",
            name=item["term"],
            definition=item.get("official_definition", ""),
            source=item.get("source", ""),
        )
        # related_terms → RELATED_TO 엣지 (양방향)
        for related in item.get("related_terms", []):
            if not related.strip():
                continue
            related_id = f"term_{related.strip()}"
            if not G.has_node(related_id):
                G.add_node(related_id, node_type="TermNode", name=related.strip(), definition="", source="")
            G.add_edge(node_id, related_id, relation="RELATED_TO")
            G.add_edge(related_id, node_id, relation="RELATED_TO")

    print(f"  TermNode: {len(glossary)}개 추가")


def _add_product_nodes(G: nx.DiGraph, product_path: Path) -> None:
    with open(product_path, encoding="utf-8") as f:
        data = json.load(f)

    count = 0
    for category, products in data.items():
        if not isinstance(products, list):
            continue
        # 카테고리에서 상품 유형 이름 추출 (deposit_bank → 예금)
        product_type = "예금" if "deposit" in category else "적금"
        route_key = (
            "financial_products/deposit"
            if product_type == "예금"
            else "financial_products/saving"
        )

        for p in products:
            prod_id = f"product_{p['fin_prdt_cd']}"
            best_rate = max(
                (opt.get("intr_rate2") or opt.get("intr_rate") or 0 for opt in p.get("options", [])),
                default=0,
            )
            G.add_node(
                prod_id,
                node_type="ProductNode",
                name=p["fin_prdt_nm"],
                bank=p.get("kor_co_nm", ""),
                product_type=product_type,
                best_rate=best_rate,
                join_way=p.get("join_way", ""),
            )
            count += 1

            # ProductNode → RouteNode
            route_node_id = f"route_{route_key}"
            if G.has_node(route_node_id):
                G.add_edge(prod_id, route_node_id, relation="LEADS_TO")

            # TermNode(예금/적금) → ProductNode
            type_term_id = f"term_{product_type}"
            if not G.has_node(type_term_id):
                G.add_node(type_term_id, node_type="TermNode", name=product_type, definition="", source="")
            G.add_edge(type_term_id, prod_id, relation="HAS_PRODUCT")

    print(f"  ProductNode: {count}개 추가")


def _add_route_nodes(G: nx.DiGraph) -> None:
    for route_key, meta in ROUTE_META.items():
        route_id = f"route_{route_key}"
        G.add_node(
            route_id,
            node_type="RouteNode",
            name=meta["label"],
            route_key=route_key,
            label=meta["label"],
            guardrail=meta.get("guardrail", False),
        )
        for term_name in meta.get("trigger_terms", []):
            term_id = f"term_{term_name}"
            if not G.has_node(term_id):
                G.add_node(term_id, node_type="TermNode", name=term_name, definition="", source="")
            relation = "TRIGGERS_GUARDRAIL" if meta.get("guardrail") else "LEADS_TO"
            G.add_edge(term_id, route_id, relation=relation)

    print(f"  RouteNode: {len(ROUTE_META)}개 추가")


def _add_reg_nodes(G: nx.DiGraph, reg_path: Path) -> None:
    if not reg_path.exists():
        print("  RegNode: regulations.json 없음, 건너뜀")
        return

    with open(reg_path, encoding="utf-8") as f:
        regulations = json.load(f)

    for reg in regulations:
        reg_id = f"reg_{reg['id']}"
        summary = reg.get("summary", "")
        details = reg.get("details", {})
        # details를 문자열로 직렬화해 content 필드에 저장
        content = summary + " | " + json.dumps(details, ensure_ascii=False) if details else summary

        G.add_node(
            reg_id,
            node_type="RegNode",
            name=reg["name"],
            content=content,
            source=reg.get("source", ""),
        )

        # related_products → TermNode GOVERNED_BY RegNode
        for term_name in reg.get("related_products", []):
            term_id = f"term_{term_name}"
            if not G.has_node(term_id):
                G.add_node(term_id, node_type="TermNode", name=term_name, definition="", source="")
            G.add_edge(term_id, reg_id, relation="GOVERNED_BY")

        # related_routes: RegNode → RouteNode (LEADS_TO) + RouteNode → RegNode (GOVERNED_BY)
        for route_key in reg.get("related_routes", []):
            route_id = f"route_{route_key}"
            if G.has_node(route_id):
                G.add_edge(reg_id, route_id, relation="LEADS_TO")
                G.add_edge(route_id, reg_id, relation="GOVERNED_BY")

    print(f"  RegNode: {len(regulations)}개 추가")


def _apply_aliases(G: nx.DiGraph) -> None:
    """ALIAS_MAP의 각 alias 노드에 target 노드의 definition + 엣지를 복사합니다.

    - alias 노드가 없으면 새로 생성
    - alias 노드가 이미 definition을 갖고 있으면 덮어쓰지 않음
    - target의 모든 outgoing/incoming 엣지를 alias에도 추가
    """
    applied = 0
    for alias, target_term in ALIAS_MAP.items():
        target_id = f"term_{target_term}"
        alias_id  = f"term_{alias}"

        if not G.has_node(target_id):
            continue  # 사전에 target이 없으면 건너뜀

        target_data = G.nodes[target_id]

        # alias 노드 생성 또는 definition만 업데이트
        if not G.has_node(alias_id):
            G.add_node(alias_id, node_type="TermNode", name=alias,
                       definition=target_data.get("definition", ""),
                       source=target_data.get("source", ""))
        else:
            # 기존 노드에 definition이 비어있을 때만 채움
            if not G.nodes[alias_id].get("definition"):
                G.nodes[alias_id]["definition"] = target_data.get("definition", "")

        # target의 outgoing 엣지 복사 (alias → neighbor)
        for _, neighbor, edge_data in G.out_edges(target_id, data=True):
            if not G.has_edge(alias_id, neighbor):
                G.add_edge(alias_id, neighbor, **edge_data)

        # target의 incoming 엣지 복사 (predecessor → alias)
        for predecessor, _, edge_data in G.in_edges(target_id, data=True):
            if not G.has_edge(predecessor, alias_id):
                G.add_edge(predecessor, alias_id, **edge_data)

        applied += 1

    print(f"  Alias 적용: {applied}개 ({list(ALIAS_MAP.keys())})")


def _add_macro_nodes(G: nx.DiGraph) -> None:
    for macro in MACRO_NODES:
        G.add_node(
            macro["id"],
            node_type="MacroNode",
            name=macro["name"],
            description=macro["description"],
        )
        for term_name in macro.get("affects", []):
            term_id = f"term_{term_name}"
            if not G.has_node(term_id):
                G.add_node(term_id, node_type="TermNode", name=term_name, definition="", source="")
            G.add_edge(macro["id"], term_id, relation="AFFECTS")

    print(f"  MacroNode: {len(MACRO_NODES)}개 추가")


def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    print("=== 지식 그래프 구축 시작 ===")

    _add_term_nodes(G, DATA_DIR / "rag" / "fss_bok_glossary.json")
    _add_route_nodes(G)
    _add_reg_nodes(G, DATA_DIR / "rag" / "regulations.json")
    _add_product_nodes(G, DATA_DIR / "rag" / "fss_product.json")
    _add_macro_nodes(G)
    _apply_aliases(G)

    # 고립 노드 수 (엣지가 없는 노드)
    isolated = [n for n in G.nodes if G.degree(n) == 0]

    print(f"\n구축 완료:")
    print(f"  노드: {G.number_of_nodes():,}개")
    print(f"  엣지: {G.number_of_edges():,}개")
    print(f"  고립 노드: {len(isolated)}개")

    node_type_counts = {}
    for _, data in G.nodes(data=True):
        t = data.get("node_type", "Unknown")
        node_type_counts[t] = node_type_counts.get(t, 0) + 1
    for t, cnt in sorted(node_type_counts.items()):
        print(f"  {t}: {cnt}개")

    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(G, f)
    print(f"\n저장 완료: {GRAPH_PATH}")
    return G


if __name__ == "__main__":
    build_graph()
