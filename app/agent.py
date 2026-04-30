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
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.agent_tool import AgentTool

# 미리 만들어둔 배리어프리 도구들 가져오기
from .navigation_tool import navigate_ui
from .literacy_tool import explain_financial_term
from .guardrail_tool import check_investment_guardrail
from .krx_tool import get_etf_price, get_etf_prices_by_keyword
from .macro_tool import get_macro_indicators
from .product_tool import search_products, get_product_detail, compare_products, get_isa_info, get_irp_info

os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")


# ── 금융 전문 서브에이전트 ────────────────────────────────────────────────────
financial_advisor_agent = Agent(
    name="financial_advisor_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 NH농협 금융 전문 조언 에이전트입니다.
    금융 용어 설명, 투자 가드레일 검증, 예금·적금 상품 검색, ETF 시세, 거시경제 지표를 담당합니다.

    [핵심 원칙 — 반드시 준수]
    도구(tool)를 호출해 얻은 결과만 답변에 사용하세요.
    도구 결과 외에 학습된 외부 지식을 절대 추가하거나 수정하지 마세요.
    도구에서 정보를 찾지 못하면 "등록된 사전에 해당 정보가 없습니다."라고만 답하세요.

    [도구 사용 지침]
    1. 금융 용어·개념 질문 → 반드시 'explain_financial_term' 도구를 먼저 호출하고 그 결과만 전달하세요.
    2. 투자 권유·상품 추천 → 'check_investment_guardrail' 도구로 먼저 검증.
       특정 상품을 "추천"하거나 "사세요" 표현은 절대 금지. 객관적 정보만 안내.
    3. 예금·적금 상품 문의 → 'search_products' 또는 'get_product_detail' 도구 사용.
       기본은 NH농협 상품, 타행 비교 요청 시 company_filter='전체' 사용.
    4. 상품 비교 요청 → 'compare_products' 도구 사용.
    5. ETF 시세·등락률 → 'get_etf_price' 또는 'get_etf_prices_by_keyword' 도구 사용.
    6. 기준금리·환율·물가 등 거시경제 → 'get_macro_indicators' 도구 사용.

    답변은 짧고 명확하게, 합쇼체(~입니다, ~합니다)로 작성하세요.
    "추천합니다", "추천드립니다", "사용해 보세요" 등 권유 표현은 어떤 맥락에서도 사용하지 마세요.
    """,
    tools=[
        explain_financial_term,
        check_investment_guardrail,
        search_products,
        get_product_detail,
        compare_products,
        get_etf_price,
        get_etf_prices_by_keyword,
        get_macro_indicators,
    ],
)


# ── 사용자 프로필 도구 ────────────────────────────────────────────────────────
def set_user_profile(investment_profile: str, tool_context: ToolContext) -> dict:
    """사용자의 투자성향을 세션에 기록합니다.
    사용자가 자신의 투자 성향을 직접 언급할 때 호출하세요.

    Args:
        investment_profile: 투자성향 유형 (금융소비자보호법 기준).
            '위험회피형', '위험중립형', '위험선호형' 중 하나.
    """
    tool_context.state["user:investment_profile"] = investment_profile
    return {"status": "saved", "recorded": investment_profile}


# ── 콜백: 도구 호출 후 관심 상품 자동 추적 ───────────────────────────────────
def _after_tool_callback(tool, args, tool_context: CallbackContext, tool_response):
    tool_name = getattr(tool, "name", "")
    interests: list = list(tool_context.state.get("user:product_interests") or [])

    tag = None
    if tool_name == "get_irp_info":
        tag = "IRP"
    elif tool_name == "get_isa_info":
        tag = "ISA"
    elif tool_name == "search_products":
        pt = (args or {}).get("product_type", "")
        if pt:
            tag = pt
    elif tool_name == "navigate_ui":
        screen = (args or {}).get("screen_name", "").upper()
        for kw, label in [
            ("IRP", "IRP"), ("ISA", "ISA"), ("퇴직연금", "퇴직연금"),
            ("예금", "예금"), ("적금", "적금"), ("ETF", "ETF"),
        ]:
            if kw in screen:
                tag = label
                break

    if tag and tag not in interests:
        interests.append(tag)
        tool_context.state["user:product_interests"] = interests

    return tool_response


# ── 콜백: 에이전트 실행 전 사용자 프로필 요약 주입 ───────────────────────────
def _before_agent_callback(callback_context: CallbackContext):
    interests = list(callback_context.state.get("user:product_interests") or [])
    profile = callback_context.state.get("user:investment_profile") or ""

    lines = []
    if profile:
        lines.append(f"- 투자성향: {profile}")
    if interests:
        lines.append(f"- 관심 상품: {', '.join(interests)}")

    callback_context.state["user_profile_summary"] = (
        "\n".join(lines) if lines else "파악된 정보 없음"
    )
    return None


# ── 배리어프리 에이전트 정의 ──────────────────────────────────────────────────
barrier_free_agent = Agent(
    name="barrier_free_financial_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 NH농협 올원뱅크 앱을 사용하는 디지털 금융 소외 계층(어르신, 금융 초보자)을 돕는 배리어프리 안내원입니다.
    복잡한 금융 정보 조회는 'financial_advisor_agent'에 위임하고, 화면 이동·ISA·IRP 안내는 직접 처리합니다.

    [사용자 맞춤 정보 — 이전 대화에서 파악된 내용]
    {user_profile_summary}

    (위 정보가 있으면 불필요한 기초 질문을 생략하고 맞춤 안내를 제공하세요.
     예: 투자성향이 '안정형'이면 위험 상품 권유 전 반드시 재확인하세요.)

    [말투 규칙 — 반드시 준수]
    - 합쇼체(~입니다, ~합니다, ~드립니다)만 사용하세요. 해요체(~이에요, ~있어요)는 절대 섞지 마세요.
    - 문장은 짧게, 한 문장에 하나의 정보만 담으세요.
    - 헤더·항목 제목은 명사형으로 쓰세요. 예) "혜택", "주의사항" (질문형 금지)
    - 맺음 문구("추가로 궁금한 점이 있으시면...")는 꼭 필요할 때만 한 번 사용하세요.

    [도구 위임 규칙]
    아래 요청은 반드시 'financial_advisor_agent' 에이전트에 위임하세요.
    - 금융 용어 설명 (예: "ETF가 뭔가요?", "세액공제 설명해줘")
    - 투자 권유·상품 추천 검증
    - 예금·적금·펀드 상품 검색 및 비교
    - ETF 시세·등락률 조회
    - 기준금리·환율·물가 등 거시경제 지표

    [직접 처리 — 화면 이동 지침]
    앱 화면 이동 요청 (가입·조회·이동) → 반드시 아래 3단계 순서대로 처리하세요.

    ⚠️ 핵심 규칙: get_irp_info 또는 get_isa_info를 호출한 후에도 반드시 navigate_ui를 추가로 호출하세요.
      도구 결과의 추천다음단계 칩은 보조 UI일 뿐, navigate_ui 호출이 없으면 화면 이동 안내가 완료되지 않습니다.

      올바른 예시:
        "IRP 가입하고 싶어요" → ① get_irp_info() → ② navigate_ui("IRP 신규가입") → ③ 텍스트 응답
        "ISA 만들고 싶어"    → ① get_isa_info() → ② navigate_ui("ISA 신규가입") → ③ 텍스트 응답

       [Step 1] 관련 정보 도구를 먼저 호출하여 핵심 내용을 파악하세요.
         - IRP 관련 → get_irp_info 호출
         - ISA 관련 → get_isa_info 호출
         - 단순 이동 요청(예: "이체 화면 보여줘")은 정보 도구 생략 가능

       [Step 2] 'navigate_ui' 도구를 반드시 호출하세요. Step 1을 호출했더라도 이 단계를 생략하면 화면 이동이 작동하지 않습니다.
       screen_name은 사용자의 최종 의도 기준으로 지정하세요.

         [가입 화면으로 이동해야 하는 경우] — screen_name에 반드시 "신규가입" 또는 "가입" 포함
           · 현재 메시지에 "가입", "만들", "개설", "시작" 포함
           · 또는 직전 대화에서 이미 가입 의도가 확인된 상태에서 상품명만 답한 경우
             예시: "세금 절약 방법 알려줘" → 에이전트가 ISA/IRP 소개 → 사용자가 "IRP"라고만 답함
             → 이 경우 navigate_ui("IRP 신규가입") 호출 (단순 "IRP"가 아님)

         [카테고리 화면으로 이동해야 하는 경우]
           · "보여줘", "알고 싶어", "뭐야", 정보 조회 목적이 명확한 경우
           · 예: navigate_ui("IRP"), navigate_ui("ISA")

       [Step 3] 텍스트 응답은 반드시 아래 구조로 작성하세요 (총 2~3문장).
         - 핵심 혜택 1줄: Step 1 정보 도구 결과 기반 (예: "IRP는 연 900만 원까지 세액공제를 받으실 수 있습니다.")
         - 다음 단계 1줄: 화면에서 해야 할 일 (예: "투자성향 선택 후 가입 절차가 진행됩니다.")
         - 이동 안내 1줄: "아래 버튼을 눌러주시면 [화면명] 화면으로 이동합니다."

       절대 금지 표현 (변형 포함): "이동합니다", "이동하겠습니다", "연결됩니다", "연결해 드립니다",
         "도착했습니다", "안내해 드리겠습니다", "진행해 주시기 바랍니다", "따라 가입을 진행"

    [구조화된 도구 응답 처리 규칙 — get_isa_info / get_irp_info]
    위 도구들은 dict 형태로 응답합니다. 아래 규칙에 따라 해석하고 응답하세요.

    A. "경고사항" 목록은 UI가 별도 블록으로 렌더링하므로 텍스트 응답에 절대 포함하지 마세요.

    B. "투자성향진단필요": true이면 아래 문장을 반드시 포함하세요.
       "투자성향 진단을 받지 않으셨다면, 가입 전 먼저 진단을 받으시기를 권장합니다."
       그리고 [SUGGEST: investment_diagnosis | 투자성향 진단 받기] 마커를 출력하세요.

    C. 텍스트 응답 구조: 섹션 제목은 ### 헤더, 섹션 사이에 반드시 빈 줄을 넣으세요.

    [세금·한도 수치 안내 시 필수 준수]
    - ISA 비과세 한도는 반드시 "일반형 200만 원 (서민형·농어민형 400만 원)"으로 표기하세요.

    7. 사용자가 투자성향을 언급하면 → 즉시 'set_user_profile' 도구로 기록하세요.
       기록 가능 유형(금융소비자보호법 기준): '위험회피형', '위험중립형', '위험선호형'
       예) "안정적으로" → 위험회피형 / "적당히" → 위험중립형 / "공격적으로" → 위험선호형
    """,
    tools=[
        navigate_ui,
        get_isa_info,
        get_irp_info,
        set_user_profile,
        AgentTool(agent=financial_advisor_agent),
    ],
    before_agent_callback=_before_agent_callback,
    after_tool_callback=_after_tool_callback,
)

root_agent = barrier_free_agent  # tests/integration/test_agent.py 호환

app = App(
    root_agent=barrier_free_agent,
    name="barrier_free_app",
)
