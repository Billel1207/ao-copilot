import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class AoDocument(Base):
    __tablename__ = "ao_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_projects.id", ondelete="CASCADE"))
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    doc_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # RC|CCTP|CCAP|DPGF|BPU|AE|ATTRI|AUTRES
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_text: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|processing|done|error
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("NOW()"))

    project: Mapped["AoProject"] = relationship("AoProject", back_populates="documents")
    pages: Mapped[list["DocumentPage"]] = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["Chunk"]] = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("ao_documents.id", ondelete="CASCADE"))
    page_num: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    char_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section: Mapped[str | None] = mapped_column(String(255), nullable=True)

    document: Mapped["AoDocument"] = relationship("AoDocument", back_populates="pages")
