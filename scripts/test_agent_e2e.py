"""
배리어프리 에이전트 end-to-end 테스트
실행: uv run python scripts/test_agent_e2e.py
"""
import os
import sys
import importlib.util

# .env 로드 (GOOGLE_GENAI_USE_VERTEXAI 보다 먼저)
from dotenv import load_dotenv
load_dotenv()

# 로컬 테스트: 직접 Gemini API 키 사용 (Vertex AI 비활성화)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

SEP = "-" * 60


# ─────────────────────────────────────────────
# STEP 1: Gemini API 연결 확인
# ─────────────────────────────────────────────
def step1_api_connection():
    print(f"\n{'='*60}")
    print("STEP 1: Gemini API 연결 확인")
    print(SEP)

    if not GOOGLE_API_KEY:
        print("[FAIL] GOOGLE_API_KEY가 .env에 없습니다.")
        sys.exit(1)

    from google import genai
    client = genai.Client(api_key=GOOGLE_API_KEY)

    # 사용 가능한 모델 중 gemini 계열만 출력
    print("사용 가능한 Gemini 모델:")
    for m in client.models.list():
        if "gemini" in m.name.lower():
            print(f"  {m.name}")

    # 간단한 ping
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="안녕하세요, 한 문장으로 짧게 답해주세요.",
    )
    print(f"\n[OK] 응답: {response.text.strip()[:100]}")


# ─────────────────────────────────────────────
# STEP 2: 핵심 도구 직접 호출 확인
# ─────────────────────────────────────────────
def _load_tool(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def step2_tools():
    print(f"\n{'='*60}")
    print("STEP 2: 핵심 도구 단독 호출 확인")

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_dir = os.path.join(base, "app")

    cases = [
        ("navigation_tool.py",  "navigate_ui",
         lambda m: m.navigate_ui("IRP 가입하고 싶어요"),
         "navigate_ui"),

        ("literacy_tool.py",    "explain_financial_term",
         lambda m: m.explain_financial_term("IRP"),
         "explain_financial_term"),

        ("guardrail_tool.py",   "check_investment_guardrail",
         lambda m: m.check_investment_guardrail("이 ETF 지금 사면 무조건 오릅니다"),
         "check_investment_guardrail"),

        ("product_tool.py",     "search_products",
         lambda m: m.search_products("예금", term_months=12, top_n=2),
         "search_products"),
    ]

    for filename, mod_name, fn, label in cases:
        print(f"\n{SEP}\n[{label}]")
        try:
            mod = _load_tool(os.path.join(app_dir, filename), mod_name)
            result = fn(mod)
            preview = str(result)[:200].replace("\n", " ")
            print(f"  → {preview}…")
            print("  [OK]")
        except Exception as e:
            print(f"  [FAIL] {e}")


# ─────────────────────────────────────────────
# STEP 3: ADK 에이전트 통합 호출
# ─────────────────────────────────────────────
def step3_agent():
    print(f"\n{'='*60}")
    print("STEP 3: ADK 에이전트 통합 호출")
    print(SEP)

    try:
        from google.adk.agents.run_config import RunConfig, StreamingMode
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types as gtypes
    except ImportError as e:
        print(f"[SKIP] ADK 임포트 실패: {e}")
        return

    try:
        from app.agent import barrier_free_agent
    except Exception as e:
        print(f"[FAIL] agent.py 로드 실패: {e}")
        return

    session_service = InMemorySessionService()
    session = session_service.create_session_sync(
        user_id="test_user", app_name="barrier_free_app"
    )
    runner = Runner(
        agent=barrier_free_agent,
        session_service=session_service,
        app_name="barrier_free_app",
    )

    queries = [
        "IRP가 뭔가요?",
        "NH농협 12개월 예금 금리 알려줘",
        "지금 기준금리가 얼마야?",
    ]

    for q in queries:
        print(f"\n질문: {q}")
        try:
            message = gtypes.Content(
                role="user", parts=[gtypes.Part.from_text(text=q)]
            )
            events = list(runner.run(
                new_message=message,
                user_id="test_user",
                session_id=session.id,
                run_config=RunConfig(streaming_mode=StreamingMode.NONE),
            ))
            # 마지막 텍스트 응답 추출
            answer = ""
            for event in reversed(events):
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if p.text]
                    if texts:
                        answer = " ".join(texts)
                        break
            print(f"답변: {answer[:300].replace(chr(10), ' ')}")
        except Exception as e:
            print(f"[FAIL] {e}")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    step1_api_connection()
    step2_tools()
    step3_agent()
    print(f"\n{'='*60}\n테스트 완료\n")
