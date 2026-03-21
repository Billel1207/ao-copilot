"""Tests for app.services.llm — LLMService with Anthropic Claude."""
import json
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Helpers / Pydantic validators for testing
# ---------------------------------------------------------------------------

class SampleValidator(BaseModel):
    title: str
    score: int


class StrictValidator(BaseModel):
    name: str
    value: float


# ---------------------------------------------------------------------------
# _build_system_blocks
# ---------------------------------------------------------------------------

class TestBuildSystemBlocks:
    def test_cache_true_returns_list(self):
        from app.services.llm import _build_system_blocks
        result = _build_system_blocks("You are an assistant.", cache=True)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "You are an assistant."
        assert result[0]["cache_control"] == {"type": "ephemeral"}

    def test_cache_false_returns_string(self):
        from app.services.llm import _build_system_blocks
        result = _build_system_blocks("Hello", cache=False)
        assert result == "Hello"

    def test_default_cache_is_true(self):
        from app.services.llm import _build_system_blocks
        result = _build_system_blocks("sys prompt")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# LLMService.__init__
# ---------------------------------------------------------------------------

class TestLLMServiceInit:
    @patch("app.services.llm.anthropic_sdk")
    def test_init_creates_client(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        mock_anthropic.Anthropic.assert_called_once()
        assert svc.provider == "anthropic"
        assert svc._usage_accumulator == []


# ---------------------------------------------------------------------------
# _parse_json_response
# ---------------------------------------------------------------------------

class TestParseJsonResponse:
    @patch("app.services.llm.anthropic_sdk")
    def test_parse_valid_json(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        result = svc._parse_json_response('{"key": "value"}', "end_turn")
        assert result == {"key": "value"}

    @patch("app.services.llm.anthropic_sdk")
    def test_parse_json_in_markdown_fencing(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        raw = '```json\n{"key": "value"}\n```'
        result = svc._parse_json_response(raw, "end_turn")
        assert result == {"key": "value"}

    @patch("app.services.llm.anthropic_sdk")
    def test_parse_json_with_surrounding_text(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        raw = 'Here is the result: {"a": 1} done.'
        result = svc._parse_json_response(raw, "end_turn")
        assert result == {"a": 1}

    @patch("app.services.llm.anthropic_sdk")
    def test_parse_invalid_json_raises(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        with pytest.raises(ValueError, match="non-JSON"):
            svc._parse_json_response("not json at all", "end_turn")

    @patch("app.services.llm.anthropic_sdk")
    def test_parse_truncated_response(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        raw = '{"items": [{"name": "a"}, {"name": "b"'
        # stop_reason=max_tokens triggers repair
        result = svc._parse_json_response(raw, "max_tokens")
        assert "items" in result


# ---------------------------------------------------------------------------
# _repair_truncated_json
# ---------------------------------------------------------------------------

class TestRepairTruncatedJson:
    def test_repair_missing_closing_brace(self):
        from app.services.llm import LLMService
        raw = '{"key": "value"'
        repaired = LLMService._repair_truncated_json(raw)
        parsed = json.loads(repaired)
        assert parsed == {"key": "value"}

    def test_repair_missing_closing_bracket(self):
        from app.services.llm import LLMService
        raw = '{"items": [1, 2, 3'
        repaired = LLMService._repair_truncated_json(raw)
        parsed = json.loads(repaired)
        # Repair may truncate at different points — just verify it's valid JSON with items list
        assert isinstance(parsed["items"], list)
        assert len(parsed["items"]) >= 2

    def test_repair_truncated_value_after_comma(self):
        from app.services.llm import LLMService
        raw = '{"a": 1, "b": "trunc'
        repaired = LLMService._repair_truncated_json(raw)
        parsed = json.loads(repaired)
        assert parsed["a"] == 1

    def test_repair_with_markdown_fencing(self):
        from app.services.llm import LLMService
        raw = '```json\n{"x": 1}\n```'
        repaired = LLMService._repair_truncated_json(raw)
        parsed = json.loads(repaired)
        assert parsed == {"x": 1}


# ---------------------------------------------------------------------------
# complete_json (calls _anthropic_json internally)
# ---------------------------------------------------------------------------

class TestCompleteJson:
    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_returns_parsed(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        # Mock the API response
        mock_content = MagicMock()
        mock_content.text = '{"title": "Test", "score": 42}'
        mock_content.type = "text"
        mock_usage = MagicMock()
        mock_usage.input_tokens = 100
        mock_usage.output_tokens = 50
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage

        svc._anthropic.messages.create.return_value = mock_response

        result = svc.complete_json("system", "user")
        assert result == {"title": "Test", "score": 42}

    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_with_required_keys_pass(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_content = MagicMock()
        mock_content.text = '{"title": "OK", "score": 10}'
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        svc._anthropic.messages.create.return_value = mock_response

        result = svc.complete_json("sys", "usr", required_keys=["title", "score"])
        assert result["title"] == "OK"

    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_with_required_keys_fail(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_content = MagicMock()
        mock_content.text = '{"title": "OK"}'
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        svc._anthropic.messages.create.return_value = mock_response

        with pytest.raises(ValueError, match="manquantes"):
            svc.complete_json("sys", "usr", required_keys=["title", "missing_key"])

    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_with_pydantic_validator(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_content = MagicMock()
        mock_content.text = '{"title": "Hello", "score": 99}'
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        svc._anthropic.messages.create.return_value = mock_response

        result = svc.complete_json("sys", "usr", validator=SampleValidator)
        assert result["title"] == "Hello"
        assert result["score"] == 99

    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_pydantic_validation_fails(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_content = MagicMock()
        mock_content.text = '{"wrong_field": "nope"}'
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.stop_reason = "end_turn"
        mock_response.usage = mock_usage
        svc._anthropic.messages.create.return_value = mock_response

        with pytest.raises(ValueError, match="non conforme"):
            svc.complete_json("sys", "usr", validator=SampleValidator)


# ---------------------------------------------------------------------------
# chat_text
# ---------------------------------------------------------------------------

class TestChatText:
    @patch("app.services.llm.anthropic_sdk")
    def test_chat_text_returns_string(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_content = MagicMock()
        mock_content.text = "The answer is 42."
        mock_usage = MagicMock()
        mock_usage.input_tokens = 50
        mock_usage.output_tokens = 20
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_response.usage = mock_usage
        svc._anthropic.messages.create.return_value = mock_response

        result = svc.chat_text("system prompt", "user prompt")
        assert result == "The answer is 42."


# ---------------------------------------------------------------------------
# Usage tracking
# ---------------------------------------------------------------------------

class TestUsageTracking:
    @patch("app.services.llm.anthropic_sdk")
    def test_usage_accumulator(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_response = MagicMock()
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50
        mock_response.usage.cache_read_input_tokens = 30
        mock_response.usage.cache_creation_input_tokens = 10

        svc._track_usage(mock_response, step="test")
        assert len(svc._usage_accumulator) == 1
        assert svc._usage_accumulator[0]["step"] == "test"
        assert svc._usage_accumulator[0]["input_tokens"] == 100

    @patch("app.services.llm.anthropic_sdk")
    def test_get_usage_summary_with_data(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_response = MagicMock()
        mock_response.usage.input_tokens = 1000
        mock_response.usage.output_tokens = 500
        mock_response.usage.cache_read_input_tokens = 200
        mock_response.usage.cache_creation_input_tokens = 0

        svc._track_usage(mock_response, step="s1")
        svc._track_usage(mock_response, step="s2")

        summary = svc.get_usage_summary()
        assert summary["total_input"] == 2000
        assert summary["total_output"] == 1000
        assert summary["total_cached"] == 400
        assert summary["steps"] == 2
        assert summary["estimated_cost_eur"] > 0
        # After summary, accumulator is cleared
        assert svc._usage_accumulator == []

    @patch("app.services.llm.anthropic_sdk")
    def test_get_usage_summary_empty(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        summary = svc.get_usage_summary()
        assert summary["total_input"] == 0
        assert summary["estimated_cost_eur"] == 0.0

    @patch("app.services.llm.anthropic_sdk")
    def test_reset_usage(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        svc._usage_accumulator = [{"step": "dummy"}]
        svc.reset_usage()
        assert svc._usage_accumulator == []


# ---------------------------------------------------------------------------
# get_model_name
# ---------------------------------------------------------------------------

class TestGetModelName:
    @patch("app.services.llm.anthropic_sdk")
    def test_model_name(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()
        assert svc.get_model_name().startswith("anthropic:")


# ---------------------------------------------------------------------------
# Batch API
# ---------------------------------------------------------------------------

class TestBatchApi:
    @patch("app.services.llm.anthropic_sdk")
    def test_create_batch(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_batch = MagicMock()
        mock_batch.id = "batch_123"
        svc._anthropic.messages.batches.create.return_value = mock_batch

        result = svc.create_batch([
            {"custom_id": "req1", "system": "sys", "user": "usr"},
        ])
        assert result == "batch_123"
        svc._anthropic.messages.batches.create.assert_called_once()

    @patch("app.services.llm.anthropic_sdk")
    def test_get_batch_status(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_batch = MagicMock()
        mock_batch.id = "batch_456"
        mock_batch.processing_status = "completed"
        mock_batch.request_counts.processing = 0
        mock_batch.request_counts.succeeded = 5
        mock_batch.request_counts.errored = 0
        mock_batch.created_at = "2025-01-01T00:00:00"
        mock_batch.ended_at = "2025-01-01T01:00:00"

        svc._anthropic.messages.batches.retrieve.return_value = mock_batch

        result = svc.get_batch_status("batch_456")
        assert result["status"] == "completed"
        assert result["request_counts"]["succeeded"] == 5


# ---------------------------------------------------------------------------
# stream_chat_text
# ---------------------------------------------------------------------------

class TestStreamChatText:
    @patch("app.services.llm.anthropic_sdk")
    def test_stream_yields_tokens(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello", " world", "!"])
        svc._anthropic.messages.stream.return_value = mock_stream

        tokens = list(svc.stream_chat_text("sys", "usr"))
        assert tokens == ["Hello", " world", "!"]

    @patch("app.services.llm.anthropic_sdk")
    def test_stream_error_yields_error_message(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        svc._anthropic.messages.stream.side_effect = Exception("connection lost")

        tokens = list(svc.stream_chat_text("sys", "usr"))
        assert len(tokens) == 1
        assert "Erreur" in tokens[0]


# ---------------------------------------------------------------------------
# _build_user_blocks
# ---------------------------------------------------------------------------

class TestBuildUserBlocks:
    def test_short_text_returns_string(self):
        from app.services.llm import _build_user_blocks
        result = _build_user_blocks("short text", cache=True)
        assert isinstance(result, str)
        assert result == "short text"

    def test_long_text_returns_cached_blocks(self):
        from app.services.llm import _build_user_blocks
        long_text = "x" * 2000
        result = _build_user_blocks(long_text, cache=True)
        assert isinstance(result, list)
        assert result[0]["cache_control"] == {"type": "ephemeral"}
        assert result[0]["text"] == long_text

    def test_cache_false_returns_string_always(self):
        from app.services.llm import _build_user_blocks
        long_text = "x" * 2000
        result = _build_user_blocks(long_text, cache=False)
        assert isinstance(result, str)

    def test_exactly_1024_chars_returns_cached_blocks(self):
        from app.services.llm import _build_user_blocks
        text = "a" * 1024
        result = _build_user_blocks(text, cache=True)
        # len(1024) is NOT < 1024, so it gets cached as a list
        assert isinstance(result, list)

    def test_1023_chars_returns_string(self):
        from app.services.llm import _build_user_blocks
        text = "a" * 1023
        result = _build_user_blocks(text, cache=True)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# _get_openai
# ---------------------------------------------------------------------------

class TestGetOpenai:
    def test_returns_none_when_no_api_key(self):
        import app.services.llm as llm_mod
        llm_mod._openai_client = None  # reset
        with patch.object(llm_mod.settings, "OPENAI_API_KEY", ""):
            result = llm_mod._get_openai()
            assert result is None

    def test_returns_client_when_key_set(self):
        import app.services.llm as llm_mod
        llm_mod._openai_client = None  # reset
        mock_openai_mod = MagicMock()
        mock_client = MagicMock()
        mock_openai_mod.OpenAI.return_value = mock_client
        with patch.object(llm_mod.settings, "OPENAI_API_KEY", "sk-test123"), \
             patch.dict("sys.modules", {"openai": mock_openai_mod}):
            result = llm_mod._get_openai()
            assert result is mock_client
        llm_mod._openai_client = None  # cleanup

    def test_returns_none_on_import_error(self):
        import app.services.llm as llm_mod
        llm_mod._openai_client = None
        with patch.object(llm_mod.settings, "OPENAI_API_KEY", "sk-test"), \
             patch.dict("sys.modules", {"openai": None}):
            # None in sys.modules causes ImportError
            result = llm_mod._get_openai()
            assert result is None
        llm_mod._openai_client = None


# ---------------------------------------------------------------------------
# OpenAI fallbacks
# ---------------------------------------------------------------------------

class TestOpenAIFallbacks:
    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_json_fallback_returns_none_when_no_client(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_get_openai.return_value = None
        svc = LLMService()
        result = svc._openai_json_fallback("sys", "usr")
        assert result is None

    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_json_fallback_success(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_client = MagicMock()
        mock_get_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"result": "ok"}'
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70
        mock_client.chat.completions.create.return_value = mock_response

        svc = LLMService()
        result = svc._openai_json_fallback("sys", "usr")
        assert result == {"result": "ok"}
        assert len(svc._usage_accumulator) == 1
        assert svc._usage_accumulator[0]["step"] == "openai_fallback"

    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_json_fallback_exception_returns_none(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_client = MagicMock()
        mock_get_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API error")

        svc = LLMService()
        result = svc._openai_json_fallback("sys", "usr")
        assert result is None

    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_text_fallback_returns_none_when_no_client(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_get_openai.return_value = None
        svc = LLMService()
        result = svc._openai_text_fallback("sys", "usr")
        assert result is None

    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_text_fallback_success(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_client = MagicMock()
        mock_get_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from GPT"
        mock_response.usage.prompt_tokens = 30
        mock_response.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_response

        svc = LLMService()
        result = svc._openai_text_fallback("sys", "usr", max_tokens=512)
        assert result == "Hello from GPT"

    @patch("app.services.llm.anthropic_sdk")
    @patch("app.services.llm._get_openai")
    def test_openai_text_fallback_exception_returns_none(self, mock_get_openai, mock_anthropic):
        from app.services.llm import LLMService
        mock_client = MagicMock()
        mock_get_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = RuntimeError("down")

        svc = LLMService()
        result = svc._openai_text_fallback("sys", "usr")
        assert result is None


# ---------------------------------------------------------------------------
# chat_text with fallback
# ---------------------------------------------------------------------------

class TestChatTextFallback:
    @patch("app.services.llm.anthropic_sdk")
    def test_chat_text_fallback_to_openai(self, mock_anthropic):
        from app.services.llm import LLMService
        import pybreaker
        svc = LLMService()

        svc._anthropic_chat_text = MagicMock(side_effect=pybreaker.CircuitBreakerError(MagicMock()))
        svc._openai_text_fallback = MagicMock(return_value="OpenAI result")

        result = svc.chat_text("sys", "usr")
        assert result == "OpenAI result"

    @patch("app.services.llm.anthropic_sdk")
    def test_chat_text_fallback_none_reraises(self, mock_anthropic):
        from app.services.llm import LLMService
        import pybreaker
        svc = LLMService()

        svc._anthropic_chat_text = MagicMock(side_effect=pybreaker.CircuitBreakerError(MagicMock()))
        svc._openai_text_fallback = MagicMock(return_value=None)

        with pytest.raises(pybreaker.CircuitBreakerError):
            svc.chat_text("sys", "usr")


# ---------------------------------------------------------------------------
# complete_json with fallback
# ---------------------------------------------------------------------------

class TestCompleteJsonFallback:
    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_fallback_to_openai(self, mock_anthropic):
        from app.services.llm import LLMService
        import pybreaker
        svc = LLMService()

        svc._anthropic_json = MagicMock(side_effect=pybreaker.CircuitBreakerError(MagicMock()))
        svc._openai_json_fallback = MagicMock(return_value={"key": "fallback"})

        result = svc.complete_json("sys", "usr")
        assert result == {"key": "fallback"}

    @patch("app.services.llm.anthropic_sdk")
    def test_complete_json_fallback_none_reraises(self, mock_anthropic):
        from app.services.llm import LLMService
        import pybreaker
        svc = LLMService()

        svc._anthropic_json = MagicMock(side_effect=pybreaker.CircuitBreakerError(MagicMock()))
        svc._openai_json_fallback = MagicMock(return_value=None)

        with pytest.raises(pybreaker.CircuitBreakerError):
            svc.complete_json("sys", "usr")


# ---------------------------------------------------------------------------
# get_batch_results
# ---------------------------------------------------------------------------

class TestGetBatchResults:
    @patch("app.services.llm.anthropic_sdk")
    def test_get_batch_results_success_and_error(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        # Successful entry
        success_entry = MagicMock()
        success_entry.custom_id = "req1"
        success_entry.result.type = "succeeded"
        success_entry.result.message.content = [MagicMock(text='{"answer": 42}')]
        success_entry.result.message.stop_reason = "end_turn"

        # Error entry
        error_entry = MagicMock()
        error_entry.custom_id = "req2"
        error_entry.result.type = "errored"

        svc._anthropic.messages.batches.results.return_value = [success_entry, error_entry]

        results = svc.get_batch_results("batch_789")
        assert len(results) == 2
        assert results[0]["custom_id"] == "req1"
        assert results[0]["status"] == "success"
        assert results[0]["result"]["answer"] == 42
        assert results[1]["custom_id"] == "req2"
        assert results[1]["status"] == "error"
        assert results[1]["result"] is None

    @patch("app.services.llm.anthropic_sdk")
    def test_get_batch_results_json_parse_failure(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        entry = MagicMock()
        entry.custom_id = "req_bad"
        entry.result.type = "succeeded"
        entry.result.message.content = [MagicMock(text="not json at all!!!")]
        entry.result.message.stop_reason = "end_turn"

        svc._anthropic.messages.batches.results.return_value = [entry]

        results = svc.get_batch_results("batch_x")
        assert results[0]["status"] == "success"
        assert "error" in results[0]["result"]


# ---------------------------------------------------------------------------
# get_batch_status with ended_at=None
# ---------------------------------------------------------------------------

class TestGetBatchStatusPending:
    @patch("app.services.llm.anthropic_sdk")
    def test_batch_status_in_progress(self, mock_anthropic):
        from app.services.llm import LLMService
        svc = LLMService()

        mock_batch = MagicMock()
        mock_batch.id = "batch_pending"
        mock_batch.processing_status = "in_progress"
        mock_batch.request_counts.processing = 3
        mock_batch.request_counts.succeeded = 2
        mock_batch.request_counts.errored = 0
        mock_batch.created_at = "2025-06-01T00:00:00"
        mock_batch.ended_at = None

        svc._anthropic.messages.batches.retrieve.return_value = mock_batch

        result = svc.get_batch_status("batch_pending")
        assert result["status"] == "in_progress"
        assert result["ended_at"] is None
        assert result["request_counts"]["total"] == 5
