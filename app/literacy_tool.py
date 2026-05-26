from pathlib import Path
from google.adk.tools.tool_context import ToolContext

BASE_DIR = Path(__file__).parent.parent
KNOWLEDGE_DIR = BASE_DIR / "data" / "knowledge"
_SEARCH_DOMAINS = ["glossary", "investment"]


def _find_page(term: str) -> str | None:
    """glossary/, investment/ 도메인에서 term과 매칭되는 페이지 내용을 반환."""
    term_lower = term.lower().strip()

    for domain in _SEARCH_DOMAINS:
        domain_dir = KNOWLEDGE_DIR / domain
        if not domain_dir.exists():
            continue
        for page in sorted(domain_dir.glob("*.md")):
            content = page.read_text(encoding="utf-8")

            # 1) 파일명 부분 매칭 (검색어가 파일명 안에 있을 때만 — 역방향은 오탐 방지)
            stem = page.stem.lower()
            if term_lower in stem:
                return content

            # 2) 프론트매터 title / tags 매칭
            in_fm = False
            for line in content.split("\n"):
                stripped = line.strip()
                if stripped == "---":
                    in_fm = not in_fm
                    continue
                if in_fm and (stripped.startswith("title:") or stripped.startswith("tags:")):
                    if term_lower in stripped.lower():
                        return content

    return None


def explain_financial_term(term: str, tool_context: ToolContext = None) -> str:
    """금융 용어를 knowledge base(glossary·investment 도메인)에서 검색해 반환합니다.

    Args:
        term: 설명을 원하는 금융 용어
    Returns:
        해당 용어의 마크다운 페이지 내용. 찾지 못하면 안내 메시지.
    """
    page = _find_page(term)
    if page:
        return page
    return f"등록된 사전에 '{term}'에 대한 정보가 없습니다."
