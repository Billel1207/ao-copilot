"""Tests for docx_exporter.py — Word document generation.

Covers the full generate_export_docx() function by mocking fetch_export_data
to return ExportData with proper mock objects.
"""
import uuid
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import fields as dc_fields
from io import BytesIO

from app.services.export_data import ExportData, DictObj


# ---------------------------------------------------------------------------
# Helpers — build realistic ExportData without touching the DB
# ---------------------------------------------------------------------------

def _mock_project(**overrides):
    """Create a mock AoProject with all fields the exporter accesses."""
    p = MagicMock()
    p.id = overrides.get("id", uuid.uuid4())
    p.title = overrides.get("title", "Construction gymnase communal")
    p.ref_marche = overrides.get("ref_marche", "AO-2024-001")
    p.acheteur = overrides.get("acheteur", "Mairie de Lyon")
    p.budget_estime = overrides.get("budget_estime", 1500000)
    p.status = overrides.get("status", "analyzed")
    p.org_id = overrides.get("org_id", uuid.uuid4())
    p.created_at = overrides.get("created_at", None)
    p.date_limite = overrides.get("date_limite", "2024-06-15")
    p.localisation = overrides.get("localisation", "Lyon 69000")
    p.type_marche = overrides.get("type_marche", "Travaux")
    p.allotissement = overrides.get("allotissement", "Lot unique")
    p.source_ao = overrides.get("source_ao", "BOAMP")
    return p


class _FakeDoc:
    """Fake document with all attributes the exporter accesses."""
    def __init__(self, name="CCAP.pdf", doc_type="CCAP"):
        self.original_name = name
        self.doc_type = doc_type
        self.page_count = 10
        self.status = "done"
        self.file_size = 50000
        self.ocr_quality_score = 95
        self.has_text = True
        self.created_at = None
        self.s3_key = "docs/test.pdf"
        self.id = uuid.uuid4()
        self.error_message = None
        self.ocr_warning = None

    def __getattr__(self, name):
        # Return safe defaults for any attribute not explicitly set
        return None

def _mock_doc(name="CCAP.pdf", doc_type="CCAP"):
    return _FakeDoc(name, doc_type)


def _full_export_data(**overrides):
    """Build a complete ExportData with realistic payloads."""
    project = overrides.pop("project", _mock_project())
    documents = overrides.pop("documents", [_mock_doc()])

    summary = overrides.pop("summary", {
        "project_overview": {
            "object": "Marché de travaux pour la construction d'un gymnase.",
            "buyer": "Mairie de Lyon",
            "location": "Lyon 69000",
            "market_type": "Travaux",
            "deadline_submission": "2024-06-15",
            "estimated_budget": "1 500 000 €",
            "scope": "Construction gymnase communal",
        },
        "key_points": [
            {"point": "Budget 1.5M€", "importance": "Élevée"},
            {"point": "Délai 12 mois", "importance": "Moyenne"},
        ],
        "risks": [
            {"risk": "Pénalités de retard élevées", "severity": "CRITIQUE"},
        ],
        "actions_next_48h": [
            {"action": "Vérifier attestations", "priority": "P0", "responsible": "Chef projet"},
            {"action": "Préparer DC1", "priority": "P1", "responsible": "Administratif"},
        ],
        "confidence_score": 0.92,
    })

    gonogo_dict = overrides.pop("gonogo", {
        "score": 72,
        "recommendation": "GO",
        "summary": "Marché intéressant.",
        "strengths": ["Budget confortable"],
        "risks": ["Pénalités"],
        "dimension_scores": [
            {"name": "Technique", "score": 80, "weight": 15, "confidence": 0.9, "explanation": "Bon"},
        ],
        "breakdown": {"Technique": 8, "Finance": 7},
    })

    checklist_items = overrides.pop("checklist_items", [
        MagicMock(requirement="DC1 signé", criticality="Eliminatoire", status="OK",
                  category="Administratif", citations=["Art. 3"], confidence=0.95),
        MagicMock(requirement="Attestation RC", criticality="Important", status="MANQUANT",
                  category="Assurances", citations=[], confidence=0.88),
    ])

    criteria = overrides.pop("criteria", {
        "eligibility_conditions": [{"condition": "DC1", "status": "OK"}],
        "evaluation": {
            "scoring_criteria": [
                {"criterion": "Prix", "weight": 40, "detail": "Note sur 40"},
                {"criterion": "Technique", "weight": 60, "detail": "Mémoire"},
            ],
        },
    })

    data = ExportData(
        project=project,
        documents=documents,
        summary=summary,
        criteria=criteria,
        gonogo=gonogo_dict,
        gonogo_obj=DictObj(gonogo_dict),
        timeline=overrides.pop("timeline", {"etapes": []}),
        timeline_obj=DictObj(overrides.pop("timeline_obj_dict", {"etapes": []})),
        checklist_items=checklist_items,
        checklist_stats=overrides.pop("checklist_stats", {"eliminatoire": 1, "important": 1, "info": 0, "ok": 1}),
        confidence=overrides.pop("confidence", 0.91),
        ccap_analysis=overrides.pop("ccap_analysis", None),
        rc_analysis=overrides.pop("rc_analysis", None),
        ae_analysis=overrides.pop("ae_analysis", None),
        cctp_analysis=overrides.pop("cctp_analysis", None),
        dc_check=overrides.pop("dc_check", None),
        conflicts=overrides.pop("conflicts", None),
        cashflow=overrides.pop("cashflow", None),
        subcontracting=overrides.pop("subcontracting", None),
        questions=overrides.pop("questions", None),
        scoring=overrides.pop("scoring", None),
        dpgf_pricing=overrides.pop("dpgf_pricing", None),
        glossaire_btp=overrides.pop("glossaire_btp", None),
        days_remaining=overrides.pop("days_remaining", 45),
        deadline_str=overrides.pop("deadline_str", "15 juin 2024"),
        ccag_derogations=overrides.pop("ccag_derogations", None),
        ccap_clauses_risquees=overrides.pop("ccap_clauses_risquees", None),
    )
    return data


# ===========================================================================
# Tests
# ===========================================================================

class TestDocxGeneration:

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_generates_valid_docx_bytes(self, mock_fetch):
        mock_fetch.return_value = _full_export_data()
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)
        assert result[:2] == b"PK"  # ZIP/DOCX signature

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_minimal_data(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            summary=None, gonogo=None, criteria=None,
            checklist_items=[], documents=[],
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)
        assert len(result) > 1000

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_ccap_risks(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            ccap_analysis={
                "clauses_risquees": [
                    {"article_reference": "Art. 5", "clause_text": "Pénalités",
                     "risk_level": "CRITIQUE", "risk_type": "Pénalités",
                     "conseil": "Négocier", "citation": "5.1"},
                ],
                "ccag_derogations": [],
                "score_risque_global": 75,
                "nb_clauses_critiques": 1,
            },
            ccap_clauses_risquees=[
                {"article_reference": "Art. 5", "risk_level": "CRITIQUE"},
            ],
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_conflicts(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            conflicts={
                "conflits": [
                    {"type": "Contradiction", "severity": "CRITIQUE",
                     "description": "Délai contradictoire", "doc1": "CCAP", "doc2": "RC",
                     "detail": "CCAP dit 30j, RC dit 60j", "recommandation": "Clarifier"},
                ],
                "nombre_conflits": 1,
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_questions(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            questions=[
                {"question": "Quel est le délai exact ?", "priority": "HAUTE",
                 "context": "Art. 5 CCAP", "category": "Délais"},
            ],
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_scoring(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            scoring={
                "criteria": [
                    {"criterion": "Prix", "weight": 40, "estimated_score": 15,
                     "max_score": 20, "justification": "Compétitif"},
                ],
                "note_technique_estimee": 14,
                "note_globale_estimee": 15,
                "classement_probable": "Top 3",
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_rc_analysis(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            rc_analysis={
                "conditions_participation": [
                    {"condition": "Chiffre d'affaires > 3M€", "type": "financière", "status": "OK"},
                ],
                "nombre_lots": 3,
                "duree_validite_offres": "120 jours",
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_ae_analysis(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            ae_analysis={
                "clauses": [
                    {"clause": "Retenue de garantie 5%", "risk_level": "MOYEN",
                     "conseil": "Standard"},
                ],
                "score_risque": 35,
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_subcontracting(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            subcontracting={
                "allowed": True,
                "max_percentage": 30,
                "conditions": ["Agrément préalable"],
                "risks": ["Responsabilité solidaire"],
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_cashflow(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            cashflow={
                "monthly_cashflow": [
                    {"month": "2024-01", "income": 100000, "expenses": 80000, "balance": 20000},
                    {"month": "2024-02", "income": 120000, "expenses": 90000, "balance": 50000},
                ],
                "total_income": 220000,
                "total_expenses": 170000,
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_dpgf_pricing(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            dpgf_pricing=[
                {"designation": "Terrassement", "quantite": 500, "unite": "m3",
                 "prix_unitaire": 25.0, "montant_ht": 12500.0},
            ],
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_cctp(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            cctp_analysis={
                "exigences_techniques": [
                    {"exigence": "Norme NF EN 1090", "category": "Structure",
                     "risk_level": "CRITIQUE", "detail": "Certification requise"},
                ],
                "score_complexite": 72,
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_dc_check(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            dc_check={
                "documents_requis": [
                    {"document": "DC1", "status": "OK", "detail": "Signé"},
                    {"document": "Kbis", "status": "MANQUANT", "detail": "À fournir"},
                ],
                "alertes": ["Kbis manquant"],
            },
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_all_sections(self, mock_fetch):
        """Full test with every section populated."""
        mock_fetch.return_value = _full_export_data(
            ccap_analysis={"clauses_risquees": [], "ccag_derogations": [], "score_risque_global": 30},
            rc_analysis={"conditions_participation": [], "nombre_lots": 1},
            ae_analysis={"clauses": [], "score_risque": 20},
            cctp_analysis={"exigences_techniques": [], "score_complexite": 50},
            dc_check={"documents_requis": [], "alertes": []},
            conflicts={"conflits": [], "nombre_conflits": 0},
            cashflow={"monthly_cashflow": []},
            subcontracting={"allowed": False},
            questions=[],
            scoring={"criteria": [], "note_globale_estimee": 14},
            dpgf_pricing=[],
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)
        assert len(result) > 5000  # A full report should be substantial

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_with_unicode_title(self, mock_fetch):
        project = _mock_project(title="Rénovation école maternelle « Les Étoiles »")
        mock_fetch.return_value = _full_export_data(project=project)
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.docx_exporter.fetch_export_data")
    def test_docx_nogo_recommendation(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            gonogo={"score": 25, "recommendation": "NO-GO", "summary": "Trop risqué",
                    "strengths": [], "risks": ["Budget insuffisant"],
                    "dimension_scores": [], "breakdown": {}},
        )
        from app.services.docx_exporter import generate_export_docx
        result = generate_export_docx(MagicMock(), str(uuid.uuid4()))
        assert isinstance(result, bytes)


class TestMemoGeneration:

    @patch("app.services.memo_exporter.fetch_export_data")
    def test_generates_valid_memo_bytes(self, mock_fetch):
        mock_fetch.return_value = _full_export_data()
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        from app.services.memo_exporter import generate_memo_technique
        result = generate_memo_technique(mock_db, str(uuid.uuid4()))
        assert isinstance(result, bytes)
        assert result[:2] == b"PK"

    @patch("app.services.memo_exporter.fetch_export_data")
    def test_memo_minimal_data(self, mock_fetch):
        mock_fetch.return_value = _full_export_data(
            summary=None, gonogo=None, criteria=None,
            checklist_items=[], documents=[],
        )
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        from app.services.memo_exporter import generate_memo_technique
        result = generate_memo_technique(mock_db, str(uuid.uuid4()))
        assert isinstance(result, bytes)

    @patch("app.services.memo_exporter.fetch_export_data")
    def test_memo_unicode_content(self, mock_fetch):
        project = _mock_project(title="Réhabilitation « Château d'Eau » — Phase 2")
        mock_fetch.return_value = _full_export_data(project=project)
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        from app.services.memo_exporter import generate_memo_technique
        result = generate_memo_technique(mock_db, str(uuid.uuid4()))
        assert isinstance(result, bytes)
