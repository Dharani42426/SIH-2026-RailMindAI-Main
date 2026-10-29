# ═══════════════════════════════════════════════════════════════
# RailMind AI — Ollama NLP Integration Tests
# Tests for Qwen3-235B integration with regex fallback
# ═══════════════════════════════════════════════════════════════

import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta


# ─────────────────────────────────────────────────────────────
# Helper: create NLPProcessor with specific provider config
# ─────────────────────────────────────────────────────────────

def _make_processor(provider="pattern"):
    """
    Create NLPProcessor with a mocked config so tests don't depend
    on .env or a running Ollama server.
    """
    mock_settings = MagicMock()
    mock_settings.NLP_PROVIDER = provider
    mock_settings.OLLAMA_BASE_URL = "http://127.0.0.1:11434"
    mock_settings.OLLAMA_MODEL = "qwen3:235b"
    mock_settings.OLLAMA_TIMEOUT_SECONDS = 30

    with patch("config.get_settings", return_value=mock_settings):
        from services.nlp_processor import NLPProcessor
        return NLPProcessor()


def _mock_ollama_response(content: dict):
    """Create a mock requests.Response for Ollama API."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "message": {
            "role": "assistant",
            "content": json.dumps(content),
        }
    }
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 1: Regex-only mode (NLP_PROVIDER=pattern)
# Ensures existing behavior is completely preserved
# ═══════════════════════════════════════════════════════════════

class TestRegexOnlyMode:
    """Verify that NLP_PROVIDER=pattern works identically to original."""

    def test_query_blocks_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Show available blocks for Kalyan-Kasara section")
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["entities"]["section"] == "KYN-KAS"

    def test_query_tasks_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Top 5 critical tasks")
        assert result["intent"] == "QUERY_TASKS"
        assert result["entities"]["severity"] == "CRITICAL"
        assert result["entities"]["limit"] == 5

    def test_schedule_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Schedule emergency block for OHE repair")
        assert result["intent"] == "SCHEDULE"
        assert result["entities"]["department"] == "TRD"

    def test_status_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Status of kasara section")
        assert result["intent"] == "STATUS"
        assert result["entities"]["section"] == "KYN-KAS"

    def test_predict_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Predict failures for Kalyan section")
        assert result["intent"] == "PREDICT"
        assert result["entities"]["section"] == "TNA-KYN"

    def test_hindi_command(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Kalyan section mein pending tasks dikhao")
        assert result["intent"] == "QUERY_TASKS"
        assert result["entities"]["section"] == "TNA-KYN"

    def test_help_intent(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Help")
        assert result["intent"] == "HELP"

    def test_km_extraction(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Schedule block near KM 65")
        assert result["entities"]["km_location"] == 65.0

    def test_api_action_mapping(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Show available blocks")
        assert result["api_action"] == "/api/blocks/available"

    def test_response_text_generated(self):
        proc = _make_processor("pattern")
        result = proc.process_command("Show available blocks for Kasara")
        assert "Fetching available block windows" in result["response_text"]


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 2: Ollama mode — graceful fallback on errors
# ═══════════════════════════════════════════════════════════════

class TestOllamaFallback:
    """Verify graceful fallback to regex when Ollama fails."""

    @patch("services.nlp_processor.requests")
    def test_connection_refused_falls_back(self, mock_requests):
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.ConnectionError("Connection refused")
        proc = _make_processor("ollama")
        result = proc.process_command("Show available blocks for Kalyan-Kasara")
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["entities"]["section"] == "KYN-KAS"

    @patch("services.nlp_processor.requests")
    def test_timeout_falls_back(self, mock_requests):
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.Timeout("Request timed out")
        proc = _make_processor("ollama")
        result = proc.process_command("Show available blocks for Kasara")
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["entities"]["section"] == "KYN-KAS"

    @patch("services.nlp_processor.requests")
    def test_http_error_falls_back(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("500 Server Error")
        mock_requests.post.return_value = mock_resp
        proc = _make_processor("ollama")
        result = proc.process_command("Top 5 critical tasks")
        assert result["intent"] == "QUERY_TASKS"
        assert result["entities"]["severity"] == "CRITICAL"

    @patch("services.nlp_processor.requests")
    def test_invalid_json_falls_back(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {"content": "This is not JSON at all, sorry!"}
        }
        mock_requests.post.return_value = mock_resp
        proc = _make_processor("ollama")
        result = proc.process_command("Show available blocks for Kasara")
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["entities"]["section"] == "KYN-KAS"

    @patch("services.nlp_processor.requests")
    def test_empty_response_falls_back(self, mock_requests):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"message": {"content": ""}}
        mock_requests.post.return_value = mock_resp
        proc = _make_processor("ollama")
        result = proc.process_command("Help")
        assert result["intent"] == "HELP"

    @patch("services.nlp_processor.requests")
    def test_invalid_intent_falls_back(self, mock_requests):
        mock_requests.post.return_value = _mock_ollama_response({
            "intent": "DESTROY_EVERYTHING",
            "section": None,
        })
        proc = _make_processor("ollama")
        result = proc.process_command("Top 5 critical tasks")
        # Falls back to regex because intent is invalid
        assert result["intent"] == "QUERY_TASKS"


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 3: Ollama mode — successful LLM integration
# ═══════════════════════════════════════════════════════════════

class TestOllamaSuccess:
    """Verify correct behavior when Ollama returns valid responses."""

    @patch("services.nlp_processor.requests")
    def test_basic_query_blocks(self, mock_requests):
        mock_requests.post.return_value = _mock_ollama_response({
            "intent": "QUERY_BLOCKS",
            "section": "KYN-KAS",
            "department": "TRD",
            "timeframe": "next week",
            "severity": None,
            "km_location": None,
            "limit": None,
        })
        proc = _make_processor("ollama")
        result = proc.process_command(
            "Kasara section mein OHE ka kaam hai, agle hafte koi suitable block batao"
        )
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["entities"]["section"] == "KYN-KAS"
        assert result["entities"]["department"] == "TRD"

    @patch("services.nlp_processor.requests")
    def test_hindi_query_tasks(self, mock_requests):
        mock_requests.post.return_value = _mock_ollama_response({
            "intent": "QUERY_TASKS",
            "section": "KYN-KAS",
            "department": None,
            "timeframe": None,
            "severity": None,
            "km_location": None,
            "limit": None,
        })
        proc = _make_processor("ollama")
        result = proc.process_command("Kasara section mein kya pending hai?")
        assert result["intent"] == "QUERY_TASKS"
        assert result["entities"]["section"] == "KYN-KAS"

    @patch("services.nlp_processor.requests")
    def test_signal_status(self, mock_requests):
        mock_requests.post.return_value = _mock_ollama_response({
            "intent": "STATUS",
            "section": None,
            "department": "SNT",
            "timeframe": None,
            "severity": None,
            "km_location": None,
            "limit": None,
        })
        proc = _make_processor("ollama")
        result = proc.process_command("signal ka status batao")
        assert result["intent"] == "STATUS"
        assert result["entities"]["department"] == "SNT"

    @patch("services.nlp_processor.requests")
    def test_markdown_fenced_json_parsed(self, mock_requests):
        """Ollama sometimes wraps JSON in markdown code fences."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "message": {
                "content": '```json\n{"intent": "QUERY_TASKS", "section": "KYN-KAS", '
                           '"department": null, "severity": "CRITICAL", '
                           '"timeframe": null, "km_location": null, "limit": null}\n```'
            }
        }
        mock_requests.post.return_value = mock_resp
        proc = _make_processor("ollama")
        result = proc.process_command("Kasara mein critical tasks dikhao")
        assert result["intent"] == "QUERY_TASKS"
        assert result["entities"]["section"] == "KYN-KAS"
        assert result["entities"]["severity"] == "CRITICAL"


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 4: Entity merging logic
# ═══════════════════════════════════════════════════════════════

class TestEntityMerging:
    """Verify regex entities have priority over LLM entities."""

    def test_regex_section_wins_over_llm(self):
        proc = _make_processor("pattern")
        regex_ent = {"section": "KYN-KAS", "section_alias": "kasara"}
        llm_ent = {"section": "TNA-KYN", "department": "TRD"}
        merged = proc._merge_entities(regex_ent, llm_ent)
        assert merged["section"] == "KYN-KAS"  # regex wins
        assert merged["department"] == "TRD"  # LLM fills gap

    def test_llm_fills_missing_department(self):
        proc = _make_processor("pattern")
        regex_ent = {"section": "KYN-KAS"}
        llm_ent = {"department": "SNT"}
        merged = proc._merge_entities(regex_ent, llm_ent)
        assert merged["section"] == "KYN-KAS"
        assert merged["department"] == "SNT"

    def test_regex_severity_wins(self):
        proc = _make_processor("pattern")
        regex_ent = {"severity": "CRITICAL"}
        llm_ent = {"severity": "LOW", "timeframe": "next week"}
        merged = proc._merge_entities(regex_ent, llm_ent)
        assert merged["severity"] == "CRITICAL"  # regex wins
        assert merged["timeframe"] == "next week"  # LLM fills gap

    def test_empty_llm_entities_preserves_regex(self):
        proc = _make_processor("pattern")
        regex_ent = {"section": "KYN-KAS", "department": "ENGG", "km_location": 65.0}
        llm_ent = {}
        merged = proc._merge_entities(regex_ent, llm_ent)
        assert merged == regex_ent

    def test_empty_regex_entities_uses_llm(self):
        proc = _make_processor("pattern")
        regex_ent = {}
        llm_ent = {"section": "KYN-KAS", "department": "TRD", "timeframe": "next week"}
        merged = proc._merge_entities(regex_ent, llm_ent)
        assert merged["section"] == "KYN-KAS"
        assert merged["department"] == "TRD"
        assert merged["timeframe"] == "next week"


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 5: LLM output validation
# ═══════════════════════════════════════════════════════════════

class TestLLMValidation:
    """Verify that invalid LLM outputs are properly rejected."""

    def test_invalid_section_discarded(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "intent": "QUERY_BLOCKS",
            "section": "INVALID-SECTION",
            "department": "TRD",
        })
        assert "section" not in entities
        assert entities["department"] == "TRD"

    def test_invalid_department_discarded(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "intent": "QUERY_TASKS",
            "section": "KYN-KAS",
            "department": "FAKE_DEPT",
        })
        assert entities["section"] == "KYN-KAS"
        assert "department" not in entities

    def test_invalid_severity_discarded(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "intent": "QUERY_TASKS",
            "severity": "SUPER_CRITICAL",
        })
        assert "severity" not in entities

    def test_null_values_handled(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "intent": "HELP",
            "section": None,
            "department": None,
            "severity": None,
            "timeframe": None,
            "km_location": None,
            "limit": None,
        })
        assert entities == {}

    def test_valid_km_location_kept(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "km_location": 65.5,
        })
        assert entities["km_location"] == 65.5

    def test_invalid_km_location_discarded(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({
            "km_location": "not a number",
        })
        assert "km_location" not in entities

    def test_valid_limit_kept(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({"limit": 10})
        assert entities["limit"] == 10

    def test_negative_limit_discarded(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({"limit": -5})
        assert "limit" not in entities

    def test_timeframe_generates_start_date(self):
        proc = _make_processor("pattern")
        entities = proc._validate_llm_entities({"timeframe": "next week"})
        assert entities["timeframe"] == "next week"
        expected_date = (date.today() + timedelta(days=7)).isoformat()
        assert entities["start_date"] == expected_date


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 6: System prompt coverage
# ═══════════════════════════════════════════════════════════════

class TestSystemPrompt:
    """Verify the system prompt includes all required domain grounding."""

    def test_prompt_contains_all_section_codes(self):
        proc = _make_processor("pattern")
        prompt = proc._build_ollama_system_prompt()
        for code in proc._valid_sections:
            assert code in prompt, f"Section code {code} missing from system prompt"

    def test_prompt_contains_all_intents(self):
        proc = _make_processor("pattern")
        prompt = proc._build_ollama_system_prompt()
        for intent in proc._valid_intents:
            assert intent in prompt, f"Intent {intent} missing from system prompt"

    def test_prompt_contains_department_keywords(self):
        proc = _make_processor("pattern")
        prompt = proc._build_ollama_system_prompt()
        assert "ENGG" in prompt
        assert "SNT" in prompt
        assert "TRD" in prompt
        assert "OHE" in prompt

    def test_prompt_contains_json_format(self):
        proc = _make_processor("pattern")
        prompt = proc._build_ollama_system_prompt()
        assert '"intent"' in prompt
        assert '"section"' in prompt

    def test_prompt_mentions_hindi(self):
        proc = _make_processor("pattern")
        prompt = proc._build_ollama_system_prompt()
        assert "Hindi" in prompt or "hindi" in prompt
        assert "Hinglish" in prompt or "hinglish" in prompt


# ═══════════════════════════════════════════════════════════════
# TEST GROUP 7: JSON parsing edge cases
# ═══════════════════════════════════════════════════════════════

class TestJsonParsing:
    """Verify _parse_llm_json handles various LLM output formats."""

    def test_clean_json(self):
        proc = _make_processor("pattern")
        result = proc._parse_llm_json('{"intent": "HELP"}')
        assert result["intent"] == "HELP"

    def test_json_with_fences(self):
        proc = _make_processor("pattern")
        result = proc._parse_llm_json('```json\n{"intent": "HELP"}\n```')
        assert result["intent"] == "HELP"

    def test_json_with_plain_fences(self):
        proc = _make_processor("pattern")
        result = proc._parse_llm_json('```\n{"intent": "HELP"}\n```')
        assert result["intent"] == "HELP"

    def test_json_with_whitespace(self):
        proc = _make_processor("pattern")
        result = proc._parse_llm_json('  \n{"intent": "HELP"}\n  ')
        assert result["intent"] == "HELP"

    def test_invalid_json_raises(self):
        proc = _make_processor("pattern")
        with pytest.raises(ValueError, match="Invalid JSON"):
            proc._parse_llm_json("This is not JSON at all and has no braces")

    def test_json_with_think_tags(self):
        """Qwen3 wraps reasoning in <think>...</think> tags."""
        proc = _make_processor("pattern")
        raw = '<think>\nLet me analyze this...\nThe intent is HELP.\n</think>\n\n{"intent": "HELP"}'
        result = proc._parse_llm_json(raw)
        assert result["intent"] == "HELP"

    def test_json_with_think_tags_no_opening(self):
        """Qwen3 sometimes omits the opening <think> tag."""
        proc = _make_processor("pattern")
        raw = 'Some reasoning text here...\n</think>\n\n{"intent": "QUERY_BLOCKS", "section": "KYN-KAS"}'
        result = proc._parse_llm_json(raw)
        assert result["intent"] == "QUERY_BLOCKS"
        assert result["section"] == "KYN-KAS"

    def test_json_with_think_tags_and_fences(self):
        """Qwen3 may combine think tags with markdown fences."""
        proc = _make_processor("pattern")
        raw = '<think>\nReasoning...\n</think>\n\n```json\n{"intent": "STATUS"}\n```'
        result = proc._parse_llm_json(raw)
        assert result["intent"] == "STATUS"

    def test_json_with_surrounding_text(self):
        """Extract JSON even when surrounded by extra text."""
        proc = _make_processor("pattern")
        raw = 'Here is the result:\n{"intent": "PREDICT"}\nDone.'
        result = proc._parse_llm_json(raw)
        assert result["intent"] == "PREDICT"
