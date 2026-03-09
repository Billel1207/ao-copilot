import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


class Citation(BaseModel):
    doc: str
    page: int
    quote: str


class KeyPoint(BaseModel):
    label: str
    value: str
    citations: list[Citation] = []


class Risk(BaseModel):
    risk: str
    severity: Literal["high", "medium", "low"]
    why: str
    citations: list[Citation] = []


class NextAction(BaseModel):
    action: str
    owner_role: str
    priority: Literal["P0", "P1", "P2"]


class ProjectOverview(BaseModel):
    title: str
    buyer: str
    scope: str
    location: str
    deadline_submission: str
    site_visit_required: bool
    market_type: str | None
    estimated_budget: str | None


class SummaryOut(BaseModel):
    project_overview: ProjectOverview
    key_points: list[KeyPoint]
    risks: list[Risk]
    actions_next_48h: list[NextAction]
    generated_at: datetime | None = None
    confidence_overall: float | None = None


class ChecklistItemOut(BaseModel):
    id: uuid.UUID
    category: str | None
    requirement: str
    criticality: str | None
    status: str
    what_to_provide: str | None
    citations: list[Citation] = []
    confidence: float | None
    assigned_to: uuid.UUID | None
    notes: str | None

    model_config = {"from_attributes": True}


class ChecklistStats(BaseModel):
    OK: int = 0
    MANQUANT: int = 0
    A_CLARIFIER: int = 0


class CriticalityStats(BaseModel):
    Eliminatoire: int = 0
    Important: int = 0
    Info: int = 0


class ChecklistItemUpdate(BaseModel):
    """Schema strict pour PATCH checklist item — évite l'injection de champs arbitraires."""
    status: Literal["OK", "MANQUANT", "À CLARIFIER"] | None = None
    notes: str | None = Field(None, max_length=2000)
    assigned_to: uuid.UUID | None = None


class ChecklistOut(BaseModel):
    total: int
    by_status: dict[str, int]
    by_criticality: dict[str, int]
    checklist: list[ChecklistItemOut]


class EligibilityCondition(BaseModel):
    condition: str
    type: Literal["hard", "soft"]
    citations: list[Citation] = []


class ScoringCriterion(BaseModel):
    criterion: str
    weight_percent: float | None
    notes: str | None
    citations: list[Citation] = []


class EvaluationOut(BaseModel):
    eligibility_conditions: list[EligibilityCondition]
    scoring_criteria: list[ScoringCriterion]
    total_weight_check: float | None
    confidence: float | None


class CriteriaOut(BaseModel):
    evaluation: EvaluationOut


class AnalysisStatusOut(BaseModel):
    project_id: uuid.UUID
    status: str
    progress_pct: int
    current_step: str
    error: str | None = None
