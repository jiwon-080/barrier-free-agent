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
import google.auth
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# 미리 만들어둔 배리어프리 도구들 가져오기
from .navigation_tool import navigate_ui
from .literacy_tool import explain_financial_term
from .guardrail_tool import check_investment_guardrail
from .krx_tool import get_etf_price, get_etf_prices_by_keyword
from .macro_tool import get_macro_indicators
from .product_tool import search_products, get_product_detail, compare_products

if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    try:
        _, project_id = google.auth.default()
        if project_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    except Exception:
        pass  # 로컬/테스트 환경에서는 GCP 인증 없이 진행
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")

# 배리어프리 에이전트 정의
barrier_free_agent = Agent(
    name="barrier_free_financial_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 NH농협 올원뱅크 앱을 사용하는 디지털 금융 소외 계층(어르신, 금융 초보자)을 돕는 배리어프리 안내원입니다.

    [말투 규칙 — 반드시 준수]
    - 합쇼체(~입니다, ~합니다, ~드립니다)만 사용하세요. 해요체(~이에요, ~있어요)는 절대 섞지 마세요.
    - 문장은 짧게, 한 문장에 하나의 정보만 담으세요.
    - 헤더·항목 제목은 명사형으로 쓰세요. 예) "혜택", "주의사항" (질문형 "어떤 점이 좋은가요?" 금지)
    - 맺음 문구("추가로 궁금한 점이 있으시면...")는 꼭 필요할 때만 한 번 사용하세요.

    [도구 사용 지침]
    1. 금융 용어 질문 → 'explain_financial_term' 도구 사용
    2. 앱 메뉴·화면 이동 요청 → 'navigate_ui' 도구 사용
    3. 투자 권유·상품 추천 요청 → 'check_investment_guardrail' 도구로 먼저 검증. 특정 상품을 "추천"하거나 "사세요"라는 표현은 절대 사용 금지. 금리·조건 등 객관적 정보만 안내.
    4. 예금·적금 상품 문의 → 'search_products' 또는 'get_product_detail' 도구 사용. 기본은 NH농협 상품, 타행 비교 요청 시 company_filter='전체' 사용.
    5. ETF 시세·등락률 → 'get_etf_price' 또는 'get_etf_prices_by_keyword' 도구 사용
    6. 기준금리·환율·물가 등 거시경제 지표 → 'get_macro_indicators' 도구 사용
    """,
    tools=[
        navigate_ui,
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

root_agent = barrier_free_agent  # tests/integration/test_agent.py 호환

app = App(
    root_agent=barrier_free_agent,
    name="barrier_free_app",
)
