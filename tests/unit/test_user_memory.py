import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent.parent))

import app.user_memory as um
import app.callbacks as cb


# ── save / load ───────────────────────────────────────────────────────────────

def test_save_and_load_preferred_style(tmp_path):
    with patch.object(um, "MEMORY_DIR", tmp_path):
        um.save_user_memory("user1", {
            "investment_profile": "위험회피형",
            "literacy_level": "기초",
            "preferred_style": "brief",
        })
        result = um.load_user_memory("user1")
    assert result["preferred_style"] == "brief"
    assert result["investment_profile"] == "위험회피형"


def test_save_style_only(tmp_path):
    """preferred_style만 있어도 저장된다."""
    with patch.object(um, "MEMORY_DIR", tmp_path):
        um.save_user_memory("user2", {"preferred_style": "detailed"})
        result = um.load_user_memory("user2")
    assert result["preferred_style"] == "detailed"


def test_no_save_without_meaningful_data(tmp_path):
    """저장할 항목이 전혀 없으면 파일을 만들지 않는다."""
    with patch.object(um, "MEMORY_DIR", tmp_path):
        um.save_user_memory("user3", {})
    assert not (tmp_path / "user3.md").exists()


def test_style_label_in_file(tmp_path):
    """저장된 파일에 한국어 레이블이 포함된다."""
    with patch.object(um, "MEMORY_DIR", tmp_path):
        um.save_user_memory("user4", {"preferred_style": "example"})
    content = (tmp_path / "user4.md").read_text(encoding="utf-8")
    assert "예시 포함" in content


def test_eval_user_not_saved(tmp_path):
    """eval 사용자 prefix는 저장되지 않는다."""
    with patch.object(um, "MEMORY_DIR", tmp_path):
        um.save_user_memory("inv_user_001", {"preferred_style": "brief"})
    assert not (tmp_path / "inv_user_001.md").exists()


# ── _detect_style ─────────────────────────────────────────────────────────────

def test_detect_style_brief():
    assert cb._detect_style("간단히 설명해줘") == "brief"
    assert cb._detect_style("핵심만 알려줘") == "brief"
    assert cb._detect_style("짧게 말해줘") == "brief"


def test_detect_style_detailed():
    assert cb._detect_style("자세히 알고 싶어요") == "detailed"
    assert cb._detect_style("구체적으로 설명해줘") == "detailed"
    assert cb._detect_style("더 설명해줘") == "detailed"


def test_detect_style_example():
    assert cb._detect_style("예시를 들어 설명해줘") == "example"
    assert cb._detect_style("예를 들어 알려줘") == "example"
    assert cb._detect_style("사례로 보여줘") == "example"


def test_detect_style_no_match():
    assert cb._detect_style("IRP 세액공제 한도가 얼마예요?") == ""
    assert cb._detect_style("") == ""
