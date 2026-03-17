"""Analyseur de sous-traitance — cross-référence RC × profil entreprise × CCTP.

Compare les exigences du RC en matière de sous-traitance avec les capacités
internes de l'entreprise et les exigences techniques du CCTP pour identifier :
- Les lots qui nécessitent de la sous-traitance
- Les conflits (RC interdit la sous-traitance mais compétence manquante)
- Le risque global de sous-traitance
"""
import json
import structlog
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.analysis import ExtractionResult
from app.models.company_profile import CompanyProfile
from app.services.llm import llm_service
from app.services.retriever import retrieve_relevant_chunks, format_context

logger = structlog.get_logger(__name__)


SUBCONTRACTING_PROMPT = """Tu es un expert en marchés publics BTP (France).
Analyse les informations suivantes pour évaluer la stratégie de sous-traitance optimale.

## Contexte entreprise
{company_context}

## Extraits RC (sous-traitance)
{rc_context}

## Extraits CCTP (exigences techniques)
{cctp_context}

## Consigne
Produis un JSON avec cette structure exacte :
{{
  "sous_traitance_autorisee": true/false,
  "restrictions_rc": "description des restrictions du RC sur la sous-traitance",
  "lots_analysis": [
    {{
      "lot": "nom ou numéro du lot",
      "competence_requise": "description de la compétence technique nécessaire",
      "competence_interne": true/false,
      "sous_traitance_recommandee": true/false,
      "justification": "pourquoi sous-traiter ou non",
      "risque": "faible|modéré|élevé"
    }}
  ],
  "conflits": [
    {{
      "type": "description du conflit",
      "source_a": "RC / CCTP / Profil",
      "source_b": "RC / CCTP / Profil",
      "description": "explication détaillée",
      "severity": "high|medium|low"
    }}
  ],
  "paiement_direct_applicable": true/false,
  "seuil_paiement_direct_eur": 600,
  "recommandations": ["conseil 1", "conseil 2"],
  "score_risque": 0-100,
  "resume": "synthèse en 3-4 phrases",
  "confidence_overall": 0.0-1.0
}}

Règles :
- Si le RC interdit la sous-traitance mais que l'entreprise manque de compétences → conflit severity=high
- Le paiement direct est obligatoire au-delà de 600€ TTC (art. 133 CMP 2019)
- Score risque élevé si > 50% des lots nécessitent sous-traitance
- Confidence faible si peu d'informations sur la sous-traitance dans le RC
"""


def analyze_subcontracting(
    project_id: str,
    db: Session,
) -> dict:
    """Analyse la stratégie de sous-traitance optimale pour un projet."""

    # Récupérer les résultats d'analyse existants
    from app.models.project import AoProject
    project = db.query(AoProject).filter_by(id=project_id).first()
    if not project:
        return {"error": "Projet introuvable"}

    # Récupérer le profil entreprise
    profile = db.query(CompanyProfile).filter_by(org_id=project.org_id).first()
    company_context = "Aucun profil entreprise renseigné."
    if profile:
        specialties = profile.specialties or []
        certifications = profile.certifications or []
        company_context = (
            f"Spécialités : {', '.join(specialties) if specialties else 'Non renseignées'}\n"
            f"Certifications : {', '.join(certifications) if certifications else 'Aucune'}\n"
            f"Effectif : {profile.employee_count or 'N/A'}\n"
            f"CA annuel : {profile.revenue_eur or 'N/A'} EUR"
        )
        if hasattr(profile, 'partenaires_specialites') and profile.partenaires_specialites:
            company_context += f"\nPartenaires sous-traitants : {', '.join(profile.partenaires_specialites)}"

    # Récupérer les chunks pertinents
    rc_chunks = retrieve_relevant_chunks(
        db, project_id, "sous-traitance groupement cotraitance", top_k=5
    )
    cctp_chunks = retrieve_relevant_chunks(
        db, project_id, "lots compétences techniques spécialités travaux", top_k=5
    )

    rc_context = format_context(rc_chunks) if rc_chunks else "Aucune information RC disponible."
    cctp_context = format_context(cctp_chunks) if cctp_chunks else "Aucune information CCTP disponible."

    prompt = SUBCONTRACTING_PROMPT.format(
        company_context=company_context,
        rc_context=rc_context[:4000],
        cctp_context=cctp_context[:4000],
    )

    result = llm_service.complete_json(
        system_prompt=prompt,
        user_prompt="Analyse la stratégie de sous-traitance optimale pour ce marché.",
    )

    if not result:
        return {
            "sous_traitance_autorisee": None,
            "lots_analysis": [],
            "conflits": [],
            "recommandations": [],
            "score_risque": 0,
            "resume": "Analyse impossible — données insuffisantes.",
            "confidence_overall": 0.0,
        }

    # Normaliser le score
    score = result.get("score_risque", 0)
    result["score_risque"] = max(0, min(100, int(score) if isinstance(score, (int, float)) else 0))

    # Normaliser la confidence
    conf = result.get("confidence_overall", 0.5)
    result["confidence_overall"] = max(0.0, min(1.0, float(conf) if isinstance(conf, (int, float)) else 0.5))

    return result
