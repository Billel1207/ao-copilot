"""Abstraction LLM — Anthropic Claude (principal) avec fallback OpenAI optionnel.

Features:
- Prompt caching (cache_control ephemeral) — 90% cheaper on cache hits
- Extended thinking for complex analyses (conflicts, CCAP, Go/No-Go)
- Circuit breaker (pybreaker) — fail-fast during API outages
- Tenacity retry with exponential backoff for transient errors
- Usage tracking (input/output/cached tokens) for cost monitoring
"""
import json
import structlog
from typing import Any

import anthropic as anthropic_sdk
import pybreaker
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = structlog.get_logger(__name__)


def _build_system_blocks(system: str, *, cache: bool = True) -> list[dict] | str:
    """Build system prompt with Anthropic prompt caching.

    When caching is enabled, returns a list of content blocks with
    cache_control ephemeral — Anthropic caches these server-side for 5 min.
    Cached tokens cost 90% less on read hits.
    """
    if not cache:
        return system
    return [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]

# Exceptions Anthropic qui méritent un retry (transitoires)
_RETRYABLE_EXCEPTIONS = (
    anthropic_sdk.RateLimitError,
    anthropic_sdk.InternalServerError,
    anthropic_sdk.APIConnectionError,
    anthropic_sdk.APITimeoutError,
)

# Circuit breaker — fail-fast after 5 consecutive failures, retry after 60s.
# Excludes BadRequestError (client-side, not transient).
_llm_breaker = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=60,
    exclude=[anthropic_sdk.BadRequestError],
    name="anthropic_llm",
)


class LLMService:
    def __init__(self):
        self._anthropic = anthropic_sdk.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL
        self.provider = "anthropic"
        # Accumulated usage for cost tracking (reset per analysis run)
        self._usage_accumulator: list[dict] = []

    def complete_json(
        self,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any] | None = None,
        required_keys: list[str] | None = None,
        validator: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """Appel LLM avec sortie JSON garantie + validation Pydantic optionnelle.

        Args:
            required_keys: Vérifie que ces clés existent dans la réponse.
            validator: Modèle Pydantic v2 pour validation stricte post-parsing.
                       Corrige automatiquement les valeurs hors-spec (enums, ranges, dates).
        """
        result = self._anthropic_json(system_prompt, user_prompt)

        # Validation de structure post-parsing (clés requises)
        if required_keys:
            missing = [k for k in required_keys if k not in result]
            if missing:
                raise ValueError(
                    f"Réponse LLM incomplète — clés manquantes: {missing}. "
                    f"Réponse reçue: {list(result.keys())}"
                )

        # Validation Pydantic stricte (normalise + corrige les valeurs)
        if validator:
            try:
                validated = validator.model_validate(result)
                result = validated.model_dump()
            except ValidationError as exc:
                logger.warning(
                    f"Validation Pydantic échouée ({validator.__name__}): {exc}. "
                    f"Tentative de parsing permissif..."
                )
                # Retry avec parsing permissif (mode="before")
                try:
                    validated = validator.model_validate(result, strict=False)
                    result = validated.model_dump()
                except ValidationError:
                    raise ValueError(
                        f"Sortie LLM non conforme au schéma {validator.__name__}: {exc}"
                    )

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        before_sleep=lambda rs: logger.warning(
            "LLM retry attempt %d after %s", rs.attempt_number, rs.outcome.exception()
        ),
    )
    @_llm_breaker
    def _anthropic_json(self, system: str, user: str) -> dict:
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            system=_build_system_blocks(system),
            messages=[{"role": "user", "content": user}],
        )
        self._track_usage(response, step="json")
        return self._parse_json_response(response.content[0].text, response.stop_reason)

    def _parse_json_response(self, raw: str, stop_reason: str) -> dict:
        """Parse JSON from LLM response with truncation repair."""
        import re

        if stop_reason == "max_tokens":
            logger.warning(
                "Réponse LLM tronquée (max_tokens=%d atteint). "
                "Tentative de réparation JSON...",
                settings.LLM_MAX_TOKENS,
            )
            raw = self._repair_truncated_json(raw)

        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]).strip()

        # Tentative 1 : parsing direct
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Tentative 2 : extraire le premier bloc JSON {...}
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Tentative 3 : réparation JSON tronqué
        repaired = self._repair_truncated_json(raw)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        raise ValueError(
            f"Réponse Anthropic non-JSON (modèle={self.model}, "
            f"stop_reason={stop_reason}): {raw[:300]!r}"
        )

    @staticmethod
    def _repair_truncated_json(raw: str) -> str:
        """Tente de réparer un JSON tronqué en fermant les accolades/crochets ouverts."""
        raw = raw.strip()
        # Supprimer markdown fencing si présent
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:]).strip()
            if raw.endswith("```"):
                raw = raw[:-3].strip()

        # Supprimer la dernière valeur probablement incomplète
        # (trouver le dernier séparateur valide: , ou : suivi de valeur tronquée)
        # D'abord, tronquer après le dernier élément complet
        last_comma = raw.rfind(",")
        last_brace = max(raw.rfind("}"), raw.rfind("]"))
        if last_comma > last_brace:
            # La dernière virgule est après le dernier crochet fermant
            # → il y a un élément tronqué après la virgule, le supprimer
            raw = raw[:last_comma]

        # Compter les accolades/crochets ouverts vs fermés
        open_braces = raw.count("{") - raw.count("}")
        open_brackets = raw.count("[") - raw.count("]")

        # Fermer dans l'ordre inverse
        raw += "]" * max(0, open_brackets)
        raw += "}" * max(0, open_braces)

        return raw

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        before_sleep=lambda rs: logger.warning(
            "LLM chat_text retry attempt %d after %s", rs.attempt_number, rs.outcome.exception()
        ),
    )
    @_llm_breaker
    def chat_text(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """Appel Claude en mode texte libre (pas JSON)."""
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.2,
            system=_build_system_blocks(system),
            messages=[{"role": "user", "content": user}],
        )
        self._track_usage(response, step="chat_text")
        return response.content[0].text

    # ── Extended Thinking ────────────────────────────────────────────────
    def complete_json_with_thinking(
        self,
        system_prompt: str,
        user_prompt: str,
        thinking_budget: int = 8000,
        validator: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """LLM call with extended thinking for complex multi-step reasoning.

        Used for conflict detection, CCAP analysis, Go/No-Go scoring, and
        questions generation — tasks that benefit from structured reasoning.

        Note: Extended thinking requires temperature=1 (Anthropic constraint).
        Quality is maintained by Pydantic validators.
        """
        result = self._anthropic_json_thinking(system_prompt, user_prompt, thinking_budget)

        if validator:
            try:
                validated = validator.model_validate(result)
                result = validated.model_dump()
            except ValidationError as exc:
                logger.warning("thinking_validation_failed", validator=validator.__name__, error=str(exc))
                try:
                    validated = validator.model_validate(result, strict=False)
                    result = validated.model_dump()
                except ValidationError:
                    raise ValueError(f"Sortie LLM (thinking) non conforme: {exc}")

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    )
    @_llm_breaker
    def _anthropic_json_thinking(self, system: str, user: str, budget: int) -> dict:
        """Anthropic call with extended thinking enabled."""
        import re
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=budget + settings.LLM_MAX_TOKENS,
            temperature=1,  # Required when thinking is enabled
            thinking={
                "type": "enabled",
                "budget_tokens": budget,
            },
            system=_build_system_blocks(system),
            messages=[{"role": "user", "content": user}],
        )

        self._track_usage(response, step="thinking")

        # Extract text block (thinking blocks are separate)
        raw = ""
        for block in response.content:
            if block.type == "text":
                raw = block.text
                break

        if not raw:
            raise ValueError("Extended thinking response contained no text block")

        return self._parse_json_response(raw, response.stop_reason)

    # ── Usage tracking ─────────────────────────────────────────────────
    def _track_usage(self, response, step: str = "unknown"):
        """Track token usage for cost monitoring."""
        usage = response.usage
        entry = {
            "step": step,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "cache_read_tokens": getattr(usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_tokens": getattr(usage, "cache_creation_input_tokens", 0) or 0,
        }
        self._usage_accumulator.append(entry)

    def get_usage_summary(self) -> dict:
        """Return accumulated usage and estimated cost, then reset."""
        if not self._usage_accumulator:
            return {"total_input": 0, "total_output": 0, "total_cached": 0, "estimated_cost_eur": 0.0}

        total_input = sum(e["input_tokens"] for e in self._usage_accumulator)
        total_output = sum(e["output_tokens"] for e in self._usage_accumulator)
        total_cached = sum(e["cache_read_tokens"] for e in self._usage_accumulator)

        # Pricing: Claude Sonnet — $3/MTok input, $15/MTok output, $0.30/MTok cached read
        cost_usd = (total_input * 3 + total_output * 15 + total_cached * 0.3) / 1_000_000
        cost_eur = cost_usd * 0.92  # Approximate EUR conversion

        summary = {
            "total_input": total_input,
            "total_output": total_output,
            "total_cached": total_cached,
            "steps": len(self._usage_accumulator),
            "estimated_cost_eur": round(cost_eur, 4),
            "details": self._usage_accumulator.copy(),
        }
        self._usage_accumulator.clear()
        return summary

    def reset_usage(self):
        """Reset usage accumulator (call at start of each analysis run)."""
        self._usage_accumulator.clear()

    # ── Batch API (Anthropic Message Batches) ─────────────────────────
    def create_batch(
        self,
        requests: list[dict],
    ) -> str:
        """Submit a batch of LLM requests for async processing (-50% cost).

        Each request is: {"custom_id": str, "system": str, "user": str}
        Returns the batch_id for later retrieval.

        Use for non-urgent workloads: BOAMP veille, nightly re-scoring, bulk analysis.
        Results available within 24h.
        """
        batch_requests = []
        for req in requests:
            batch_requests.append({
                "custom_id": req["custom_id"],
                "params": {
                    "model": self.model,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "temperature": settings.LLM_TEMPERATURE,
                    "system": _build_system_blocks(req["system"], cache=False),
                    "messages": [{"role": "user", "content": req["user"]}],
                },
            })

        batch = self._anthropic.messages.batches.create(requests=batch_requests)
        logger.info("batch_created", batch_id=batch.id, count=len(requests))
        return batch.id

    def get_batch_status(self, batch_id: str) -> dict:
        """Check status of a batch. Returns {status, results_url, counts}."""
        batch = self._anthropic.messages.batches.retrieve(batch_id)
        return {
            "id": batch.id,
            "status": batch.processing_status,
            "request_counts": {
                "total": batch.request_counts.processing + batch.request_counts.succeeded + batch.request_counts.errored,
                "succeeded": batch.request_counts.succeeded,
                "errored": batch.request_counts.errored,
                "processing": batch.request_counts.processing,
            },
            "created_at": str(batch.created_at),
            "ended_at": str(batch.ended_at) if batch.ended_at else None,
        }

    def get_batch_results(self, batch_id: str) -> list[dict]:
        """Retrieve results from a completed batch. Returns list of {custom_id, result}."""
        results = []
        for entry in self._anthropic.messages.batches.results(batch_id):
            custom_id = entry.custom_id
            if entry.result.type == "succeeded":
                raw = entry.result.message.content[0].text
                try:
                    parsed = self._parse_json_response(raw, entry.result.message.stop_reason)
                except ValueError:
                    parsed = {"error": "JSON parse failed", "raw": raw[:500]}
                results.append({"custom_id": custom_id, "result": parsed, "status": "success"})
            else:
                results.append({"custom_id": custom_id, "result": None, "status": "error"})
        return results

    # ── Tool Use (legal references verification) ──────────────────────
    def complete_json_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        tool_handler: callable,
        max_tool_calls: int = 3,
        validator: type[BaseModel] | None = None,
    ) -> dict[str, Any]:
        """LLM call with tool use for verifying legal references.

        Claude can call tools during analysis (e.g., check_ccag_article,
        check_legal_threshold). The tool_handler receives the tool call
        and returns the result.

        Args:
            tools: Anthropic tool definitions
            tool_handler: function(tool_name, tool_input) -> str
            max_tool_calls: Maximum number of tool call rounds
        """
        messages = [{"role": "user", "content": user_prompt}]

        for _ in range(max_tool_calls + 1):
            response = self._anthropic.messages.create(
                model=self.model,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                system=_build_system_blocks(system_prompt),
                messages=messages,
                tools=tools,
            )
            self._track_usage(response, step="tool_use")

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        try:
                            result = tool_handler(block.name, block.input)
                        except Exception as e:
                            result = f"Erreur outil: {e}"
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

                # Add assistant response and tool results to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            else:
                # Final response — extract JSON
                raw = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        raw = block.text
                        break

                result = self._parse_json_response(raw, response.stop_reason)

                if validator:
                    try:
                        validated = validator.model_validate(result)
                        result = validated.model_dump()
                    except ValidationError as exc:
                        try:
                            validated = validator.model_validate(result, strict=False)
                            result = validated.model_dump()
                        except ValidationError:
                            raise ValueError(f"Sortie LLM (tools) non conforme: {exc}")

                return result

        # If we exhausted tool calls, try to extract from last response
        raise ValueError("Max tool call rounds exceeded without final response")

    def get_model_name(self) -> str:
        return f"anthropic:{self.model}"


llm_service = LLMService()
