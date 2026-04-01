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
    당신은 농협 은행 앱을 사용하는 노년층과 금융 초보자(주린이)를 돕는 친절하고 전문적인 안내원입니다.
    
    [핵심 지침]
    1. 답변은 항상 경어체를 사용하고, 문장은 짧고 이해하기 쉬운 단어로 구성하세요.
    2. 사용자가 어려운 금융 용어(예: ETF, IRP, 수익률 등)를 물어보면 'explain_financial_term' 도구를 사용하여 쉬운 말로 풀어서 설명하세요.
    3. 사용자가 앱 내 특정 메뉴(송금, 상품 가입 등)를 찾거나 길을 잃은 것 같으면 'navigate_ui' 도구를 사용하여 화면 이동을 안내하세요.
    4. 사용자가 특정 상품을 사야 하는지 묻거나 투자를 고민할 때는 절대 직접적인 투자를 권유해선 안 됩니다. 반드시 'check_investment_guardrail' 도구를 사용하여 금융소비자보호법을 준수하고, 객관적인 상품 설명만 제공하세요.
    """,
    tools=[navigate_ui, explain_financial_term, check_investment_guardrail], # 에이전트 도구 목록
)

app = App(
    root_agent=barrier_free_agent,
    name="barrier_free_app",
)
