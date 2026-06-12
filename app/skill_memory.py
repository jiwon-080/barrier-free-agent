# app/skill_memory.py
"""Hermes 스타일 에이전트 스킬 메모리.

memory/agents/{agent_name}_skills.md 에 해결 패턴을 누적합니다.
각 에이전트는 make_skill_appender()로 생성된 전용 도구를 사용합니다.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "memory" / "agents"

_HEADER = """\
# {agent_name} 스킬 메모리

> Hermes 패턴 — 에이전트가 복잡한 케이스 해결 후 자동 누적.
> 트리거 조건과 해결 패턴을 기록해 유사 케이스 재활용.

"""


def _ensure_file(agent_name: str) -> Path:
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = AGENTS_DIR / f"{agent_name}_skills.md"
    if not path.exists():
        path.write_text(_HEADER.format(agent_name=agent_name), encoding="utf-8")
    return path


def load_agent_skills(agent_name: str) -> str:
    """memory/agents/{agent_name}_skills.md 를 읽어 반환. 파일 없으면 빈 문자열."""
    path = AGENTS_DIR / f"{agent_name}_skills.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def append_skill_entry(agent_name: str, skill_summary: str, trigger: str, example_query: str) -> dict:
    """스킬 항목 1개를 파일에 append합니다."""
    path = _ensure_file(agent_name)
    now = datetime.now().strftime("%Y-%m-%d")
    entry = (
        f"## [{now}] {trigger or '신규 패턴'}\n\n"
        f"**요약**: {skill_summary}\n\n"
        f"**트리거**: {trigger or '—'}\n\n"
        f"**예시 질문**: {example_query or '—'}\n\n"
        f"---\n\n"
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(entry)
    return {"status": "appended", "agent": agent_name, "file": path.name}


def list_all_skills() -> dict:
    """memory/agents/ 전체 스킬 파일 목록과 항목 수를 반환합니다."""
    if not AGENTS_DIR.exists():
        return {"agents": [], "total_entries": 0}

    result = []
    total = 0
    for path in sorted(AGENTS_DIR.glob("*_skills.md")):
        text = path.read_text(encoding="utf-8")
        count = text.count("\n## [")
        total += count
        result.append({"agent": path.stem.replace("_skills", ""), "entries": count, "file": path.name})
    return {"agents": result, "total_entries": total}


def make_skill_appender(agent_name: str):
    """에이전트 전용 append_skill 도구를 생성합니다."""

    def append_skill(skill_summary: str, trigger: str = "", example_query: str = "") -> dict:
        """새로운 해결 패턴을 발견했을 때 스킬 문서에 기록합니다.

        아래 상황에서 호출하세요:
        - 지식베이스에 없는 질문 유형을 처음 해결했을 때
        - 도구 조합·라우팅에서 효과적인 패턴을 발견했을 때
        - 사용자가 예상치 못한 방식으로 질문해 새로운 접근이 필요했을 때

        Args:
            skill_summary: 해결 패턴 핵심 요약 (1-2문장)
            trigger: 이 패턴이 발동되는 조건/키워드
            example_query: 대표 질문 (수치·이름 등 개인정보 반드시 제거)
        """
        return append_skill_entry(agent_name, skill_summary, trigger, example_query)

    append_skill.__name__ = f"append_skill"
    return append_skill
