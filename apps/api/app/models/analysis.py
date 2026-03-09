import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Float, Integer, Text, JSON, text, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_documents.id", ondelete="CASCADE"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_projects.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # float[] stored as JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    document: Mapped["AoDocument"] = relationship("AoDocument", back_populates="chunks")


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_projects.id", ondelete="CASCADE"))
    result_type: Mapped[str] = mapped_column(String(30), nullable=False)  # summary|checklist|criteria|questions
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    project: Mapped["AoProject"] = relationship("AoProject", back_populates="extraction_results")


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_projects.id", ondelete="CASCADE"))
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    criticality: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="MANQUANT")
    what_to_provide: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    project: Mapped["AoProject"] = relationship("AoProject", back_populates="checklist_items")


class CriteriaItem(Base):
    __tablename__ = "criteria_items"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_projects.id", ondelete="CASCADE"))
    item_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # eligibility|scoring
    criterion: Mapped[str] = mapped_column(Text, nullable=False)
    weight_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    condition_type: Mapped[str | None] = mapped_column(String(10), nullable=True)  # hard|soft
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    citations: Mapped[list | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    project: Mapped["AoProject"] = relationship("AoProject", back_populates="criteria_items")


class AccessLog(Base):
    __tablename__ = "access_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ua: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))
