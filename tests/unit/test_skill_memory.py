import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent.parent))

import app.skill_memory as sm


def test_load_agent_skills_missing_file(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        result = sm.load_agent_skills("nonexistent_agent")
    assert result == ""


def test_append_skill_entry_creates_file(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        result = sm.append_skill_entry("test_agent", "요약 내용", "트리거 조건", "예시 질문")
    assert result["status"] == "appended"
    skill_file = tmp_path / "test_agent_skills.md"
    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")
    assert "요약 내용" in content
    assert "트리거 조건" in content


def test_append_skill_entry_appends_multiple(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        sm.append_skill_entry("test_agent", "요약1", "트리거1", "질문1")
        sm.append_skill_entry("test_agent", "요약2", "트리거2", "질문2")
    content = (tmp_path / "test_agent_skills.md").read_text(encoding="utf-8")
    assert content.count("\n## [") == 2


def test_load_agent_skills_returns_content(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        sm.append_skill_entry("test_agent", "로드 테스트", "트리거", "질문")
        result = sm.load_agent_skills("test_agent")
    assert "로드 테스트" in result


def test_list_all_skills_counts_entries(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        sm.append_skill_entry("agent_a", "요약a", "트리거a", "질문a")
        sm.append_skill_entry("agent_b", "요약b1", "트리거b1", "질문b1")
        sm.append_skill_entry("agent_b", "요약b2", "트리거b2", "질문b2")
        result = sm.list_all_skills()
    assert result["total_entries"] == 3
    agents = {a["agent"]: a["entries"] for a in result["agents"]}
    assert agents["agent_a"] == 1
    assert agents["agent_b"] == 2


def test_skill_appender_max_limit_returns_skipped(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        appender = sm.make_skill_appender("limit_test_agent")
        for i in range(sm._MAX_SKILL_ENTRIES):
            appender(f"요약{i}", f"트리거{i}", f"질문{i}")
        result = appender("초과 요약", "초과 트리거", "초과 질문")
    assert result["status"] == "skipped"
    assert "상한" in result["reason"]


def test_skill_appender_below_limit_appends(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path):
        appender = sm.make_skill_appender("normal_agent")
        result = appender("정상 요약", "정상 트리거", "정상 질문")
    assert result["status"] == "appended"
    assert result["agent"] == "normal_agent"


def test_list_all_skills_empty_dir(tmp_path):
    with patch.object(sm, "AGENTS_DIR", tmp_path / "missing"):
        result = sm.list_all_skills()
    assert result["total_entries"] == 0
    assert result["agents"] == []
