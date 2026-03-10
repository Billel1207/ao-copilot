"""Abstraction LLM — Anthropic Claude (principal) avec fallback OpenAI optionnel."""
import json
import structlog
from typing import Any

import anthropic as anthropic_sdk
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = structlog.get_logger(__name__)

# Exceptions Anthropic qui méritent un retry (transitoires)
_RETRYABLE_EXCEPTIONS = (
    anthropic_sdk.RateLimitError,
    anthropic_sdk.InternalServerError,
    anthropic_sdk.APIConnectionError,
    anthropic_sdk.APITimeoutError,
)


class LLMService:
    def __init__(self):
        self._anthropic = anthropic_sdk.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL
        self.provider = "anthropic"

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
    def _anthropic_json(self, system: str, user: str) -> dict:
        import re
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=settings.LLM_MAX_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        raw = response.content[0].text
        stop_reason = response.stop_reason

        # Détecter la troncature (max_tokens atteint)
        if stop_reason == "max_tokens":
            logger.warning(
                "Réponse LLM tronquée (max_tokens=%d atteint). "
                "Tentative de réparation JSON...",
                settings.LLM_MAX_TOKENS,
            )
            raw = self._repair_truncated_json(raw)

        # Extraire le JSON de la réponse (peut être entouré de markdown)
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

        # Tentative 3 : réparation JSON tronqué (fermer brackets/braces ouverts)
        repaired = self._repair_truncated_json(raw)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

        # Échec définitif : lever une erreur claire
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
    def chat_text(self, system: str, user: str, max_tokens: int = 1024) -> str:
        """Appel Claude en mode texte libre (pas JSON)."""
        response = self._anthropic.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.2,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    def get_model_name(self) -> str:
        return f"anthropic:{self.model}"


llm_service = LLMService()
