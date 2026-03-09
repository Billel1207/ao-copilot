import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    original_name: str
    doc_type: str | None
    page_count: int | None
    file_size_kb: int | None
    has_text: bool
    status: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class SignedUrlOut(BaseModel):
    url: str
    expires_in: int
