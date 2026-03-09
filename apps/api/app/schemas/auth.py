import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    org_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères")
        return v

    @field_validator("full_name", "org_name")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    org_id: uuid.UUID
    org_slug: str | None = None
    onboarding_completed: bool = False

    model_config = {"from_attributes": True}


class OrgOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    plan: str
    quota_docs: int

    model_config = {"from_attributes": True}
