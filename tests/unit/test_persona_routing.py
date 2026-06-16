import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).parent.parent.parent))

import app.callbacks as cb


# ── _build_fewshot_block ──────────────────────────────────────────────────────

def test_fewshot_block_contains_all_personas():
    block = cb._build_fewshot_block()
    assert block != "", "퓨샷 파일이 로드되지 않았습니다 (data/personas/few_shot_examples.json)"
    for persona in ["고령층", "사회초년생", "주부", "직장인", "중장년"]:
        assert f"[{persona}]" in block, f"{persona} 섹션 없음"


def test_fewshot_block_empty_when_file_missing(tmp_path):
    with patch.object(cb, "_FEWSHOT_FILE", tmp_path / "nonexistent.json"):
        result = cb._build_fewshot_block()
    assert result == ""


def test_fewshot_block_format(tmp_path):
    """페르소나별 타이틀이 들여쓰기(  - )로 목록화돼야 한다."""
    fake = '[{"persona": "직장인", "title": "연말정산 환급 계산"}]'
    fake_file = tmp_path / "few_shot_examples.json"
    fake_file.write_text(fake, encoding="utf-8")
    with patch.object(cb, "_FEWSHOT_FILE", fake_file):
        result = cb._build_fewshot_block()
    assert "[직장인]" in result
    assert "  - 연말정산 환급 계산" in result


# ── _detect_persona ───────────────────────────────────────────────────────────

def _mock_llm(response_text: str):
    """LLM이 response_text를 반환하도록 genai.Client를 mock합니다."""
    mock_resp = MagicMock()
    mock_resp.text = response_text
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_resp
    return mock_client


def test_detect_persona_valid_persona():
    """LLM이 유효한 페르소나 반환 시 그대로 반환한다."""
    mock_client = _mock_llm("고령층")
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client", return_value=mock_client):
        result = cb._detect_persona("저 65세인데 적금 추천 부탁드려요")
    assert result == "고령층"


def test_detect_persona_invalid_llm_response_returns_empty():
    """LLM이 선택지에 없는 값 반환 시 빈 문자열을 반환한다."""
    mock_client = _mock_llm("청소년")
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client", return_value=mock_client):
        result = cb._detect_persona("어떤 발화")
    assert result == ""


def test_detect_persona_moreom_returns_empty():
    """LLM이 '모름' 반환 시 빈 문자열을 반환한다."""
    mock_client = _mock_llm("모름")
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client", return_value=mock_client):
        result = cb._detect_persona("어떤 발화")
    assert result == ""


def test_detect_persona_llm_exception_returns_empty():
    """LLM 호출 중 예외 발생 시 빈 문자열을 반환한다."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API 오류")
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client", return_value=mock_client):
        result = cb._detect_persona("일반 금융 질문")
    assert result == ""


def test_detect_persona_empty_message_returns_empty():
    """빈 메시지 입력 시 LLM 호출 없이 빈 문자열을 반환한다."""
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client") as mock_cls:
        result = cb._detect_persona("")
    mock_cls.assert_not_called()
    assert result == ""


def test_detect_persona_no_fewshot_returns_empty():
    """_FEWSHOT_BLOCK이 비어 있으면 LLM 호출 없이 빈 문자열을 반환한다."""
    with patch.object(cb, "_FEWSHOT_BLOCK", ""), \
         patch.object(cb.genai, "Client") as mock_cls:
        result = cb._detect_persona("65세 연금 질문")
    mock_cls.assert_not_called()
    assert result == ""


def test_detect_persona_strips_quotes():
    """LLM 응답에 따옴표가 붙어 있어도 올바르게 파싱한다."""
    mock_client = _mock_llm('"직장인"')
    with patch.object(cb, "_FEWSHOT_BLOCK", "퓨샷 블록"), \
         patch.object(cb.genai, "Client", return_value=mock_client):
        result = cb._detect_persona("연말정산 환급금 알고 싶어요")
    assert result == "직장인"


# ── 상수 검증 ─────────────────────────────────────────────────────────────────

def test_valid_personas_set():
    """_VALID_PERSONAS 집합이 5개 페르소나를 모두 포함해야 한다."""
    expected = {"고령층", "사회초년생", "주부", "직장인", "중장년"}
    assert cb._VALID_PERSONAS == expected


def test_persona_hints_keys_match_valid_personas():
    """_PERSONA_HINTS 키가 _VALID_PERSONAS와 일치해야 한다."""
    assert set(cb._PERSONA_HINTS.keys()) == cb._VALID_PERSONAS
