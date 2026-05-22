import re
from typing import Literal

# 패턴 DB: (패턴 라벨, 위험도, 키워드 목록)
_FRAUD_PATTERNS: list[tuple[str, Literal["HIGH", "MEDIUM", "LOW"], list[str]]] = [
    (
        "보이스피싱 — 기관 사칭",
        "HIGH",
        ["검찰청", "경찰청", "금감원", "금융감독원", "국세청", "법원", "수사관", "형사",
         "체포영장", "구속영장", "계좌 동결", "명의 도용", "피의자"],
    ),
    (
        "보이스피싱 — 대출 빙자",
        "HIGH",
        ["저금리 대환", "대출 승인됐", "대출 승인 났", "수수료 먼저", "선입금", "선이자",
         "보증금 입금", "한도 늘려", "신용 올려", "앱 설치"],
    ),
    (
        "스미싱 — 택배·기관 문자",
        "HIGH",
        ["택배 미수령", "소포 반송", "주소 불일치", "클릭하세요", "확인하세요",
         "http://", "https://", "bit.ly", "단축 url"],
    ),
    (
        "투자 사기",
        "HIGH",
        ["원금 보장", "원금보장", "수익 보장", "수익보장", "고수익 보장",
         "비공개 정보", "내부 정보", "내부자 정보", "리딩방", "코인 보장",
         "일 수익", "월 수익 보장"],
    ),
    (
        "금융 정보 탈취",
        "HIGH",
        ["계좌번호 알려", "비밀번호 알려", "카드번호 알려", "otp 알려", "공인인증서 보내",
         "신분증 사진 보내", "주민등록번호 알려", "개인정보 입력"],
    ),
    (
        "불법 대출 광고",
        "MEDIUM",
        ["무직자 대출", "신용불량 대출", "연체자 대출", "당일 입금", "즉시 대출",
         "정부 지원 대출", "저금리 비밀 상품"],
    ),
    (
        "피싱 사이트 유도",
        "MEDIUM",
        ["은행 앱 재설치", "금융앱 업데이트", "인증 만료", "보안 프로그램 설치",
         "원격 접속", "팀뷰어", "anydesk"],
    ),
]

# 위험도 한글 변환
_RISK_KO = {"HIGH": "높음 🔴", "MEDIUM": "중간 🟠", "LOW": "낮음 🟢"}

# 신고 안내
_REPORT_GUIDE = (
    "금융감독원 1332 | 경찰청 112 | 한국인터넷진흥원 118\n"
    "이미 돈을 이체했다면 즉시 은행 콜센터에 전화해 지급정지를 요청하십시오."
)


def check_fraud_pattern(text: str) -> dict:
    """보이스피싱·금융사기 패턴 DB를 기반으로 입력 텍스트의 위험도를 판정합니다.

    Args:
        text: 사용자가 받은 문자·전화 내용 또는 의심스러운 상황 설명

    Returns:
        위험도 판정 결과 dict
    """
    text_lower = text.lower()
    matched: list[dict] = []

    for label, risk, keywords in _FRAUD_PATTERNS:
        found = [kw for kw in keywords if kw.lower() in text_lower]
        if found:
            matched.append({"유형": label, "위험도": risk, "감지_키워드": found})

    if not matched:
        return {
            "위험도": _RISK_KO["LOW"],
            "감지된_패턴": [],
            "판정": "입력된 내용에서 알려진 금융사기 패턴이 감지되지 않았습니다.",
            "안내": "패턴이 없더라도 의심스러우면 금감원 1332로 문의하십시오.",
        }

    # 최고 위험도 결정
    priority = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    top_risk = max(matched, key=lambda m: priority[m["위험도"]])["위험도"]

    if top_risk == "HIGH":
        verdict = "금융사기 가능성이 매우 높습니다. 먼저 해당 기관 공식 번호(홈페이지 기재)로 직접 확인하시고, 의심스러우면 즉시 신고하십시오."
    else:
        verdict = "금융사기 의심 요소가 있습니다. 해당 기관 공식 번호로 먼저 확인하십시오."

    return {
        "위험도": _RISK_KO[top_risk],
        "감지된_패턴": matched,
        "판정": verdict,
        "신고_및_대응": _REPORT_GUIDE,
    }
