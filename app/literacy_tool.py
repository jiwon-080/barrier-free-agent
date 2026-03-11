from google.adk.tools import tool

@tool
def explain_financial_term(term: str) -> str:
    """주린이(초보 투자자)를 위해 어려운 금융 용어를 쉬운 말로 풀어서 설명합니다.
    
    Args:
        term: 설명을 원하는 금융 용어
    """
    # TODO: RAG(Retrieval-Augmented Generation)를 통한 용어 사전 조회 구현
    return f"'{term}'에 대한 쉬운 설명입니다: (RAG 데이터 로드 필요)"
