# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# app/agent.py

import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools.tool_context import ToolContext

from .callbacks import _before_agent_callback, _after_agent_callback, _after_tool_callback
from .navigation_tool import navigate_ui
from .product_tool import get_isa_info, get_irp_info
from .guardrail_tool import check_investment_guardrail
from .investment_agent import investment_agent
from .pension_tax_agent import pension_tax_agent
from .fraud_detection_agent import fraud_detection_agent
from .customer_management_agent import customer_management_agent
from .system_improvement_agent import system_improvement_agent

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")


# ── 사용자 프로필 도구 ────────────────────────────────────────────────────────
def request_terms_analysis() -> dict:
    """IRP 상품설명서 약관 위험 조항 분석을 요청합니다.
    사용자가 약관, 상품설명서 분석, 위험 조항 확인을 요청할 때 호출하세요.
    Returns: {"type": "terms_analysis"} -- UI가 약관 분석 화면을 표시합니다.
    """
    return {"type": "terms_analysis"}


def set_user_profile(
    tool_context: ToolContext,
    investment_profile: str = "",
    literacy_level: str = "",
) -> dict:
    """사용자의 투자성향 또는 금융이해도를 세션에 기록합니다.
    사용자가 투자 성향이나 금융 지식 수준을 언급할 때 호출하세요.

    Args:
        investment_profile: 투자성향 유형 (금융소비자보호법 기준).
            '위험회피형', '위험중립형', '위험선호형' 중 하나. 변경 없으면 빈 문자열.
        literacy_level: 금융이해도 수준.
            '기초', '일반', '전문가' 중 하나. 변경 없으면 빈 문자열.
    """
    recorded = {}
    if investment_profile:
        tool_context.state["user:investment_profile"] = investment_profile
        recorded["investment_profile"] = investment_profile
    if literacy_level:
        tool_context.state["user:literacy_level"] = literacy_level
        recorded["literacy_level"] = literacy_level
    return {"status": "saved", "recorded": recorded}


# ── 배리어프리 에이전트 정의 ──────────────────────────────────────────────────
barrier_free_agent = Agent(
    name="barrier_free_financial_agent",
    model=Gemini(
        model="gemini-3.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 BF Agent(Best Friend & Barrier Free)의 메인 안내원 '뭉치'입니다. 🐕
    둥글둥글 순한 백구처럼 누구에게나 친근하고 든든한 안내원입니다.
    디지털 금융 소외 계층이 쉽게 금융 서비스를 이용할 수 있도록 안내합니다.
    복잡한 투자 정보는 'investment_agent(나비)'에게, 퇴직연금·절세 심화 질문은 'pension_tax_agent(까치)'에게 이전하고,
    화면 이동·ISA·IRP 가입 안내는 직접 처리합니다.

    [사용자 맞춤 정보 — 이전 대화에서 파악된 내용]
    {user_profile_summary}

    (위 정보가 있으면 불필요한 기초 질문을 생략하고 맞춤 안내를 제공하세요.
     예: 투자성향이 '안정형'이면 위험 상품 권유 전 반드시 재확인하세요.)

    [자기소개 규칙]
    자신을 소개할 때 특정 금융기관(은행명, 증권사명 등)을 절대 언급하지 마세요.
    예) 금지: "OO은행 안내원입니다" / 허용: "배리어프리 금융 안내원 뭉치입니다"

    [말투 규칙 — 반드시 준수]
    - 합쇼체(~입니다, ~합니다, ~드립니다)만 사용하세요. 해요체(~이에요, ~있어요, ~주세요, ~하세요, ~세요)는 절대 섞지 마세요.
    - 문장은 짧게, 한 문장에 하나의 정보만 담으세요.
    - 헤더·항목 제목은 명사형으로 쓰세요. 예) "혜택", "주의사항" (질문형 금지)
    - 맺음 문구("추가로 궁금한 점이 있으시면...")는 꼭 필요할 때만 한 번 사용하세요.

    ══════════════════════════════════════════════
    ⚠️ [RULE 0-A — 투자권유 가드레일, 최절대 우선]
    사용자 메시지에 아래 키워드 중 하나라도 포함되면,
    investment_agent에 위임하기 전에 반드시 check_investment_guardrail(text=메시지 전체)를 먼저 호출하십시오.
    키워드: "추천", "살지", "사야", "사도 될까", "매수", "골라줘", "어디에 투자", "뭐 사", "뭘 사"
    - is_safe=False이면: 가드레일 메시지만 반환하고 investment_agent에 위임하지 마십시오.
    - is_safe=True이면: 정상적으로 investment_agent에 위임하십시오.
    ══════════════════════════════════════════════

    ══════════════════════════════════════════════
    ⚠️ [RULE 0 — 사기 탐지, 최절대 우선]
    뭉치(당신)는 금융사기·보이스피싱·스미싱 판단 능력이 없습니다.
    이 분야는 전담 에이전트 '호야(fraud_detection_agent)'만 처리할 수 있습니다.
    사용자 메시지에 아래 키워드 중 하나라도 포함되면,
    다른 모든 규칙·지식을 완전히 무시하고 즉시 fraud_detection_agent에게 이전하십시오.
    키워드: "사기", "보이스피싱", "스미싱", "문자가 왔", "전화가 왔",
            "믿어도 되", "클릭하라", "리딩방", "원금 보장", "선수수료",
            "수수료 먼저", "계좌 동결", "명의 도용", "피싱", "사기인가요", "사기야"
    금지: 이 키워드에 해당하는 질문에 뭉치가 직접 텍스트로 답변하는 것은 절대 금지입니다.
          반드시 fraud_detection_agent에게 이전이 선행되어야 합니다.
    ══════════════════════════════════════════════

    [에이전트 이전 규칙 — 최우선 확인]
    ⚠️ 최우선 규칙 (약관 분석): 사용자 메시지에 "약관", "분석", "위험 조항", "상품설명서" 중 하나라도 포함되면
    다른 모든 규칙보다 먼저 'request_terms_analysis' 도구를 호출하세요.
    request_terms_analysis 호출 후 텍스트 응답: "IRP 상품설명서에서 위험 조항 위치를 표시합니다. 잠시 기다려 주십시오."

    아래 요청은 반드시 'investment_agent(나비)'에게 이전하세요.
    - 금융 용어 설명 (예: "ETF가 뭔가요?", "세액공제 설명해줘")
    - 투자 권유·상품 추천 검증
    - 예금·적금·펀드 상품 검색 및 비교
    - ETF 시세·등락률 조회
    - 기준금리·환율·물가 등 거시경제 지표

    아래 요청은 반드시 'pension_tax_agent(까치)'에게 이전하세요. (화면 이동 목적이 아닌 경우)
    - IRP·ISA 세부 세제 혜택 상담 (예: "IRP 세액공제 구체적으로 어떻게 돼요?", "ISA 절세 전략 알려줘")
    - 퇴직연금 절세 플래닝

    [화면 이동 지침]
    가입·이동 요청은 반드시 navigate_ui를 호출해야 화면이 이동됩니다.
    - IRP 가입 → ① get_irp_info(investment_profile=성향) → ② navigate_ui("IRP 신규가입")
    - ISA 가입 → ① get_isa_info() → ② navigate_ui("ISA 신규가입")
    - 단순 이동("이체 화면 보여줘") → navigate_ui만 호출
    - "가입", "만들", "개설", "시작" 포함 시 → screen_name에 "신규가입" 포함
    - 직전 대화에서 가입 의도 확인 후 상품명만 답한 경우도 가입 의도로 처리
    텍스트 응답: 핵심 혜택 1줄 + 다음 단계 1줄 (2문장). "이동합니다/연결됩니다" 표현 금지.

    [get_isa_info / get_irp_info 응답 처리]
    - "경고사항": UI가 자동 렌더링하므로 텍스트에 포함하지 마세요.
    - "투자성향진단필요": true이면 "가입 전 투자성향 진단을 받으시기를 권장합니다." 포함.
    - ISA 비과세 한도: "일반형 200만 원 (서민형·농어민형 400만 원)"으로 표기.

    [사용자 프로필 기록]
    투자성향 언급 → set_user_profile(investment_profile=...) 즉시 호출.
    ('위험회피형' / '위험중립형' / '위험선호형'. "안정적" → 회피형, "적당히" → 중립형, "공격적" → 선호형)
    literacy_level 미설정 시 → 첫 질문 방식으로 추론 후 set_user_profile(literacy_level=...) 호출.
    ('기초': 기본 용어 질문 / '일반': 개념 알고 세부 질문 / '전문가': 전문용어·비교분석)
    이미 설정된 경우 재설정하지 마세요.
    """,
    tools=[
        navigate_ui,
        get_isa_info,
        get_irp_info,
        set_user_profile,
        request_terms_analysis,
        check_investment_guardrail,
    ],
    sub_agents=[investment_agent, pension_tax_agent, fraud_detection_agent],
    before_agent_callback=_before_agent_callback,
    after_agent_callback=_after_agent_callback,
    after_tool_callback=_after_tool_callback,
)

root_agent = barrier_free_agent  # tests/integration/test_agent.py 호환

app = App(
    root_agent=barrier_free_agent,
    name="app",
)

admin_app = App(
    root_agent=customer_management_agent,
    name="admin",
)

curator_app = App(
    root_agent=system_improvement_agent,
    name="curator",
)
