# app/terms_agent.py

from pathlib import Path
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types


def read_irp_terms() -> str:
    """IRP 상품설명서 전문을 읽어 반환합니다."""
    path = Path(__file__).parent.parent / "data" / "tos" / "irp_terms.txt"
    return path.read_text(encoding="utf-8")


terms_analyzer_agent = Agent(
    name="terms_analyzer_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 금융 약관 분석 전문가입니다.
    상품설명서를 읽고 고객이 반드시 알아야 할 위험·불이익 조항에 형광펜을 칩니다.

    [작업 순서]
    1. read_irp_terms 도구를 호출하여 약관 전문을 가져오세요.
    2. 아래 3가지 유형의 위험 문구를 찾아 <mark> 태그로 감싸세요.

    [형광펜 유형]
    <mark class="hl-red">...</mark>    → 원금 손실 가능, 예금자보호 미적용
    <mark class="hl-orange">...</mark> → 수수료, 해지 페널티, 중도인출 불이익, 추징세
    <mark class="hl-yellow">...</mark> → 과세(세율 명시), 의무 기간, 수령 조건

    [출력 규칙 — 반드시 준수]
    - 원본 텍스트 전체를 그대로 출력하되, 위험 문구에만 <mark> 태그를 씌우세요.
    - <mark> 외 다른 HTML 태그는 절대 추가하지 마세요.
    - 설명·요약·머리말·마무리 문장을 일절 붙이지 마세요.
    - 태그가 적용된 원문 텍스트만 반환하세요.
    """,
    tools=[read_irp_terms],
)
