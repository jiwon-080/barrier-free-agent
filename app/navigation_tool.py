from typing import Dict, Any

def navigate_ui(query: str) -> Dict[str, Any]:
    """어르신들을 위해 NH올원뱅크 앱의 화면 이동 경로를 안내합니다.
    
    Args:
        query: 사용자의 요청 (예: 'IRP 가입', '예금 가입')
    """
    if "IRP" in query or "퇴직연금" in query:
        return {
            "type": "navigation",
            "path": ["메인 화면", "전체 메뉴(우측 상단 ≡)", "금융상품(좌측 탭)", "퇴직연금", "퇴직연금(IRP) 가입"],
            "visual_instructions": [
                {"step": 1, "action": "우측 상단 '≡' 버튼 클릭", "location": "오른쪽 위", "color": "검정색"},
                {"step": 2, "action": "좌측 메뉴에서 '금융상품' 탭 클릭", "location": "왼쪽 세로 메뉴", "color": "초록색 강조"},
                {"step": 3, "action": "리스트에서 '퇴직연금' 클릭", "location": "중앙 리스트", "color": "기본"},
                {"step": 4, "action": "세부 메뉴에서 '퇴직연금(IRP)' 클릭", "location": "중앙 리스트", "color": "기본"},
                {"step": 5, "action": "'퇴직연금(IRP) 가입' 버튼 클릭", "location": "화면 하단", "color": "파란색 강조"}
            ],
            "voice_guide": "어르신, IRP 가입 화면을 찾으시는군요? 화면 오른쪽 맨 위에 있는 줄 세 개 버튼을 먼저 눌러보시겠어요? 그 다음 왼쪽에서 '금융상품'을 누르시고, 순서대로 따라오시면 제가 끝까지 도와드릴게요. 천천히 하셔도 됩니다."
        }
    
    elif "예금" in query or "적금" in query:
        return {
            "type": "suggestion",
            "suggestion_action": "큰글 모드 전환",
            "visual_instructions": [
                {"step": 1, "action": "상단 '큰글' 토글 스위치 클릭", "location": "화면 최상단 중앙", "color": "회색에서 초록색으로 변경됨"}
            ],
            "voice_guide": "어르신, 예금 가입은 글씨가 큰 '큰글 모드'에서 하시는 게 훨씬 눈이 편하실 거예요. 화면 맨 위에 있는 '큰글' 버튼을 한 번 눌러보시겠어요? 그러면 제가 더 보기 쉽게 예금 가입을 도와드릴게요."
        }
    
    return {
        "type": "error",
        "message": "죄송합니다. 요청하신 기능의 위치를 찾지 못했습니다.",
        "voice_guide": "죄송해요, 어르신. 제가 그 기능이 어디 있는지 아직 공부를 더 해야 할 것 같아요. 'IRP 가입'이나 '예금 가입'처럼 다시 한 번 말씀해 주시겠어요?"
    }
