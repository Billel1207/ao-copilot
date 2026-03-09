import uuid
from datetime import datetime
from pydantic import BaseModel
from typing import Literal


class ProjectCreate(BaseModel):
    title: str
    reference: str | None = None
    buyer: str | None = None
    market_type: Literal["travaux", "services", "fournitures"] | None = None
    submission_deadline: datetime | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    reference: str | None = None
    buyer: str | None = None
    market_type: str | None = None
    submission_deadline: datetime | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    title: str
    reference: str | None
    buyer: str | None
    market_type: str | None
    status: str
    submission_deadline: datetime | None
    # Win/Loss tracking fields
    result: str | None = None
    result_amount_eur: float | None = None
    result_date: datetime | None = None
    result_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int
