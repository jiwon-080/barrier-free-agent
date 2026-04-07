# GraphRAG 사전 구축 가이드

> 배리어프리 에이전트를 위한 금융 지식 그래프 구축 실전 가이드
> 목표: 단순 키워드 검색 → 개념 간 관계 기반 다중 홉 추론으로 전환

---

## 0. 전체 파이프라인 개요

```
[데이터 수집]         [그래프 구축]         [검색 엔진]           [에이전트 통합]
  크롤링/파싱    →   노드/엣지 생성    →   임베딩 + 탐색    →   graph_rag_tool.py
  fss_glossary       NetworkX Graph        유사도 검색             literacy_tool
  NH 상품정보         JSON 직렬화           다중 홉 추론            navigation 연동
  세법 조항
```

---

## 1. 데이터 수집

### 1-1. 이미 확보된 데이터

| 파일 | 내용 | 사용 방식 |
|---|---|---|
| `data/rag/fss_glossary.json` | 금융감독원 파인 금융용어사전 전체 | TermNode의 주 원천 |
| `nh_menu_analysis.md` | NH올원뱅크 메뉴 트리 + 클릭 뎁스 분석 | RouteNode 원천 |
| `app/navigation_tool.py` | 실제 라우트 맵 (`irp_tax_saving` 등) | RouteNode + LEADS_TO 엣지 |

### 1-2. 금융감독원 파인 (FSS Fine) 크롤링

**대상 URL**: `https://fine.fss.or.kr/fine/fnctip/fncDicary/list.do?menuNo=900021`

**크롤링 전략**: 해당 사이트는 목록이 여러 페이지로 나뉘어 있고 JavaScript 렌더링이 필요할 수 있습니다.

```python
# scripts/crawl_fss_glossary.py
import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://fine.fss.or.kr"
LIST_URL = f"{BASE_URL}/fine/fnctip/fncDicary/list.do"
DETAIL_URL = f"{BASE_URL}/fine/fnctip/fncDicary/view.do"

def fetch_glossary_list(page: int) -> list[dict]:
    """용어사전 목록 페이지에서 용어 링크를 수집합니다."""
    params = {"menuNo": "900021", "pageIndex": page}
    headers = {"User-Agent": "Mozilla/5.0 (for academic/research use)"}
    
    resp = requests.get(LIST_URL, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    terms = []
    # 실제 CSS selector는 페이지 구조 확인 후 수정
    for row in soup.select("table.tbl_type tbody tr"):
        cols = row.find_all("td")
        if len(cols) >= 2:
            terms.append({
                "term": cols[1].get_text(strip=True),
                "link": cols[1].find("a")["href"] if cols[1].find("a") else None
            })
    return terms

def fetch_term_detail(term_id: str) -> dict:
    """용어 상세 페이지에서 정의 및 관련 용어를 수집합니다."""
    params = {"menuNo": "900021", "fncDicaryId": term_id}
    headers = {"User-Agent": "Mozilla/5.0 (for academic/research use)"}
    
    resp = requests.get(DETAIL_URL, params=params, headers=headers, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # 관련 용어 링크 파싱 (RELATED_TO 엣지 생성에 사용)
    related = [a.get_text(strip=True) 
               for a in soup.select(".related_terms a")]
    
    return {
        "official_definition": soup.select_one(".view_content").get_text(strip=True),
        "related_terms": related,  # → RELATED_TO 엣지 원천
        "source": "금융감독원 파인"
    }

# 실행: python -m scripts.crawl_fss_glossary --pages 1-50 --output data/rag/fss_glossary_full.json
```

> **주의**: 크롤링 전 `robots.txt` 확인 필수. 요청 간격 1~2초 권장 (`time.sleep(1.5)`). 학술/비상업적 목적임을 User-Agent에 명시.

### 1-3. NH농협 퇴직연금 상품 정보 수집

**방법**: 공개 상품안내서(PDF) + 공식 웹페이지 스크래핑

```python
# scripts/crawl_nh_products.py
# 대상: NH농협은행 퇴직연금 공개 상품 안내 페이지
# 수집 대상 정보:
#   - 상품명 (개인형IRP 세액공제용, DC형 퇴직연금 등)
#   - 운용 가능 상품군 (예금/펀드/ETF/디폴트옵션)
#   - 가입 조건, 한도, 세액공제 요건
#   - 위험 등급 (보통/높음/매우높음)

NH_PRODUCTS = [
    {
        "name": "개인형IRP 세액공제용",
        "route": "irp_tax_saving",
        "risk_level": "LOW",          # 예금 중심 운용 시
        "tax_benefit": "연 900만원 한도 세액공제 (연금저축 포함)",
        "eligible": "소득이 있는 개인 누구나",
        "related_terms": ["IRP", "세액공제", "연금계좌", "퇴직연금"],
        "governed_by": ["조세특례제한법_제59조의3", "근로자퇴직급여보장법"]
    },
    {
        "name": "개인형IRP 퇴직금수령용",
        "route": "irp_new",
        "risk_level": "MEDIUM",
        "eligible": "퇴직자 (퇴직급여 의무 이전)",
        "related_terms": ["IRP", "퇴직금", "퇴직급여"],
        "governed_by": ["근로자퇴직급여보장법_제24조"]
    },
    {
        "name": "확정기여형(DC) 퇴직연금",
        "route": "retirement_pension",
        "risk_level": "MEDIUM",
        "eligible": "DC형 가입 사업장 근로자",
        "related_terms": ["DC", "퇴직연금", "확정기여형"],
        "governed_by": ["근로자퇴직급여보장법"]
    },
]
# data/nh_products.json으로 저장
```

### 1-4. 세법 규정 데이터 (수동 정리)

연금 세액공제 관련 핵심 규정은 크롤링보다 **수동 정리**가 정확합니다.

```json
// data/regulations.json
[
  {
    "id": "tax_benefit_irp_900",
    "name": "IRP 세액공제 한도",
    "content": "연금계좌(IRP + 연금저축) 납입액 합계 연 900만원 한도로 세액공제. 총급여 5,500만원 이하: 16.5%, 초과: 13.2%",
    "law": "조세특례제한법 제59조의3",
    "related_products": ["개인형IRP 세액공제용"],
    "related_terms": ["세액공제", "IRP", "연금저축계좌"]
  },
  {
    "id": "tax_benefit_pension_600",
    "name": "연금저축 세액공제 한도",
    "content": "연금저축만으로는 연 600만원 한도. IRP 추가 시 합산 900만원까지 인정.",
    "law": "조세특례제한법 제59조의3",
    "related_terms": ["연금저축계좌", "세액공제", "IRP"]
  },
  {
    "id": "guardrail_investment_advice",
    "name": "금융소비자보호법 투자권유 금지",
    "content": "금융소비자에게 특정 금융상품 투자를 권유하려면 적합성 원칙 준수 필요. 부적합 상품 권유 금지.",
    "law": "금융소비자보호법 제17조",
    "related_terms": ["투자권유", "적합성 원칙", "ETF", "펀드"]
  }
]
```

---

## 2. 그래프 스키마 설계

### 2-1. 노드(Node) 타입

```
TermNode
  - id: str          # 고유 ID (예: "term_IRP")
  - name: str        # 표시명 (예: "IRP")
  - aliases: list    # 동의어 (예: ["개인형퇴직연금계좌", "Individual Retirement Pension"])
  - definition: str  # 금감원 공식 정의
  - simple_def: str  # 에이전트가 사용하는 쉬운 설명
  - source: str      # "금융감독원 파인"

ProductNode
  - id: str          # "product_irp_tax"
  - name: str        # "개인형IRP 세액공제용"
  - route: str       # "irp_tax_saving" (navigation_tool 라우트와 직접 연동)
  - risk_level: str  # "LOW" / "MEDIUM" / "HIGH"
  - eligible: str    # 가입 대상
  - tax_benefit: str # 세액공제 혜택 요약

RouteNode
  - id: str          # "route_irp_tax_saving"
  - route_key: str   # "irp_tax_saving" (demo.py session_state와 일치)
  - label: str       # "개인형 IRP 세액공제용 화면"
  - depth: int       # 앱 내 메뉴 깊이 (1~5)
  - consent_message: str  # 동의 메시지
  - voice_guide: str      # 음성 안내문

RegNode
  - id: str          # "reg_tax_benefit_irp_900"
  - name: str        # "IRP 세액공제 한도"
  - content: str     # 규정 내용
  - law: str         # 법령명
```

### 2-2. 엣지(Edge) 타입

| 엣지 | 방향 | 예시 |
|---|---|---|
| `RELATED_TO` | 양방향 | `IRP` ↔ `퇴직연금` |
| `SYNONYM_OF` | 양방향 | `ETF` ↔ `상장지수펀드` |
| `LEADS_TO` | 단방향 | `TermNode(IRP)` → `RouteNode(irp_tax_saving)` |
| `HAS_PRODUCT` | 단방향 | `TermNode(IRP)` → `ProductNode(개인형IRP 세액공제용)` |
| `GOVERNED_BY` | 단방향 | `ProductNode` → `RegNode` |
| `RISK_LEVEL` | 단방향 | `ProductNode(ETF운용)` → `HIGH` (레이블) |
| `TRIGGERS_GUARDRAIL` | 단방향 | `TermNode(ETF)` → `RouteNode(investment_diagnosis)` |

### 2-3. 그래프 시각화 미리보기

```
[TermNode: IRP]
    │── SYNONYM_OF ──▶ [TermNode: 개인형퇴직연금계좌]
    │── RELATED_TO ──▶ [TermNode: 세액공제]
    │                       └── GOVERNED_BY ──▶ [RegNode: 세액공제한도 900만원]
    │── HAS_PRODUCT ─▶ [ProductNode: 개인형IRP 세액공제용]
    │                       └── LEADS_TO ──────▶ [RouteNode: irp_tax_saving]
    └── RELATED_TO ──▶ [TermNode: 퇴직연금]
                            └── RELATED_TO ──▶ [TermNode: DC]

[TermNode: ETF]
    │── RISK_LEVEL ──▶ HIGH
    └── TRIGGERS_GUARDRAIL ─▶ [RouteNode: investment_diagnosis]
```

---

## 3. 그래프 구축 (NetworkX)

### 3-1. 환경 설정

```bash
uv add networkx sentence-transformers
# 임베딩을 Gemini API로 할 경우: google-generativeai는 이미 설치됨
```

### 3-2. 그래프 빌드 스크립트

```python
# scripts/build_graph.py
import json
import networkx as nx
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
GRAPH_PATH = DATA_DIR / "rag" / "knowledge_graph.pkl"

def build_graph() -> nx.DiGraph:
    G = nx.DiGraph()

    # ── 1. TermNode: fss_glossary.json 로드 ──────────────────────────────
    with open(DATA_DIR / "rag" / "fss_glossary.json", encoding="utf-8-sig") as f:
        glossary = [item for item in json.load(f) 
                    if isinstance(item, dict) and "term" in item]

    for item in glossary:
        node_id = f"term_{item['term']}"
        G.add_node(node_id,
                   type="TermNode",
                   name=item["term"],
                   definition=item.get("official_definition", ""),
                   source=item.get("source", "금융감독원 파인"),
                   aliases=[])
        
        # 동의어 처리 (aliases 필드가 있을 경우)
        for alias in item.get("aliases", []):
            alias_id = f"term_{alias}"
            G.add_node(alias_id, type="TermNode", name=alias)
            G.add_edge(node_id, alias_id, relation="SYNONYM_OF")
            G.add_edge(alias_id, node_id, relation="SYNONYM_OF")
        
        # 관련 용어 엣지
        for related in item.get("related_terms", []):
            related_id = f"term_{related}"
            G.add_edge(node_id, related_id, relation="RELATED_TO")
            G.add_edge(related_id, node_id, relation="RELATED_TO")

    # ── 2. RouteNode: navigation_tool 라우트 맵 ──────────────────────────
    ROUTE_MAP = {
        "irp_tax_saving": {
            "label": "개인형 IRP 세액공제용 화면",
            "depth": 5,
            "trigger_terms": ["IRP", "세액공제", "개인형IRP"],
            "consent_message": "IRP 세액공제용 가입 화면으로 바로 이동해 드릴까요?",
            "voice_guide": "IRP 가입 화면으로 안내해 드릴게요.",
        },
        "investment_diagnosis": {
            "label": "투자 성향 진단 화면",
            "depth": 3,
            "trigger_terms": ["ETF", "펀드", "고위험"],
            "guardrail": True,
        },
        "my_pension": {
            "label": "MY퇴직연금 현황 화면",
            "depth": 3,
            "trigger_terms": ["MY퇴직연금", "내 연금"],
        },
        "portfolio": {
            "label": "포트폴리오 화면",
            "depth": 5,
            "trigger_terms": ["포트폴리오", "운용현황"],
        },
        "retirement_pension": {
            "label": "퇴직연금 메뉴",
            "depth": 2,
            "trigger_terms": ["퇴직연금", "DC"],
        },
    }

    for route_key, info in ROUTE_MAP.items():
        route_id = f"route_{route_key}"
        G.add_node(route_id,
                   type="RouteNode",
                   route_key=route_key,
                   label=info["label"],
                   depth=info.get("depth", 1),
                   guardrail=info.get("guardrail", False))
        
        # 트리거 용어 → LEADS_TO 엣지
        for term in info.get("trigger_terms", []):
            term_id = f"term_{term}"
            if not G.has_node(term_id):
                G.add_node(term_id, type="TermNode", name=term)
            G.add_edge(term_id, route_id, relation="LEADS_TO")
        
        # TRIGGERS_GUARDRAIL 엣지 (고위험 화면)
        if info.get("guardrail"):
            for term in info.get("trigger_terms", []):
                term_id = f"term_{term}"
                G.add_edge(term_id, route_id, relation="TRIGGERS_GUARDRAIL")

    # ── 3. RegNode: regulations.json ─────────────────────────────────────
    reg_path = DATA_DIR / "regulations.json"
    if reg_path.exists():
        with open(reg_path, encoding="utf-8") as f:
            regulations = json.load(f)
        
        for reg in regulations:
            reg_id = f"reg_{reg['id']}"
            G.add_node(reg_id,
                       type="RegNode",
                       name=reg["name"],
                       content=reg["content"],
                       law=reg["law"])
            
            for term in reg.get("related_terms", []):
                term_id = f"term_{term}"
                if not G.has_node(term_id):
                    G.add_node(term_id, type="TermNode", name=term)
                G.add_edge(term_id, reg_id, relation="GOVERNED_BY")

    # ── 4. ProductNode: nh_products.json ─────────────────────────────────
    product_path = DATA_DIR / "nh_products.json"
    if product_path.exists():
        with open(product_path, encoding="utf-8") as f:
            products = json.load(f)
        
        for product in products:
            prod_id = f"product_{product['id']}"
            route_id = f"route_{product['route']}"
            G.add_node(prod_id,
                       type="ProductNode",
                       name=product["name"],
                       risk_level=product.get("risk_level", "UNKNOWN"),
                       eligible=product.get("eligible", ""),
                       tax_benefit=product.get("tax_benefit", ""))
            
            # ProductNode → RouteNode
            if G.has_node(route_id):
                G.add_edge(prod_id, route_id, relation="LEADS_TO")
            
            # TermNode → ProductNode
            for term in product.get("related_terms", []):
                term_id = f"term_{term}"
                if not G.has_node(term_id):
                    G.add_node(term_id, type="TermNode", name=term)
                G.add_edge(term_id, prod_id, relation="HAS_PRODUCT")

    # 그래프 저장
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GRAPH_PATH, "wb") as f:
        pickle.dump(G, f)
    
    print(f"그래프 구축 완료: {G.number_of_nodes()} 노드, {G.number_of_edges()} 엣지")
    return G

if __name__ == "__main__":
    build_graph()
```

```bash
# 실행
uv run python scripts/build_graph.py
```

---

## 4. GraphRAG 검색 엔진

### 4-1. 임베딩 기반 유사도 검색

쿼리가 "IRP"처럼 정확히 일치하지 않아도 ("아이알피", "개인 퇴직연금 계좌") 올바른 노드를 찾을 수 있도록 임베딩 인덱스를 구축합니다.

```python
# app/graph_rag_tool.py (임베딩 인덱스 부분)
import numpy as np
import pickle
from pathlib import Path
import google.generativeai as genai

BASE_DIR = Path(__file__).parent.parent
GRAPH_PATH = BASE_DIR / "data" / "rag" / "knowledge_graph.pkl"
EMBED_PATH = BASE_DIR / "data" / "rag" / "node_embeddings.pkl"

def build_embedding_index(G):
    """TermNode 이름 + 정의를 임베딩하여 인덱스 구축."""
    texts, node_ids = [], []
    
    for node_id, data in G.nodes(data=True):
        if data.get("type") == "TermNode":
            text = data.get("name", "") + " " + data.get("definition", "")[:200]
            texts.append(text)
            node_ids.append(node_id)
    
    # Gemini Embeddings API 사용
    embeddings = []
    for text in texts:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        embeddings.append(result["embedding"])
    
    index = {"node_ids": node_ids, "embeddings": np.array(embeddings)}
    with open(EMBED_PATH, "wb") as f:
        pickle.dump(index, f)
    return index

def find_node_by_query(query: str, index: dict, G, top_k: int = 3) -> list[str]:
    """쿼리 임베딩과 가장 유사한 노드 ID 반환."""
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=query,
        task_type="retrieval_query"
    )
    q_vec = np.array(result["embedding"])
    
    # 코사인 유사도
    embs = index["embeddings"]
    scores = embs @ q_vec / (np.linalg.norm(embs, axis=1) * np.linalg.norm(q_vec) + 1e-9)
    top_indices = np.argsort(scores)[::-1][:top_k]
    
    return [index["node_ids"][i] for i in top_indices]
```

### 4-2. 다중 홉 탐색 함수

```python
# app/graph_rag_tool.py (핵심 탐색 함수)
import networkx as nx
import pickle

def load_graph() -> nx.DiGraph:
    with open(GRAPH_PATH, "rb") as f:
        return pickle.load(f)

def graph_search(query: str, depth: int = 2) -> dict:
    """
    쿼리로 시작 노드를 찾고, depth 홉까지 탐색하여 관련 정보를 반환합니다.
    
    Returns:
        {
            "matched_term": str,          # 가장 유사한 용어
            "definition": str,            # 용어 정의
            "related_terms": list[str],   # 관련 용어 목록
            "suggested_route": str | None, # 추천 화면 경로 (navigation_tool 연동)
            "regulation_hint": str | None, # 관련 법령/한도
            "guardrail": bool,            # True면 고위험 상품 경고
            "products": list[str],        # 관련 상품명
        }
    """
    G = load_graph()
    
    # 1) 시작 노드 탐색 (정확 일치 우선 → 임베딩 폴백)
    start_node = _find_start_node(query, G)
    if not start_node:
        return {"matched_term": None, "definition": None,
                "related_terms": [], "suggested_route": None,
                "regulation_hint": None, "guardrail": False, "products": []}
    
    node_data = G.nodes[start_node]
    result = {
        "matched_term": node_data.get("name"),
        "definition": node_data.get("definition", ""),
        "related_terms": [],
        "suggested_route": None,
        "regulation_hint": None,
        "guardrail": False,
        "products": [],
    }
    
    # 2) BFS로 depth 홉까지 탐색
    visited = {start_node}
    queue = [(start_node, 0)]
    
    while queue:
        current, hop = queue.pop(0)
        if hop >= depth:
            continue
        
        for neighbor in G.successors(current):
            edge_data = G.edges[current, neighbor]
            relation = edge_data.get("relation", "")
            neighbor_data = G.nodes[neighbor]
            neighbor_type = neighbor_data.get("type", "")
            
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, hop + 1))
            
            # 관계 타입별 결과 수집
            if relation == "RELATED_TO" and neighbor_type == "TermNode":
                result["related_terms"].append(neighbor_data.get("name"))
            
            elif relation in ("LEADS_TO",) and neighbor_type == "RouteNode":
                # 첫 번째로 발견된 라우트를 추천 (depth가 얕을수록 우선)
                if not result["suggested_route"]:
                    result["suggested_route"] = neighbor_data.get("route_key")
                    result["guardrail"] = neighbor_data.get("guardrail", False)
            
            elif relation == "TRIGGERS_GUARDRAIL":
                result["guardrail"] = True
                result["suggested_route"] = neighbor_data.get("route_key")
            
            elif relation == "GOVERNED_BY" and neighbor_type == "RegNode":
                result["regulation_hint"] = neighbor_data.get("content")
            
            elif relation == "HAS_PRODUCT" and neighbor_type == "ProductNode":
                result["products"].append(neighbor_data.get("name"))
    
    return result

def _find_start_node(query: str, G: nx.DiGraph) -> str | None:
    """정확 이름 매칭 우선, 없으면 부분 매칭."""
    # 정확 일치
    exact = f"term_{query}"
    if G.has_node(exact):
        return exact
    
    # 부분 이름 매칭
    for node_id, data in G.nodes(data=True):
        if data.get("type") == "TermNode":
            name = data.get("name", "")
            if query in name or name in query:
                return node_id
    
    return None  # → 임베딩 검색 폴백 (build_embedding_index 완료 후 활성화)
```

### 4-3. literacy_tool.py 통합 방식

```python
# app/literacy_tool.py — 변경 부분만 발췌
from app.graph_rag_tool import graph_search  # 추가

def explain_financial_term(term: str) -> str:
    # 1) GraphRAG 우선 시도
    graph_result = graph_search(term, depth=2)
    
    if graph_result["matched_term"]:
        # 그래프에서 찾은 정의 + 관련 용어 + 규정 힌트를 조합
        definition = graph_result["definition"]
        related = ", ".join(graph_result["related_terms"][:3])
        reg_hint = graph_result["regulation_hint"] or ""
        
        return (
            f"### [{graph_result['matched_term']}] 에 대한 설명\n\n"
            f"**1. 수익 및 구조:** {definition}\n\n"
            f"{'**관련 규정:** ' + reg_hint + chr(10) + chr(10) if reg_hint else ''}"
            f"{'**연관 개념:** ' + related + chr(10) + chr(10) if related else ''}"
            f"**2. 최대 리스크:** 모든 금융 상품은 손실 위험이 있습니다. "
            f"'{graph_result['matched_term']}' 관련 결정 전 투자 성향을 확인하세요."
        )
    
    # 2) 폴백: 기존 키워드 검색
    return _legacy_keyword_search(term)
```

---

## 5. 그래프 품질 검증

### 5-1. 빌드 후 기본 검증

```python
# scripts/validate_graph.py
import pickle
import networkx as nx

with open("data/rag/knowledge_graph.pkl", "rb") as f:
    G = pickle.load(f)

print(f"노드 수: {G.number_of_nodes()}")
print(f"엣지 수: {G.number_of_edges()}")
print(f"연결 컴포넌트 수: {nx.number_weakly_connected_components(G)}")

# 고립 노드 확인 (엣지가 없는 노드 → 데이터 문제)
isolated = [n for n in G.nodes if G.degree(n) == 0]
print(f"고립 노드: {len(isolated)}개 → {isolated[:5]}")

# 필수 노드 존재 확인
must_exist = ["term_IRP", "term_ETF", "term_세액공제", "route_irp_tax_saving"]
for node in must_exist:
    status = "✅" if G.has_node(node) else "❌"
    print(f"  {status} {node}")

# 다중 홉 탐색 테스트
from app.graph_rag_tool import graph_search
test_cases = ["IRP", "ETF", "세액공제", "퇴직연금"]
for q in test_cases:
    result = graph_search(q)
    route = result.get("suggested_route", "없음")
    guardrail = "⚠️ 가드레일" if result.get("guardrail") else ""
    print(f"  '{q}' → route: {route} {guardrail}")
```

### 5-2. 핵심 시나리오 수동 검증

| 쿼리 | 기대 matched_term | 기대 suggested_route | 기대 guardrail |
|---|---|---|---|
| "IRP" | IRP | irp_tax_saving | False |
| "ETF" | ETF | investment_diagnosis | **True** |
| "세액공제" | 세액공제 | irp_tax_saving | False |
| "퇴직연금" | 퇴직연금 | retirement_pension | False |
| "아무말" | None | None | False |

---

## 6. 데이터 디렉토리 최종 구조

```
data/
├── rag/
│   ├── fss_glossary.json          # 기존: 금감원 용어사전 (원본)
│   ├── fss_glossary_full.json     # 크롤링 확장본 (related_terms 포함)
│   ├── knowledge_graph.pkl        # NetworkX 그래프 (build_graph.py 생성)
│   └── node_embeddings.pkl        # 노드 임베딩 인덱스 (선택적)
├── regulations.json               # 세법/금소법 규정 (수동 정리)
├── nh_products.json               # NH 퇴직연금 상품 정보
└── eval/
    └── golden_set_nh_bank.json    # 기존 골든셋 (multi-hop 케이스 추가 예정)
```

---

## 7. 확장 고려사항

### 단기 (데모 범위)
- **NetworkX + 정적 JSON**: 외부 인프라 불필요, 로컬 Streamlit에서 즉시 작동
- 그래프를 `.pkl`로 직렬화 → 앱 기동 시 메모리 로드 (데이터 양 적으므로 충분)

### 중기 (운영 전환 시)
- **Neo4j Aura Free** (클라우드 관리형): Cypher 쿼리로 다중 홉 탐색 고도화
- `MATCH (t:Term)-[:LEADS_TO]->(r:Route) WHERE t.name = 'IRP' RETURN r.route_key`

### 장기 (자동화)
- 금감원 용어사전 주기적 크롤링 → 그래프 자동 재빌드 (`make update-graph`)
- 사용자 질의 로그 → 새로운 RELATED_TO 엣지 자동 추가 (HITL)
