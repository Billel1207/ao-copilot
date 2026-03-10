"""Validation Pydantic stricte de TOUTES les sorties LLM.

Chaque analyse du pipeline passe par un modèle Pydantic v2 strict
qui rejette les hallucinations structurelles (dates invalides, enums hors-scope,
scores hors-range, citations vides, etc.).
"""
from __future__ import annotations

import structlog
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

logger = structlog.get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

class LLMCitation(BaseModel):
    doc: str = ""
    page: int = 0
    quote: str = ""

class LLMProjectOverview(BaseModel):
    title: str = ""
    buyer: str = ""
    scope: str = ""
    location: str = ""
    deadline_submission: str = ""
    site_visit_required: bool = False
    market_type: str | None = None
    estimated_budget: str | None = None

    @field_validator("deadline_submission")
    @classmethod
    def validate_deadline(cls, v: str) -> str:
        if not v or v.strip() == "":
            return ""
        # Tenter le parsing ISO — sinon vider (ne pas inventer)
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            logger.warning(f"Date submission invalide rejetee: {v!r}")
            return ""
        return v

class LLMKeyPoint(BaseModel):
    label: str
    value: str
    citations: list[LLMCitation] = []

class LLMRisk(BaseModel):
    risk: str
    severity: str = "medium"
    why: str = ""
    citations: list[LLMCitation] = []

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        if v.lower() not in allowed:
            return "medium"
        return v.lower()

class LLMNextAction(BaseModel):
    action: str
    owner_role: str = ""
    priority: str = "P1"

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"P0", "P1", "P2"}
        if v.upper() not in allowed:
            return "P1"
        return v.upper()

class ValidatedSummary(BaseModel):
    """Modele strict de validation du résumé LLM."""
    project_overview: LLMProjectOverview
    key_points: list[LLMKeyPoint] = []
    risks: list[LLMRisk] = []
    actions_next_48h: list[LLMNextAction] = []
    confidence_overall: float | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════════

class LLMChecklistItem(BaseModel):
    category: str = "Administratif"
    requirement: str
    criticality: str = "Important"
    status: str = "MANQUANT"
    what_to_provide: str = ""
    citations: list[LLMCitation] = []
    confidence: float = 0.5

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {"Administratif", "Technique", "Financier", "Planning"}
        if v not in allowed:
            # Best-effort mapping
            v_lower = v.lower()
            for a in allowed:
                if a.lower() in v_lower or v_lower in a.lower():
                    return a
            return "Administratif"
        return v

    @field_validator("criticality")
    @classmethod
    def validate_criticality(cls, v: str) -> str:
        mapping = {
            "eliminatoire": "Éliminatoire",
            "éliminatoire": "Éliminatoire",
            "important": "Important",
            "info": "Info",
            "information": "Info",
        }
        normalized = mapping.get(v.lower().strip(), None)
        if normalized:
            return normalized
        if v in ("Éliminatoire", "Important", "Info"):
            return v
        return "Important"

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        mapping = {
            "ok": "OK",
            "manquant": "MANQUANT",
            "a clarifier": "À CLARIFIER",
            "à clarifier": "À CLARIFIER",
        }
        normalized = mapping.get(v.lower().strip(), None)
        if normalized:
            return normalized
        if v in ("OK", "MANQUANT", "À CLARIFIER"):
            return v
        return "MANQUANT"

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))

class ValidatedChecklist(BaseModel):
    """Modele strict de validation de la checklist LLM."""
    checklist: list[LLMChecklistItem] = []


# ═══════════════════════════════════════════════════════════════════════════════
# CRITERIA
# ═══════════════════════════════════════════════════════════════════════════════

class LLMEligibilityCondition(BaseModel):
    condition: str
    type: str = "hard"
    citations: list[LLMCitation] = []

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v.lower() not in ("hard", "soft"):
            return "hard"
        return v.lower()

class LLMScoringCriterion(BaseModel):
    criterion: str
    weight_percent: float | None = None
    notes: str | None = None
    citations: list[LLMCitation] = []

    @field_validator("weight_percent")
    @classmethod
    def validate_weight(cls, v: float | None) -> float | None:
        if v is not None:
            if v < 0 or v > 100:
                return None
        return v

class LLMEvaluation(BaseModel):
    eligibility_conditions: list[LLMEligibilityCondition] = []
    scoring_criteria: list[LLMScoringCriterion] = []
    total_weight_check: float | None = None
    confidence: float | None = None

class ValidatedCriteria(BaseModel):
    """Modele strict de validation des critères LLM."""
    evaluation: LLMEvaluation

    @model_validator(mode="after")
    def check_weights_sum(self) -> "ValidatedCriteria":
        """Vérifie que les pondérations totalisent ~100% si fournies."""
        weights = [
            c.weight_percent
            for c in self.evaluation.scoring_criteria
            if c.weight_percent is not None
        ]
        if weights:
            total = sum(weights)
            if abs(total - 100) > 10:
                logger.warning(
                    f"Pondérations critères = {total:.1f}% (attendu ~100%). "
                    f"Les poids peuvent être approximatifs."
                )
                self.evaluation.total_weight_check = total
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# GO/NO-GO
# ═══════════════════════════════════════════════════════════════════════════════

class LLMGoNoGoBreakdown(BaseModel):
    technical_fit: int = 50
    financial_capacity: int = 50
    timeline_feasibility: int = 50
    competitive_position: int = 50

    @field_validator("technical_fit", "financial_capacity", "timeline_feasibility", "competitive_position")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, int(v)))

class ValidatedGoNoGo(BaseModel):
    """Modele strict de validation du Go/No-Go LLM."""
    score: int = 50
    recommendation: str = "ATTENTION"
    strengths: list[str] = []
    risks: list[str] = []
    summary: str = ""
    breakdown: LLMGoNoGoBreakdown = LLMGoNoGoBreakdown()

    @field_validator("score")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, int(v)))

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        allowed = {"GO", "ATTENTION", "NO-GO"}
        v_upper = v.upper().strip().replace("_", "-")
        if v_upper in allowed:
            return v_upper
        # Mapping best-effort
        if "go" in v.lower() and "no" not in v.lower():
            return "GO"
        if "no" in v.lower():
            return "NO-GO"
        return "ATTENTION"

    @model_validator(mode="after")
    def check_score_recommendation_coherence(self) -> "ValidatedGoNoGo":
        """Vérifie la cohérence score↔recommendation."""
        s = self.score
        r = self.recommendation
        if s >= 70 and r == "NO-GO":
            logger.warning(f"Incohérence Go/No-Go: score={s} mais recommendation={r}")
            self.recommendation = "GO"
        elif s < 40 and r == "GO":
            logger.warning(f"Incohérence Go/No-Go: score={s} mais recommendation={r}")
            self.recommendation = "NO-GO"
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# TIMELINE / DEADLINES
# ═══════════════════════════════════════════════════════════════════════════════

class LLMKeyDate(BaseModel):
    label: str = ""
    date: str | None = None
    mandatory: bool = False

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str | None) -> str | None:
        if not v or v.strip() == "":
            return None
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except (ValueError, TypeError):
            logger.warning(f"Date clé invalide rejetée: {v!r}")
            return None

class ValidatedTimeline(BaseModel):
    """Modele strict de validation du timeline LLM."""
    submission_deadline: str | None = None
    execution_start: str | None = None
    execution_duration_months: int | None = None
    site_visit_date: str | None = None
    questions_deadline: str | None = None
    key_dates: list[LLMKeyDate] = []

    @field_validator("submission_deadline", "execution_start", "site_visit_date", "questions_deadline")
    @classmethod
    def validate_iso_date(cls, v: str | None) -> str | None:
        if not v or v.strip() == "":
            return None
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
            return v
        except (ValueError, TypeError):
            logger.warning(f"Date ISO invalide rejetée: {v!r}")
            return None

    @field_validator("execution_duration_months")
    @classmethod
    def validate_duration(cls, v: int | None) -> int | None:
        if v is not None:
            if v < 0 or v > 240:  # Max 20 ans
                return None
        return v


# ═══════════════════════════════════════════════════════════════════════════════
# RC (Règlement de Consultation) — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMRcCondition(BaseModel):
    condition: str
    type: str = "hard"  # hard = éliminatoire, soft = recommandé
    details: str = ""
    citations: list[LLMCitation] = []

class LLMRcGroupement(BaseModel):
    groupement_autorise: bool = True
    forme_imposee: str | None = None
    mandataire_solidaire: bool = False
    details: str = ""

class LLMRcSousTraitance(BaseModel):
    sous_traitance_autorisee: bool = True
    restrictions: list[str] = []
    details: str = ""

class ValidatedRcAnalysis(BaseModel):
    """Analyse complète du Règlement de Consultation."""
    who_can_apply: list[LLMRcCondition] = []
    groupement: LLMRcGroupement = LLMRcGroupement()
    sous_traitance: LLMRcSousTraitance = LLMRcSousTraitance()
    variantes_autorisees: bool = False
    variantes_details: str = ""
    prestations_supplementaires: bool = False
    prestations_details: str = ""
    visite_site_obligatoire: bool = False
    visite_details: str = ""
    langue_offre: str = "français"
    devise_offre: str = "EUR"
    duree_validite_offres_jours: int | None = None
    nombre_lots: int | None = None
    lots_details: list[dict] = []
    procedure_type: str = ""  # ouvert, restreint, dialogue compétitif, etc.
    resume: str = ""
    confidence_overall: float = 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# AE (Acte d'Engagement) — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMAeClause(BaseModel):
    clause_type: str
    description: str
    risk_level: str = "MOYEN"
    citation: str = ""
    conseil: str = ""

    @field_validator("risk_level")
    @classmethod
    def validate_risk(cls, v: str) -> str:
        if v.upper() not in ("CRITIQUE", "HAUT", "MOYEN", "BAS"):
            return "MOYEN"
        return v.upper()

class LLMCcagDerogation(BaseModel):
    """Dérogation au CCAG-Travaux 2021 détectée dans un document du DCE."""
    article_ccag: str = ""
    valeur_ccag: str = ""
    valeur_ccap: str = ""  # Peut aussi contenir la valeur AE
    impact: str = "NEUTRE"
    description: str = ""

    @field_validator("impact")
    @classmethod
    def validate_impact(cls, v: str) -> str:
        allowed = {"DEFAVORABLE", "FAVORABLE", "NEUTRE"}
        v_upper = v.upper().strip()
        if v_upper in allowed:
            return v_upper
        # Mapping fuzzy
        if "defav" in v.lower() or "négatif" in v.lower():
            return "DEFAVORABLE"
        if "favor" in v.lower() or "positif" in v.lower():
            return "FAVORABLE"
        return "NEUTRE"

class ValidatedAeAnalysis(BaseModel):
    """Analyse complète de l'Acte d'Engagement."""
    prix_forme: str = ""  # forfait, unitaire, mixte
    prix_revision: bool = False
    prix_revision_details: str = ""
    montant_total_ht: str | None = None
    duree_marche: str = ""
    reconduction: bool = False
    reconduction_details: str = ""
    penalites_retard: str = ""
    retenue_garantie_pct: float | None = None
    avance_pct: float | None = None
    delai_paiement_jours: int | None = None
    clauses_risquees: list[LLMAeClause] = []
    ccag_derogations: list[LLMCcagDerogation] = []
    score_risque_global: int = 0
    resume: str = ""
    confidence_overall: float = 0.5

    @field_validator("score_risque_global")
    @classmethod
    def clamp(cls, v: int) -> int:
        return max(0, min(100, int(v)))


# ═══════════════════════════════════════════════════════════════════════════════
# DC1/DC2 CHECKER — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMDcRequirement(BaseModel):
    document: str  # "DC1", "DC2", "Kbis", "URSSAF", etc.
    obligatoire: bool = True
    date_validite: str | None = None  # Date d'expiration si connue
    statut: str = "À_FOURNIR"  # OK, À_FOURNIR, EXPIRE, NON_REQUIS
    details: str = ""
    citations: list[LLMCitation] = []

class ValidatedDcCheck(BaseModel):
    """Vérification DC1/DC2 + attestations requises."""
    documents_requis: list[LLMDcRequirement] = []
    formulaires_obligatoires: list[str] = []  # ex: ["DC1 v2024", "DC2 v2024"]
    attestations_fiscales: bool = False
    attestation_urssaf: bool = False
    attestation_assurance_rc: bool = False
    attestation_assurance_decennale: bool = False
    kbis_requis: bool = False
    certifications_requises: list[str] = []
    alertes: list[str] = []  # Alertes importantes
    resume: str = ""
    confidence_overall: float = 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# CONFLITS INTRA-DCE — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMConflict(BaseModel):
    conflict_type: str  # "delai", "montant", "exigence", "clause_illegale", "reference", "deviation_ccag", "cctp_dpgf"
    severity: str = "MOYEN"
    doc_a: str = ""
    doc_b: str = ""
    description: str
    citation_a: str = ""
    citation_b: str = ""
    recommendation: str = ""

    @field_validator("conflict_type")
    @classmethod
    def validate_conflict_type(cls, v: str) -> str:
        allowed = {"delai", "montant", "exigence", "clause_illegale", "reference", "deviation_ccag", "cctp_dpgf"}
        v_lower = v.lower().strip().replace("é", "e").replace(" ", "_")
        if v_lower in allowed:
            return v_lower
        # Mapping fuzzy
        mapping = {
            "délai": "delai", "delais": "delai", "deadline": "delai",
            "montants": "montant", "prix": "montant", "financial": "montant",
            "exigences": "exigence", "requirement": "exigence",
            "clause_illegale": "clause_illegale", "illegale": "clause_illegale",
            "illegal": "clause_illegale", "clause illegale": "clause_illegale",
            "references": "reference", "ref": "reference",
            "ccag": "deviation_ccag", "derog": "deviation_ccag",
            "derogation": "deviation_ccag", "deviation": "deviation_ccag",
            "derogation_ccag": "deviation_ccag",
            "cctp": "cctp_dpgf", "dpgf": "cctp_dpgf",
            "materiau": "cctp_dpgf", "quantite": "cctp_dpgf",
        }
        for key, val in mapping.items():
            if key in v_lower:
                return val
        return "exigence"  # Default fallback

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v.upper() not in ("CRITIQUE", "HAUT", "MOYEN", "BAS"):
            return "MOYEN"
        return v.upper()

class ValidatedConflicts(BaseModel):
    """Détection de conflits entre pièces du DCE."""
    conflicts: list[LLMConflict] = []
    nb_critiques: int = 0
    nb_total: int = 0
    resume: str = ""
    confidence_overall: float = 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# QUESTIONS AUX ACHETEURS — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMQuestion(BaseModel):
    question: str
    context: str = ""  # Pourquoi cette question est importante
    priority: str = "HAUTE"
    related_doc: str = ""
    related_article: str = ""

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        if v.upper() not in ("CRITIQUE", "HAUTE", "MOYENNE", "BASSE"):
            return "HAUTE"
        return v.upper()

class ValidatedQuestions(BaseModel):
    """Questions pertinentes à poser à l'acheteur."""
    questions: list[LLMQuestion] = []
    resume: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING SIMULATOR — NOUVEAU
# ═══════════════════════════════════════════════════════════════════════════════

class LLMScoringDimension(BaseModel):
    criterion: str
    weight_pct: float = 0
    estimated_score: float = 0  # 0-20 ou 0-100 selon barème
    max_score: float = 20
    justification: str = ""
    tips_to_improve: list[str] = []

class ValidatedScoringSimulation(BaseModel):
    """Simulation de scoring acheteur."""
    dimensions: list[LLMScoringDimension] = []
    note_technique_estimee: float = 0
    note_financiere_estimee: float = 0
    note_globale_estimee: float = 0
    classement_probable: str = ""  # "Top 3", "Milieu de peloton", "Risqué"
    axes_amelioration: list[str] = []
    resume: str = ""


# ═══════════════════════════════════════════════════════════════════════════════
# CCAP (Cahier des Clauses Administratives Particulières)
# ═══════════════════════════════════════════════════════════════════════════════

class LLMCcapClause(BaseModel):
    clause: str = ""
    risk_type: str = ""
    severity: str = "MOYEN"
    article_ccag: str = ""
    explication: str = ""
    recommendation: str = ""
    citation: str = ""

    @field_validator("severity", mode="before")
    @classmethod
    def normalize_severity(cls, v):
        mapping = {"critique": "CRITIQUE", "haut": "HAUT", "moyen": "MOYEN", "faible": "FAIBLE"}
        return mapping.get(str(v).lower().strip(), "MOYEN")

class ValidatedCcapAnalysis(BaseModel):
    clauses_risquees: list[LLMCcapClause] = []
    ccag_derogations: list[LLMCcagDerogation] = []
    score_risque_global: int = 50
    nb_clauses_critiques: int = 0
    resume: str = ""
    confidence_overall: float = 0.5

    @field_validator("score_risque_global", mode="before")
    @classmethod
    def clamp_score(cls, v):
        return max(0, min(100, int(v or 50)))


# ═══════════════════════════════════════════════════════════════════════════════
# CCTP (Cahier des Clauses Techniques Particulières)
# ═══════════════════════════════════════════════════════════════════════════════

_CCTP_CATEGORIES = {
    "materiaux", "normes", "execution", "essais",
    "garanties", "risques", "documents", "restrictives",
}

_CCTP_RISK_LEVELS = {"CRITIQUE", "HAUT", "MOYEN", "BAS", "INFO"}

_CCTP_RISK_TYPES = {
    "geotechnique", "amiante", "plomb", "pollution",
    "reseaux", "demolition", "environnement", "autre",
}

_CCTP_DOC_TYPES = {
    "DOE", "DIUO", "notes_calcul", "plans_exe",
    "PAQ", "fiches_techniques", "PV_essais", "autre",
}

_CCTP_RESPONSABLES = {"titulaire", "moa", "moe", "labo_externe"}


class LLMCctpExigence(BaseModel):
    category: str = "autre"
    description: str = ""
    norme_ref: str | None = None
    risk_level: str = "INFO"
    citation: str = ""
    conseil: str = ""

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower in _CCTP_CATEGORIES:
            return v_lower
        # Fuzzy mapping
        mapping = {
            "matériau": "materiaux", "materiau": "materiaux", "fourniture": "materiaux",
            "norme": "normes", "dtu": "normes", "eurocode": "normes", "re2020": "normes",
            "exécution": "execution", "chantier": "execution", "phasage": "execution",
            "essai": "essais", "contrôle": "essais", "controle": "essais", "test": "essais",
            "garantie": "garanties", "décennale": "garanties", "gpa": "garanties",
            "risque": "risques", "danger": "risques", "amiante": "risques",
            "document": "documents", "doe": "documents", "diuo": "documents",
            "restrictif": "restrictives", "restriction": "restrictives", "marque": "restrictives",
        }
        for key, val in mapping.items():
            if key in v_lower:
                return val
        return "autre"

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper in _CCTP_RISK_LEVELS:
            return v_upper
        mapping = {"CRITICAL": "CRITIQUE", "HIGH": "HAUT", "MEDIUM": "MOYEN",
                    "LOW": "BAS", "INFORMATION": "INFO"}
        return mapping.get(v_upper, "INFO")


class LLMCctpNorme(BaseModel):
    code: str = ""
    titre: str = ""
    applicabilite: str = ""


class LLMCctpMateriau(BaseModel):
    designation: str = ""
    marque_imposee: bool = False
    anticoncurrentiel: bool = False
    alternative: str | None = None


class LLMCctpEssai(BaseModel):
    type: str = ""
    frequence: str = ""
    responsable: str = "titulaire"

    @field_validator("responsable")
    @classmethod
    def validate_responsable(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower in _CCTP_RESPONSABLES:
            return v_lower
        mapping = {"maître d'ouvrage": "moa", "maitre ouvrage": "moa",
                    "maître d'œuvre": "moe", "maitre oeuvre": "moe",
                    "laboratoire": "labo_externe", "externe": "labo_externe",
                    "entreprise": "titulaire"}
        for key, val in mapping.items():
            if key in v_lower:
                return val
        return "titulaire"


class LLMCctpDocument(BaseModel):
    type: str = "autre"
    obligatoire: bool = True
    delai: str = ""


class LLMCctpRisqueTechnique(BaseModel):
    type: str = "autre"
    severity: str = "MOYEN"
    description: str = ""
    mitigation: str = ""

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower in _CCTP_RISK_TYPES:
            return v_lower
        mapping = {
            "géotechnique": "geotechnique", "sol": "geotechnique", "nappe": "geotechnique",
            "amiante": "amiante", "désamiantage": "amiante",
            "plomb": "plomb", "saturnisme": "plomb",
            "pollution": "pollution", "dépollution": "pollution", "sol pollué": "pollution",
            "réseau": "reseaux", "dict": "reseaux", "canalisation": "reseaux",
            "démolition": "demolition", "déconstruction": "demolition",
            "environnement": "environnement", "abf": "environnement", "faune": "environnement",
        }
        for key, val in mapping.items():
            if key in v_lower:
                return val
        return "autre"

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper in _CCTP_RISK_LEVELS:
            return v_upper
        return "MOYEN"


class LLMCctpContradiction(BaseModel):
    """Contradiction interne détectée au sein du CCTP."""
    article_a: str = ""
    article_b: str = ""
    description: str = ""
    severity: str = "medium"

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        v_lower = v.lower().strip()
        if v_lower in allowed:
            return v_lower
        mapping = {"haut": "high", "haute": "high", "critique": "high",
                   "moyen": "medium", "moyenne": "medium",
                   "bas": "low", "basse": "low", "faible": "low"}
        return mapping.get(v_lower, "medium")


class ValidatedCctpAnalysis(BaseModel):
    exigences_techniques: list[LLMCctpExigence] = []
    normes_dtu_applicables: list[LLMCctpNorme] = []
    materiaux_imposes: list[LLMCctpMateriau] = []
    essais_controles: list[LLMCctpEssai] = []
    documents_execution: list[LLMCctpDocument] = []
    risques_techniques: list[LLMCctpRisqueTechnique] = []
    contradictions_techniques: list[LLMCctpContradiction] = []
    score_complexite_technique: int = 50
    resume: str = ""
    confidence_overall: float = 0.5

    @field_validator("score_complexite_technique")
    @classmethod
    def clamp_score(cls, v: int) -> int:
        return max(0, min(100, int(v)))

    @field_validator("confidence_overall")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def validate_llm_output(payload: dict, model_class: type[BaseModel]) -> dict:
    """Valide un payload LLM avec un modèle Pydantic strict.

    Retourne le dict validé (avec valeurs corrigées/normalisées).
    Lève ValidationError si la structure est fondamentalement invalide.
    """
    validated = model_class.model_validate(payload)
    return validated.model_dump()


def verify_citations_exist(
    items: list[dict],
    chunks: list[dict],
    citation_key: str = "citations",
) -> tuple[list[dict], int]:
    """Vérifie que les citations LLM existent dans les chunks RAG.

    Retourne (items_with_verification, nb_verified).
    Chaque citation reçoit un champ 'verified': bool.
    """
    # Construire un index de tout le contenu des chunks
    all_content = " ".join(c.get("content", "") for c in chunks).lower()

    total_verified = 0
    for item in items:
        for citation in item.get(citation_key, []):
            quote = citation.get("quote", "").lower().strip()
            if quote and len(quote) > 10:
                # Vérification par sous-chaîne (tolérance: 60% des mots présents)
                words = quote.split()
                found = sum(1 for w in words if w in all_content)
                citation["verified"] = found >= len(words) * 0.6
                if citation["verified"]:
                    total_verified += 1
            else:
                citation["verified"] = False

    return items, total_verified


def compute_overall_confidence(
    payload: dict,
    chunks: list[dict],
    min_similarity: float = 0.0,
    ocr_quality: float | None = None,
) -> float:
    """Calcule un score de confiance global (0.0-1.0) pour une analyse.

    Basé sur:
    - Nombre de chunks avec similarité > 0.5 (qualité contexte RAG)
    - Présence des champs critiques dans le payload
    - Score de confiance moyen des items (si applicable)
    - Qualité OCR des documents sources (si disponible)
    """
    scores: list[float] = []

    # 1. Qualité du contexte RAG (proportion de chunks pertinents)
    if chunks:
        good_chunks = sum(1 for c in chunks if c.get("similarity", 0) > 0.5)
        rag_quality = good_chunks / len(chunks)
        scores.append(rag_quality)

    # 2. Complétude du payload
    non_empty = sum(1 for v in payload.values() if v and v != [] and v != {})
    if payload:
        completeness = non_empty / len(payload)
        scores.append(completeness)

    # 3. Score de confiance moyen des items (checklist, critères)
    confidences: list[float] = []
    for key in ("checklist", "eligibility_conditions", "scoring_criteria"):
        items = payload.get(key, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "confidence" in item:
                    confidences.append(item["confidence"])
    if confidences:
        scores.append(sum(confidences) / len(confidences))

    # 4. Similarité minimale des chunks
    if min_similarity > 0:
        scores.append(min(1.0, min_similarity / 0.7))  # Normalisé: 0.7 = confiance max

    # 5. Pénalité OCR — si la qualité OCR est faible, la confiance est réduite
    if ocr_quality is not None:
        # Score OCR 0-100. Si < 90, pénalité linéaire.
        # 90+ → 1.0, 70 → 0.7, 50 → 0.5, 30 → 0.3
        ocr_factor = min(1.0, ocr_quality / 90.0)
        scores.append(ocr_factor)
        if ocr_quality < 70:
            logger.warning(
                f"Qualité OCR faible ({ocr_quality:.0f}/100) — "
                f"confiance pénalisée"
            )

    return round(sum(scores) / max(len(scores), 1), 2) if scores else 0.5
