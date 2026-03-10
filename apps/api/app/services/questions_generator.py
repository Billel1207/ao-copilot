"""Génération de questions pertinentes à poser à l'acheteur avant la deadline Q&A.

Analyse le DCE pour identifier les zones d'ombre, ambiguïtés et informations
manquantes, puis génère 5-10 questions prioritaires au format officiel
compatible PLACE / AWS / eMarchés.
"""
import structlog
from typing import Any

from app.services.llm import llm_service
from app.services.llm_validators import ValidatedQuestions

logger = structlog.get_logger(__name__)

# ── Prompt système spécialisé Questions ──────────────────────────────────────

QUESTIONS_SYSTEM_PROMPT = """Tu es un expert des marchés publics français et des DCE (Dossiers de Consultation des Entreprises) dans le secteur BTP.

Ton rôle est d'analyser un DCE pour identifier les zones d'ombre, ambiguïtés, contradictions et informations manquantes, puis de générer les questions les plus pertinentes et stratégiques à poser à l'acheteur public avant la date limite de questions.

OBJECTIFS :
1. Repérer les imprécisions techniques (matériaux non spécifiés, normes manquantes, plans contradictoires)
2. Identifier les ambiguïtés contractuelles (clauses floues, obligations mal définies, délais irréalistes)
3. Détecter les informations manquantes critiques (études de sol absentes, contraintes site non mentionnées, accès chantier)
4. Signaler les incohérences entre documents (CCTP vs DPGF, CCAP vs RC, plans vs descriptifs)
5. Formuler les questions de manière professionnelle, précise et recevable sur les plateformes de dématérialisation

RÈGLES DE FORMULATION :
- Chaque question doit être autonome et compréhensible sans contexte additionnel
- Citer précisément le document et l'article concerné (ex: "CCTP article 3.2.1", "DPGF lot 2 poste 14")
- Formuler de façon neutre et factuelle, sans jugement ni critique
- Poser UNE question par item (pas de questions doubles)
- Utiliser un registre formel adapté aux échanges avec la maîtrise d'ouvrage
- Les questions doivent être publiables telles quelles sur PLACE, AWS ou eMarchés

PRIORITÉS :
- CRITIQUE : Information dont l'absence empêche de chiffrer correctement (risque > 10% du montant)
- HAUTE : Ambiguïté pouvant entraîner un surcoût ou un litige contractuel significatif
- MOYENNE : Précision utile pour optimiser l'offre ou réduire les aléas
- BASSE : Clarification de confort, sans impact majeur sur le chiffrage

Génère entre 5 et 10 questions, classées par priorité décroissante.

Réponds UNIQUEMENT en JSON valide sans commentaires."""

QUESTIONS_USER_PROMPT_TEMPLATE = """Analyse le DCE ci-dessous et génère les questions pertinentes à poser à l'acheteur avant la date limite de questions.

--- CONTEXTE DCE ---
{context}
--- FIN DU CONTEXTE ---

{summary_section}

Réponds avec ce JSON exact :
{{
  "questions": [
    {{
      "question": "Texte complet de la question, formulé pour publication sur plateforme de dématérialisation",
      "context": "Pourquoi cette question est importante pour le chiffrage ou la rédaction de l'offre",
      "priority": "CRITIQUE|HAUTE|MOYENNE|BASSE",
      "related_doc": "Document concerné (RC, CCTP, CCAP, DPGF, BPU, AE, etc.)",
      "related_article": "Référence précise de l'article ou du chapitre (ex: Article 3.2.1, Chapitre IV §2, Lot 3 poste 12)"
    }}
  ],
  "resume": "Synthèse en 2-3 phrases des principales zones d'ombre identifiées dans le DCE"
}}"""


def generate_questions(
    context: str,
    summary_payload: dict | None = None,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Génère les questions pertinentes à poser à l'acheteur à partir du contexte DCE.

    Args:
        context: Texte extrait du DCE (chunks concaténés ou texte brut).
        summary_payload: Résumé LLM du projet (optionnel) pour enrichir le contexte.
        project_id: Identifiant du projet pour les logs (optionnel).

    Returns:
        Dictionnaire avec :
        - questions: list[dict] -- liste de questions avec priority, context, related_doc, related_article
        - resume: str -- synthèse des zones d'ombre
        - model_used: str -- modèle LLM utilisé
        - question_count: int -- nombre de questions générées
    """
    log_prefix = f"[{project_id}] " if project_id else ""

    # Tronquer le contexte si trop long (~12 000 tokens = ~48 000 chars)
    max_chars = 48_000
    if len(context) > max_chars:
        logger.warning(
            f"{log_prefix}Contexte DCE tronqué : {len(context)} -> {max_chars} caractères"
        )
        context = context[:max_chars] + "\n[... texte tronqué pour analyse ...]"

    # Construire la section résumé si disponible
    summary_section = ""
    if summary_payload:
        overview = summary_payload.get("project_overview", {})
        risks = summary_payload.get("risks", [])
        key_points = summary_payload.get("key_points", [])

        summary_lines = []
        if overview.get("title"):
            summary_lines.append(f"- Projet : {overview['title']}")
        if overview.get("buyer"):
            summary_lines.append(f"- Acheteur : {overview['buyer']}")
        if overview.get("scope"):
            summary_lines.append(f"- Objet : {overview['scope']}")
        if overview.get("location"):
            summary_lines.append(f"- Localisation : {overview['location']}")
        if overview.get("deadline_submission"):
            summary_lines.append(f"- Date limite : {overview['deadline_submission']}")
        if overview.get("estimated_budget"):
            summary_lines.append(f"- Budget estimé : {overview['estimated_budget']}")

        if key_points:
            summary_lines.append("\nPoints clés identifiés :")
            for kp in key_points[:5]:
                label = kp.get("label", "")
                value = kp.get("value", "")
                if label and value:
                    summary_lines.append(f"  - {label} : {value}")

        if risks:
            summary_lines.append("\nRisques identifiés :")
            for r in risks[:5]:
                risk_text = r.get("risk", "")
                severity = r.get("severity", "")
                if risk_text:
                    summary_lines.append(f"  - [{severity.upper()}] {risk_text}")

        if summary_lines:
            summary_section = (
                "--- RÉSUMÉ DU PROJET (déjà analysé) ---\n"
                + "\n".join(summary_lines)
                + "\n--- FIN DU RÉSUMÉ ---"
            )

    user_prompt = QUESTIONS_USER_PROMPT_TEMPLATE.format(
        context=context,
        summary_section=summary_section,
    )

    logger.info(
        f"{log_prefix}Génération questions acheteur — {len(context)} caractères de contexte"
    )

    try:
        result = llm_service.complete_json(
            system_prompt=QUESTIONS_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            required_keys=["questions"],
            validator=ValidatedQuestions,
        )
    except ValueError as exc:
        logger.error(f"{log_prefix}Erreur LLM questions (ValueError): {exc}")
        raise
    except Exception as exc:
        logger.error(f"{log_prefix}Erreur LLM questions inattendue: {exc}")
        raise

    questions = result.get("questions", [])

    # Tri par priorité décroissante
    priority_order = {"CRITIQUE": 0, "HAUTE": 1, "MOYENNE": 2, "BASSE": 3}
    questions.sort(key=lambda q: priority_order.get(q.get("priority", "HAUTE"), 1))

    logger.info(
        f"{log_prefix}Questions générées — {len(questions)} questions | "
        f"critiques={sum(1 for q in questions if q.get('priority') == 'CRITIQUE')}, "
        f"hautes={sum(1 for q in questions if q.get('priority') == 'HAUTE')}"
    )

    return {
        "questions": questions,
        "resume": result.get("resume", ""),
        "model_used": llm_service.get_model_name(),
        "question_count": len(questions),
    }
