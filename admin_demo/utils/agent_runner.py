"""ADK 에이전트를 Streamlit에서 동기식으로 실행하는 래퍼."""
import asyncio
import uuid
import sys
import os
from pathlib import Path

# app/ 패키지를 import할 수 있도록 프로젝트 루트를 경로에 추가
_PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from google.adk.runners import InMemoryRunner
from google.genai import types


def _extract_text(events) -> str:
    """이벤트 목록에서 에이전트 최종 텍스트 응답을 추출합니다."""
    texts = []
    for event in events:
        if not event.content or not event.content.parts:
            continue
        if event.author == "user":
            continue
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                texts.append(part.text)
    return texts[-1] if texts else "(응답 없음)"


async def _run(runner: InMemoryRunner, user_id: str, session_id: str, message: str) -> tuple[str, list]:
    """에이전트를 실행하고 (응답 텍스트, 이벤트 목록)을 반환합니다."""
    content = types.Content(
        role="user",
        parts=[types.Part(text=message)],
    )
    events = []
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        events.append(event)
    return _extract_text(events), events


class AgentChat:
    """Streamlit session_state에 상태를 유지하는 에이전트 채팅 인터페이스."""

    def __init__(self, agent, app_name: str, state_key: str):
        self.state_key = state_key
        self._agent = agent
        self._app_name = app_name

    def _get_state(self, st_state: dict) -> dict:
        if self.state_key not in st_state:
            st_state[self.state_key] = {
                "runner": InMemoryRunner(agent=self._agent, app_name=self._app_name),
                "session_id": str(uuid.uuid4()),
                "history": [],  # [{"role": "user"|"agent", "text": str}]
            }
        return st_state[self.state_key]

    def send(self, st_state: dict, message: str) -> str:
        state = self._get_state(st_state)
        state["history"].append({"role": "user", "text": message})

        response, _ = asyncio.run(_run(
            runner=state["runner"],
            user_id="admin",
            session_id=state["session_id"],
            message=message,
        ))

        state["history"].append({"role": "agent", "text": response})
        return response

    def history(self, st_state: dict) -> list:
        return self._get_state(st_state)["history"]

    def reset(self, st_state: dict) -> None:
        if self.state_key in st_state:
            del st_state[self.state_key]
