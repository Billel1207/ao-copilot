"""Tests pour app/services/jurisprudence_btp.py — base jurisprudentielle BTP."""
import pytest

from app.services.jurisprudence_btp import (
    JURISPRUDENCE_BTP,
    JurisprudenceEntry,
    get_relevant_jurisprudence,
    get_jurisprudence_context_for_analyzer,
)


# ── Data integrity ───────────────────────────────────────────────────────────

class TestJurisprudenceData:
    """Verify the jurisprudence database has correct structure."""

    def test_database_populated(self):
        assert len(JURISPRUDENCE_BTP) >= 30

    def test_all_entries_are_jurisprudence_entry(self):
        for entry in JURISPRUDENCE_BTP:
            assert isinstance(entry, JurisprudenceEntry)

    def test_all_entries_have_required_fields(self):
        for entry in JURISPRUDENCE_BTP:
            assert entry.reference, f"Missing reference: {entry}"
            assert entry.juridiction, f"Missing juridiction: {entry.reference}"
            assert entry.date, f"Missing date: {entry.reference}"
            assert entry.theme, f"Missing theme: {entry.reference}"
            assert entry.resume, f"Missing resume: {entry.reference}"
            assert entry.principe, f"Missing principe: {entry.reference}"
            assert len(entry.keywords) >= 1, f"Missing keywords: {entry.reference}"

    def test_valid_themes(self):
        valid_themes = {"penalites", "resiliation", "reception", "sous_traitance", "prix", "responsabilite", "procedure"}
        for entry in JURISPRUDENCE_BTP:
            assert entry.theme in valid_themes, (
                f"Invalid theme '{entry.theme}' for {entry.reference}"
            )

    def test_valid_juridictions(self):
        valid_juridictions = {"Conseil d'État", "CAA", "Cour de cassation", "TA"}
        for entry in JURISPRUDENCE_BTP:
            assert entry.juridiction in valid_juridictions, (
                f"Invalid juridiction '{entry.juridiction}' for {entry.reference}"
            )

    def test_date_format(self):
        """All dates should be ISO format YYYY-MM-DD."""
        import re
        for entry in JURISPRUDENCE_BTP:
            assert re.match(r"\d{4}-\d{2}-\d{2}", entry.date), (
                f"Invalid date format '{entry.date}' for {entry.reference}"
            )

    def test_entries_are_frozen(self):
        """JurisprudenceEntry should be immutable (frozen dataclass)."""
        entry = JURISPRUDENCE_BTP[0]
        with pytest.raises(AttributeError):
            entry.reference = "modified"

    def test_covers_all_themes(self):
        themes_found = {entry.theme for entry in JURISPRUDENCE_BTP}
        assert "penalites" in themes_found
        assert "resiliation" in themes_found
        assert "reception" in themes_found
        assert "sous_traitance" in themes_found
        assert "prix" in themes_found
        assert "responsabilite" in themes_found
        assert "procedure" in themes_found


# ── get_relevant_jurisprudence() ─────────────────────────────────────────────

class TestGetRelevantJurisprudence:

    def test_by_theme_penalites(self):
        results = get_relevant_jurisprudence("penalites")
        assert len(results) > 0
        for r in results:
            assert r["theme"] == "penalites"

    def test_by_theme_resiliation(self):
        results = get_relevant_jurisprudence("resiliation")
        assert len(results) > 0

    def test_by_theme_reception(self):
        results = get_relevant_jurisprudence("reception")
        assert len(results) > 0

    def test_result_structure(self):
        results = get_relevant_jurisprudence("penalites")
        assert len(results) > 0
        r = results[0]
        assert "reference" in r
        assert "principe" in r
        assert "resume" in r
        assert "theme" in r

    def test_max_results_respected(self):
        results = get_relevant_jurisprudence("penalites", max_results=2)
        assert len(results) <= 2

    def test_with_keywords_filters(self):
        results = get_relevant_jurisprudence("penalites", keywords=["proportionnalité"])
        assert len(results) > 0
        # First result should be most relevant to proportionnalité
        assert any("proportionn" in r["principe"].lower() for r in results[:2])

    def test_unknown_theme_returns_empty(self):
        results = get_relevant_jurisprudence("theme_inexistant")
        assert results == []

    def test_with_accented_keywords(self):
        results = get_relevant_jurisprudence("penalites", keywords=["pénalités"])
        assert len(results) > 0

    def test_default_max_results_is_5(self):
        results = get_relevant_jurisprudence("penalites")
        assert len(results) <= 5


# ── get_jurisprudence_context_for_analyzer() ─────────────────────────────────

class TestGetJurisprudenceContext:

    def test_ccap_context(self):
        context = get_jurisprudence_context_for_analyzer("ccap")
        assert isinstance(context, str)
        assert len(context) > 100
        assert "JURISPRUDENCE" in context
        assert "pénalités" in context.lower() or "penalites" in context.lower() or "CE," in context

    def test_ae_context(self):
        context = get_jurisprudence_context_for_analyzer("ae")
        assert isinstance(context, str)
        assert len(context) > 100

    def test_context_contains_references(self):
        context = get_jurisprudence_context_for_analyzer("ccap")
        # Should contain at least some CE references
        assert "CE," in context or "CAA" in context

    def test_context_has_footer_instructions(self):
        context = get_jurisprudence_context_for_analyzer("ccap")
        assert "jurisprudence" in context.lower()

    def test_ccap_has_more_themes_than_ae(self):
        ccap = get_jurisprudence_context_for_analyzer("ccap")
        ae = get_jurisprudence_context_for_analyzer("ae")
        # CCAP includes reception which AE does not
        assert len(ccap) >= len(ae)
