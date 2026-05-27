"""Cross-session user memory — Hermes-style file-based persistence.

memory/users/{user_id}.md 파일에 투자성향·금융이해도·관심상품을 저장합니다.
PII(이름·계좌번호 등)는 저장하지 않습니다.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "memory" / "users"

_SKIP_PREFIXES = (
    "nav_user_", "inv_user_", "pt_user_", "fraud_user_",
    "eval_user_", "_test_",
)


def _is_eval_user(user_id: str) -> bool:
    return any(user_id.startswith(p) for p in _SKIP_PREFIXES)


def load_user_memory(user_id: str) -> dict:
    """memory/users/{user_id}.md에서 프로필 로드. 파일 없으면 빈 dict 반환."""
    if _is_eval_user(user_id):
        return {}

    path = MEMORY_DIR / f"{user_id}.md"
    if not path.exists():
        return {}

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
            val = val.strip("\"'")
            if val and val.lower() != "null":
                result[key] = val

    # product_interests: "[IRP, ISA]" → list
    raw = result.pop("product_interests", "")
    interests = [x.strip() for x in raw.strip("[]").split(",") if x.strip()]
    if interests:
        result["product_interests"] = interests

    return result


def save_user_memory(user_id: str, profile: dict) -> None:
    """memory/users/{user_id}.md에 프로필 저장. 의미 있는 데이터 없으면 no-op."""
    if _is_eval_user(user_id):
        return

    investment_profile = profile.get("investment_profile", "")
    literacy_level = profile.get("literacy_level", "")
    product_interests: list = profile.get("product_interests") or []

    if not investment_profile and not literacy_level:
        return

    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    interests_str = ", ".join(product_interests)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    content = f"""---
investment_profile: {investment_profile or 'null'}
literacy_level: {literacy_level or 'null'}
product_interests: [{interests_str}]
updated_at: {now}
---

| 항목 | 값 |
|---|---|
| 투자성향 | {investment_profile or '미설정'} |
| 금융이해도 | {literacy_level or '미설정'} |
| 관심 상품 | {interests_str or '없음'} |
| 마지막 업데이트 | {now} |
"""
    (MEMORY_DIR / f"{user_id}.md").write_text(content, encoding="utf-8")


def delete_user_memory(user_id: str) -> bool:
    """memory/users/{user_id}.md 삭제. 삭제 성공 시 True 반환."""
    path = MEMORY_DIR / f"{user_id}.md"
    if path.exists():
        path.unlink()
        return True
    return False
