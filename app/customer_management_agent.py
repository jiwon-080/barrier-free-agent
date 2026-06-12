# app/customer_management_agent.py
"""고객 관리 에이전트 — 관리자 전용 백그라운드 에이전트.

memory/users/ 사용자 프로필 조회·삭제·통계 기능을 제공합니다.
`adk web admin` 또는 ADK playground의 admin 앱으로 접근합니다.
"""
from __future__ import annotations

from collections import Counter

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .user_memory import MEMORY_DIR, delete_user_memory
from .skill_memory import list_all_skills, AGENTS_DIR


def _read_frontmatter(path) -> dict:
    """파일에서 YAML 프론트매터 전체를 파싱합니다."""
    result: dict = {}
    in_fm = False
    for line in path.read_text(encoding="utf-8").split("\n"):
        s = line.strip()
        if s == "---":
            if not in_fm:
                in_fm = True
            else:
                break
            continue
        if not in_fm:
            continue
        if ": " in s:
            key, _, val = s.partition(": ")
            result[key.strip()] = val.strip().strip("\"'")
    raw = result.pop("product_interests", "[]")
    result["product_interests"] = [x.strip() for x in raw.strip("[]").split(",") if x.strip()]
    return result


def list_users() -> dict:
    """모든 사용자 목록과 프로필 요약을 반환합니다.
    "사용자 목록", "사용자 현황", "사용자 보고해줘" 요청 시 호출하세요.
    """
    if not MEMORY_DIR.exists():
        return {"users": [], "total": 0}

    users = []
    for path in sorted(MEMORY_DIR.glob("*.md")):
        mem = _read_frontmatter(path)
        users.append({
            "user_id": path.stem,
            "investment_profile": mem.get("investment_profile") or "미설정",
            "literacy_level": mem.get("literacy_level") or "미설정",
            "product_interests": mem.get("product_interests") or [],
            "updated_at": mem.get("updated_at") or "",
        })
    return {"users": users, "total": len(users)}


def get_user_profile(user_id: str) -> dict:
    """특정 사용자의 상세 프로필을 반환합니다.

    Args:
        user_id: 조회할 사용자 ID
    """
    path = MEMORY_DIR / f"{user_id}.md"
    if not path.exists():
        return {"error": f"사용자 '{user_id}'의 메모리 파일이 없습니다."}
    return {"user_id": user_id, **_read_frontmatter(path)}


def delete_user_profile(user_id: str) -> dict:
    """특정 사용자의 메모리 파일을 삭제합니다.

    Args:
        user_id: 삭제할 사용자 ID
    """
    success = delete_user_memory(user_id)
    if success:
        return {"status": "deleted", "user_id": user_id}
    return {"status": "not_found", "user_id": user_id}


def get_user_stats() -> dict:
    """전체 사용자 통계 — 투자성향·금융이해도 분포, 관심 상품 현황을 반환합니다.
    "통계", "분포", "집계", "현황 리포트" 요청 시 호출하세요.
    """
    if not MEMORY_DIR.exists():
        return {"total": 0}

    paths = list(MEMORY_DIR.glob("*.md"))
    if not paths:
        return {"total": 0}

    profile_dist: Counter = Counter()
    literacy_dist: Counter = Counter()
    interest_dist: Counter = Counter()

    for path in paths:
        mem = _read_frontmatter(path)
        p = mem.get("investment_profile")
        lv = mem.get("literacy_level")
        profile_dist[p if (p and p != "null") else "미설정"] += 1
        literacy_dist[lv if (lv and lv != "null") else "미설정"] += 1
        for interest in mem.get("product_interests") or []:
            interest_dist[interest] += 1

    return {
        "total": len(paths),
        "investment_profile_distribution": dict(profile_dist),
        "literacy_level_distribution": dict(literacy_dist),
        "top_product_interests": dict(interest_dist.most_common(10)),
    }


def list_agent_skills() -> dict:
    """에이전트별 스킬 문서 목록과 최근 항목을 반환합니다.
    "스킬 현황", "스킬 보고해줘", "에이전트 학습 현황" 요청 시 호출하세요.
    """
    stats = list_all_skills()
    details = []
    for agent_info in stats["agents"]:
        path = AGENTS_DIR / agent_info["file"]
        text = path.read_text(encoding="utf-8")
        sections = [s.strip() for s in text.split("\n## [") if s.strip()]
        recent = sections[-1][:200] + "..." if sections and len(sections[-1]) > 200 else (sections[-1] if sections else "")
        details.append({**agent_info, "latest_entry": recent})
    return {**stats, "agents": details}


customer_management_agent = Agent(
    name="customer_management_agent",
    model=Gemini(
        model="gemini-3-flash-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 BF Agent의 고객 관리 에이전트입니다. 관리자 전용입니다.
    memory/users/ 에 저장된 사용자 프로필을 조회·삭제·집계합니다.

    [도구 사용 규칙]
    1. "사용자 목록", "사용자 현황", "보고해줘" → list_users()
    2. "사용자 [ID]", "[ID] 프로필" → get_user_profile(user_id=...)
    3. "삭제", "초기화", "지워줘" + user_id → delete_user_profile(user_id=...)
       ⚠️ 삭제는 취소 불가 — user_id를 반드시 메시지에서 정확히 파악 후 호출하세요.
    4. "통계", "분포", "집계", "리포트" → get_user_stats()
    5. "스킬 현황", "스킬 보고", "에이전트 학습" → list_agent_skills()

    [응답 형식]
    - 목록·통계는 Markdown 표로 출력하십시오.
    - 삭제 결과는 "user_id [X] 메모리가 삭제되었습니다." 형식으로 명확히 보고하십시오.
    - 합쇼체(~입니다, ~합니다, ~드립니다)만 사용하십시오.

    [주의사항]
    - 이 에이전트는 관리자 전용입니다. 일반 사용자에게 노출되지 않습니다.
    - user_id는 시스템 식별자입니다. 이름·계좌번호 등 PII는 저장되지 않습니다.
    """,
    tools=[list_users, get_user_profile, delete_user_profile, get_user_stats, list_agent_skills],
)
