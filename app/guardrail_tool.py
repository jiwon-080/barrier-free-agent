import re
from typing import Dict, Any

def check_investment_guardrail(text: str) -> Dict[str, Any]:
    """금융소비자보호법(금소법) 준수를 위해 부적절한 투자 권유나 과장 광고가 있는지 검사합니다.
    
    Args:
        text: 검사할 메시지 내용 (사용자 입력 또는 에이전트 답변)
        
    Returns:
        검사 결과 (통과 여부 및 메시지)
    """
    # 투자 권유성 또는 과장 광고성 키워드 목록
    prohibited_keywords = [
        "추천", "무조건", "수익 보장", "수익보장", "가입하세요", 
        "확실한", "대박", "원금 보장", "원금보장", "절대"
    ]
    
    # 키워드 검사
    found_keywords = [word for word in prohibited_keywords if word in text]
    
    if found_keywords:
        return {
            "is_safe": False,
            "detected_keywords": found_keywords,
            "message": "죄송합니다. 저는 투자 권유를 할 수 없으며, 객관적인 상품 정보만 제공할 수 있습니다.",
            "voice_guide": "어르신, 제가 특정 상품을 추천해드리는 것은 법으로 금지되어 있어요. 대신 궁금하신 상품의 내용을 쉽고 객관적으로 설명해 드릴게요."
        }
    
    return {
        "is_safe": True,
        "message": text
    }
