# app/system_improvement_agent.py
"""스킬 문서 큐레이터 에이전트 — 관리자 전용 백그라운드 에이전트.

memory/agents/ 하위 에이전트 스킬 문서를 정기적으로 정리·병합·압축합니다.
`adk web curator` 또는 admin_app에서 관리자 발화로 트리거합니다.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types

from .skill_memory import AGENTS_DIR, list_all_skills

_CURATION_LOG = AGENTS_DIR / "_curation_log.md"
_CURATION_THRESHOLD = 10  # 이 이상 누적 시 큐레이션 권장


def get_curation_status() -> dict:
    """에이전트별 스킬 항목 수와 큐레이션 필요 여부를 반환합니다.
    "스킬 현황", "큐레이션 현황", "정리 필요한 에이전트" 요청 시 호출하세요.
    """
    stats = list_all_skills()

    last_curated = "기록 없음"
    if _CURATION_LOG.exists():
        lines = _CURATION_LOG.read_text(encoding="utf-8").strip().split("\n")
        last_curated = lines[-1] if lines else "기록 없음"

    agents_with_status = []
    for info in stats["agents"]:
        agents_with_status.append({
            **info,
            "needs_curation": info["entries"] >= _CURATION_THRESHOLD,
        })

    return {
        "agents": agents_with_status,
        "total_entries": stats["total_entries"],
        "curation_threshold": _CURATION_THRESHOLD,
        "last_curated": last_curated,
    }


def read_skill_file(agent_name: str) -> dict:
    """에이전트의 스킬 파일 전체 내용을 반환합니다.
    스킬 내용 검토 및 정리 전 반드시 먼저 호출하세요.

    Args:
        agent_name: 에이전트 이름 (예: investment_agent, pension_tax_agent)
    """
    path = AGENTS_DIR / f"{agent_name}_skills.md"
    if not path.exists():
        return {"error": f"'{agent_name}' 스킬 파일이 없습니다."}

    content = path.read_text(encoding="utf-8")
    entry_count = content.count("\n## [")
    return {
        "agent_name": agent_name,
        "content": content,
        "entry_count": entry_count,
        "file": path.name,
    }


def write_skill_file(agent_name: str, curated_content: str) -> dict:
    """큐레이션된 내용으로 스킬 파일을 덮어씁니다.

    ⚠️ 반드시 read_skill_file로 원본을 읽은 후 호출하세요.
    ⚠️ 큐레이션 원칙:
       - 유사·중복 항목 → 하나로 병합 (가장 구체적인 예시 유지)
       - 오래되고 일반적인 항목 → 제거 또는 단순화
       - 결과 항목 수는 원본보다 적거나 같아야 합니다

    Args:
        agent_name: 에이전트 이름
        curated_content: 정리된 스킬 파일 전체 내용 (마크다운)
    """
    path = AGENTS_DIR / f"{agent_name}_skills.md"
    original_count = 0
    if path.exists():
        original_count = path.read_text(encoding="utf-8").count("\n## [")

    new_count = curated_content.count("\n## [")
    if new_count > original_count:
        return {
            "status": "rejected",
            "reason": f"항목 수가 늘었습니다 (원본 {original_count}개 → {new_count}개). 큐레이션은 항목을 줄여야 합니다.",
        }

    path.write_text(curated_content, encoding="utf-8")

    # 큐레이션 이력 기록
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    log_entry = f"[{now}] {agent_name}: {original_count}개 → {new_count}개\n"
    _CURATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _CURATION_LOG.open("a", encoding="utf-8") as f:
        f.write(log_entry)

    return {
        "status": "written",
        "agent_name": agent_name,
        "original_entries": original_count,
        "curated_entries": new_count,
        "reduced_by": original_count - new_count,
    }


system_improvement_agent = Agent(
    name="system_improvement_agent",
    model=Gemini(
        model="gemini-3.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""
    당신은 BF Agent의 스킬 문서 큐레이터입니다. 관리자 전용입니다.
    memory/agents/ 하위 에이전트 스킬 문서를 정리·병합·압축합니다.

    [역할]
    에이전트가 대화 중 누적한 스킬 항목을 주기적으로 정리합니다.
    목표: 스킬 문서를 더 간결하고 재사용하기 좋은 형태로 유지합니다.

    [큐레이션 원칙]
    1. 유사/중복 항목 → 하나로 병합 (가장 구체적인 예시와 트리거 조건 유지)
    2. 너무 일반적이거나 당연한 항목 → 제거
    3. 트리거 조건이 겹치는 항목 → 조건을 명확하게 구분하거나 병합
    4. 최종 항목 수는 원본보다 적어야 합니다

    [도구 사용 지침]
    1. "스킬 현황", "큐레이션 현황", "정리 필요" → get_curation_status()
    2. "[agent명] 스킬 정리해줘" →
       a. read_skill_file(agent_name=...) 로 내용 확인
       b. 큐레이션 원칙에 따라 내용을 정리 (병합·제거)
       c. write_skill_file(agent_name=..., curated_content=정리된내용) 으로 저장
    3. "전체 정리", "모두 정리" →
       get_curation_status() 확인 후 needs_curation=True인 에이전트부터 순서대로 처리
    4. "이력 보여줘", "언제 정리했어" → get_curation_status()의 last_curated 필드 참조

    [응답 형식]
    - 현황 보고는 Markdown 표로 출력하십시오.
    - 정리 결과는 "항목 N개 → M개로 압축 (X개 병합/제거)" 형식으로 보고하십시오.
    - 합쇼체(~입니다, ~합니다, ~드립니다)만 사용하십시오.

    [주의사항]
    - 스킬 항목을 제거할 때는 반드시 이유를 함께 보고하십시오.
    - 항목이 10개 미만인 에이전트는 큐레이션 불필요 — 건너뛰십시오.
    - write_skill_file 이후 수정 취소는 불가합니다. 신중히 처리하십시오.
    """,
    tools=[get_curation_status, read_skill_file, write_skill_file],
)
