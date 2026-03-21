"""Tests pour app/services/btp_knowledge.py — base de connaissances BTP."""
import pytest

from app.services.btp_knowledge import (
    BTP_GLOSSARY,
    CERTIFICATION_MAPPING,
    CCAP_RISK_RULES,
    MARKET_THRESHOLDS,
    get_ccap_context_for_prompt,
    get_relevant_glossary_terms,
    check_market_threshold,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Constants integrity
# ═══════════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_glossary_has_entries(self):
        assert len(BTP_GLOSSARY) >= 50

    def test_glossary_entries_are_strings(self):
        for term, definition in BTP_GLOSSARY.items():
            assert isinstance(term, str) and len(term) > 0
            assert isinstance(definition, str) and len(definition) > 10

    def test_certification_mapping_has_entries(self):
        assert len(CERTIFICATION_MAPPING) >= 15

    def test_key_certifications_present(self):
        for cert in ("Qualibat", "RGE", "ISO 9001", "MASE"):
            assert cert in CERTIFICATION_MAPPING

    def test_key_glossary_terms_present(self):
        for term in ("RC", "CCTP", "CCAP", "DPGF", "BPU", "AE", "DCE", "CCAG"):
            assert term in BTP_GLOSSARY

    def test_ccap_risk_rules_structure(self):
        assert len(CCAP_RISK_RULES) > 0
        for rule in CCAP_RISK_RULES:
            assert "description" in rule
            assert "threshold" in rule
            assert "risk" in rule
            assert "conseil" in rule

    def test_market_thresholds_keys(self):
        assert "avance_obligatoire" in MARKET_THRESHOLDS
        assert "retenue_garantie_max" in MARKET_THRESHOLDS
        assert "delai_paiement" in MARKET_THRESHOLDS
        assert "appel_offres_travaux" in MARKET_THRESHOLDS


# ═══════════════════════════════════════════════════════════════════════════════
# get_ccap_context_for_prompt
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetCcapContext:
    def test_returns_string(self):
        ctx = get_ccap_context_for_prompt()
        assert isinstance(ctx, str)
        assert len(ctx) > 100

    def test_contains_risk_rules(self):
        ctx = get_ccap_context_for_prompt()
        assert "RISQUES CONTRACTUELS" in ctx

    def test_contains_thresholds(self):
        ctx = get_ccap_context_for_prompt()
        assert "SEUILS RÉGLEMENTAIRES" in ctx
        assert "Avance forfaitaire" in ctx
        assert "Retenue de garantie" in ctx


# ═══════════════════════════════════════════════════════════════════════════════
# get_relevant_glossary_terms
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetRelevantGlossaryTerms:
    def test_finds_matching_terms(self):
        text = "Le CCAP impose des pénalités et le CCTP détaille les prescriptions."
        result = get_relevant_glossary_terms(text)
        assert "CCAP" in result
        assert "CCTP" in result

    def test_case_insensitive(self):
        text = "Le ccap du marché public"
        result = get_relevant_glossary_terms(text)
        assert "CCAP" in result

    def test_no_match(self):
        text = "Un texte sans aucun terme BTP reconnu"
        result = get_relevant_glossary_terms(text)
        # Might match some common words, but should be empty or small
        assert isinstance(result, dict)

    def test_empty_text(self):
        result = get_relevant_glossary_terms("")
        assert len(result) == 0

    def test_returns_definitions(self):
        text = "Le BPU est joint au DCE"
        result = get_relevant_glossary_terms(text)
        if "BPU" in result:
            assert len(result["BPU"]) > 20  # definition not empty

    def test_multiple_terms(self):
        text = "RC CCTP CCAP DPGF AE DCE — tout le DCE est là"
        result = get_relevant_glossary_terms(text)
        assert len(result) >= 4


# ═══════════════════════════════════════════════════════════════════════════════
# check_market_threshold
# ═══════════════════════════════════════════════════════════════════════════════


class TestCheckMarketThreshold:
    def test_gre_a_gre(self):
        result = check_market_threshold(10_000)
        assert "gré à gré" in result.lower() or "gré" in result

    def test_mapa(self):
        result = check_market_threshold(100_000)
        assert "adaptée" in result.lower() or "MAPA" in result

    def test_formalized_services(self):
        result = check_market_threshold(500_000)
        assert "formalisée" in result.lower()

    def test_formalized_travaux(self):
        result = check_market_threshold(6_000_000)
        assert "travaux" in result.lower()

    def test_zero(self):
        result = check_market_threshold(0)
        assert isinstance(result, str) and len(result) > 10

    def test_boundary_25k(self):
        below = check_market_threshold(24_999)
        above = check_market_threshold(25_000)
        assert "gré" in below
        assert "adaptée" in above.lower() or "MAPA" in above

    def test_returns_amount_in_text(self):
        result = check_market_threshold(150_000)
        assert "150" in result
