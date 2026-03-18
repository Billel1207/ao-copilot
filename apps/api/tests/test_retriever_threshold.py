"""Tests pour le seuil dynamique RAG (retriever.py get_dynamic_threshold).

Couvre :
- OCR quality > 80% → threshold 0.50
- OCR quality 50-80% → threshold 0.40
- OCR quality < 50% → threshold 0.30
- Sans OCR quality → fallback depuis DB ou défaut
- get_max_similarity
- SIMILARITY_THRESHOLD constant
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.retriever import (
    get_dynamic_threshold,
    get_max_similarity,
    SIMILARITY_THRESHOLD,
)


def _mock_db(avg_ocr_score=None):
    """Return a mock sync Session with a fake AVG(ocr_quality_score) result."""
    db = MagicMock()
    row = MagicMock()
    row.__getitem__ = lambda self, idx: avg_ocr_score if idx == 0 else None
    db.execute.return_value.fetchone.return_value = row if avg_ocr_score is not None else MagicMock(__getitem__=lambda s, i: None)
    return db


# ── get_dynamic_threshold with explicit ocr_quality ─────────────────────

def test_threshold_high_ocr_quality():
    """OCR quality > 80% → threshold 0.50 (strict)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=95.0)
    assert result == 0.50


def test_threshold_medium_ocr_quality():
    """OCR quality 50-80% → threshold 0.40 (moderate)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=65.0)
    assert result == 0.40


def test_threshold_low_ocr_quality():
    """OCR quality < 50% → threshold 0.30 (lenient)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=30.0)
    assert result == 0.30


def test_threshold_boundary_80():
    """OCR quality exactement 80% → threshold 0.40 (>=50 et <=80)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=80.0)
    assert result == 0.40


def test_threshold_boundary_50():
    """OCR quality exactement 50% → threshold 0.40 (>=50)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=50.0)
    assert result == 0.40


def test_threshold_boundary_just_above_80():
    """OCR quality 80.1% → threshold 0.50 (>80)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=80.1)
    assert result == 0.50


def test_threshold_boundary_just_below_50():
    """OCR quality 49.9% → threshold 0.30 (<50)."""
    db = MagicMock()
    result = get_dynamic_threshold(db, "proj-1", ocr_quality=49.9)
    assert result == 0.30


# ── get_dynamic_threshold without ocr_quality (DB lookup) ────────────────

def test_threshold_from_db_high():
    """Sans ocr_quality, récupère AVG depuis DB : 90 → 0.50."""
    db = _mock_db(avg_ocr_score=90.0)
    result = get_dynamic_threshold(db, "proj-1")
    assert result == 0.50


def test_threshold_from_db_medium():
    """Sans ocr_quality, récupère AVG depuis DB : 60 → 0.40."""
    db = _mock_db(avg_ocr_score=60.0)
    result = get_dynamic_threshold(db, "proj-1")
    assert result == 0.40


def test_threshold_from_db_low():
    """Sans ocr_quality, récupère AVG depuis DB : 25 → 0.30."""
    db = _mock_db(avg_ocr_score=25.0)
    result = get_dynamic_threshold(db, "proj-1")
    assert result == 0.30


def test_threshold_db_returns_none_defaults_to_high():
    """DB retourne NULL (aucun doc avec OCR score) → fallback 85.0 → 0.50."""
    db = MagicMock()
    row = MagicMock()
    row.__getitem__ = lambda self, idx: None
    db.execute.return_value.fetchone.return_value = row
    result = get_dynamic_threshold(db, "proj-1")
    assert result == 0.50  # 85.0 > 80 → 0.50


def test_threshold_db_exception_defaults_to_high():
    """Exception DB → fallback 85.0 → 0.50."""
    db = MagicMock()
    db.execute.side_effect = Exception("DB connection error")
    result = get_dynamic_threshold(db, "proj-1")
    assert result == 0.50


# ── get_max_similarity ──────────────────────────────────────────────────

def test_max_similarity_empty_list():
    """Liste vide → 0.0."""
    assert get_max_similarity([]) == 0.0


def test_max_similarity_single_chunk():
    """Un seul chunk → sa similarity."""
    chunks = [{"similarity": 0.85}]
    assert get_max_similarity(chunks) == 0.85


def test_max_similarity_multiple_chunks():
    """Plusieurs chunks → le max."""
    chunks = [
        {"similarity": 0.60},
        {"similarity": 0.92},
        {"similarity": 0.45},
    ]
    assert get_max_similarity(chunks) == 0.92


def test_max_similarity_missing_field():
    """Chunk sans 'similarity' → utilise 0.0."""
    chunks = [{"content": "test"}]
    assert get_max_similarity(chunks) == 0.0


# ── Constants ───────────────────────────────────────────────────────────

def test_default_similarity_threshold():
    """SIMILARITY_THRESHOLD par défaut est 0.50."""
    assert SIMILARITY_THRESHOLD == 0.50
