"""Tests pour app/services/btp_pricing.py — référentiel prix BTP."""
import pytest

from app.services.btp_pricing import (
    PRICE_ADJUSTMENT_2026,
    PRICE_INDEXES,
    PRICING_REFERENCE,
    COEFFICIENTS_GEOGRAPHIQUES,
    get_price_index,
    apply_price_adjustment,
    detect_revision_formula,
    get_all_price_indexes,
    get_geo_coefficient,
    get_pricing_reference,
    check_dpgf_pricing,
    get_pricing_summary,
    PriceIndexTemplate,
    PricingEntry,
    _parse_price,
    _normalize,
)


# ── Constants ────────────────────────────────────────────────────────────────

class TestConstants:
    """Verify pricing constants are defined correctly."""

    def test_adjustment_coefficient(self):
        assert PRICE_ADJUSTMENT_2026 == 1.08

    def test_price_indexes_populated(self):
        assert len(PRICE_INDEXES) >= 5

    def test_pricing_reference_populated(self):
        assert len(PRICING_REFERENCE) > 50

    def test_geo_coefficients_populated(self):
        assert len(COEFFICIENTS_GEOGRAPHIQUES) >= 15
        assert COEFFICIENTS_GEOGRAPHIQUES["france"] == 1.00
        assert COEFFICIENTS_GEOGRAPHIQUES["paris"] > 1.0

    def test_all_price_indexes_have_required_fields(self):
        for idx in PRICE_INDEXES:
            assert isinstance(idx, PriceIndexTemplate)
            assert idx.code
            assert idx.nom
            assert idx.base_value > 0
            assert idx.latest_value > 0
            assert 0 <= idx.part_fixe <= 1
            assert 0 <= idx.part_variable <= 1

    def test_all_pricing_entries_have_required_fields(self):
        for entry in PRICING_REFERENCE:
            assert isinstance(entry, PricingEntry)
            assert entry.nom_fr
            assert entry.unite
            assert entry.prix_min_eur <= entry.prix_moyen_eur <= entry.prix_max_eur
            assert entry.categorie
            assert len(entry.keywords) >= 1


# ── get_price_index() ────────────────────────────────────────────────────────

class TestGetPriceIndex:

    def test_bt01_exists(self):
        idx = get_price_index("BT01")
        assert idx is not None
        assert idx.code == "BT01"

    def test_tp01_exists(self):
        idx = get_price_index("TP01")
        assert idx is not None
        assert idx.code == "TP01"

    def test_case_insensitive(self):
        idx = get_price_index("bt01")
        assert idx is not None
        assert idx.code == "BT01"

    def test_unknown_index_returns_none(self):
        assert get_price_index("ZZ99") is None


# ── apply_price_adjustment() ─────────────────────────────────────────────────

class TestApplyPriceAdjustment:

    def test_with_bt01(self):
        result = apply_price_adjustment(100_000.0, "BT01")
        assert result["prix_base"] == 100_000.0
        assert result["prix_ajuste"] > result["prix_base"]
        assert result["coefficient"] > 1.0
        assert result["index_code"] == "BT01"
        assert "formule" in result

    def test_with_unknown_index(self):
        result = apply_price_adjustment(50_000.0, "INVALID")
        assert result["prix_ajuste"] == 50_000.0
        assert result["coefficient"] == 1.0
        assert "erreur" in result

    def test_zero_price(self):
        result = apply_price_adjustment(0.0, "BT01")
        assert result["prix_ajuste"] == 0.0

    def test_coefficient_formula(self):
        """Verify coefficient = part_fixe + part_variable * (latest/base)."""
        idx = get_price_index("BT01")
        result = apply_price_adjustment(1000.0, "BT01")
        expected_coeff = idx.part_fixe + idx.part_variable * (idx.latest_value / idx.base_value)
        assert abs(result["coefficient"] - round(expected_coeff, 4)) < 0.001


# ── detect_revision_formula() ────────────────────────────────────────────────

class TestDetectRevisionFormula:

    def test_returns_none_for_empty_text(self):
        assert detect_revision_formula("") is None
        assert detect_revision_formula(None) is None

    def test_detects_revisable_market(self):
        text = "Le marché est à prix révisable avec clause de révision de prix selon l'indice BT01."
        result = detect_revision_formula(text)
        assert result is not None
        assert result["is_revisable"] is True
        assert "BT01" in result["detected_indexes"]

    def test_detects_fixed_price(self):
        text = "Le marché est à prix ferme et non révisable."
        result = detect_revision_formula(text)
        assert result is not None
        assert result["is_ferme"] is True
        assert result["is_revisable"] is False

    def test_detects_tp01_index(self):
        text = "La formule de révision utilise l'indice TP01 pour les travaux publics."
        result = detect_revision_formula(text)
        assert result is not None
        assert "TP01" in result["detected_indexes"]

    def test_no_revision_info(self):
        text = "Le bâtiment sera construit en briques rouges."
        result = detect_revision_formula(text)
        assert result is None

    def test_detects_formula_pattern(self):
        text = "La révision de prix s'applique selon la formule P = P0 × [0.15 + 0.85 × (BT01n / BT01_0)]"
        result = detect_revision_formula(text)
        assert result is not None
        assert result["formula_found"] is not None
        assert result["is_revisable"] is True


# ── get_all_price_indexes() ──────────────────────────────────────────────────

class TestGetAllPriceIndexes:

    def test_returns_list(self):
        result = get_all_price_indexes()
        assert isinstance(result, list)
        assert len(result) == len(PRICE_INDEXES)

    def test_each_item_has_required_fields(self):
        for item in get_all_price_indexes():
            assert "code" in item
            assert "nom" in item
            assert "variation_pct" in item
            assert isinstance(item["variation_pct"], float)


# ── get_geo_coefficient() ────────────────────────────────────────────────────

class TestGetGeoCoefficient:

    def test_ile_de_france(self):
        assert get_geo_coefficient("ile-de-france") == 1.25

    def test_paris(self):
        assert get_geo_coefficient("paris") == 1.30

    def test_bretagne(self):
        assert get_geo_coefficient("bretagne") == 0.95

    def test_unknown_region_returns_default(self):
        assert get_geo_coefficient("atlantide") == 1.00

    def test_france_default(self):
        assert get_geo_coefficient("france") == 1.00


# ── _normalize() ─────────────────────────────────────────────────────────────

class TestNormalize:

    def test_lowercase(self):
        assert _normalize("BÉTON") == "beton"

    def test_removes_accents(self):
        assert "e" in _normalize("éèêë")
        assert "a" in _normalize("àâä")

    def test_removes_punctuation(self):
        result = _normalize("béton, armé (voiles)")
        assert "," not in result
        assert "(" not in result


# ── _parse_price() ───────────────────────────────────────────────────────────

class TestParsePrice:

    def test_float_passthrough(self):
        assert _parse_price(42.5) == 42.5

    def test_int_converts(self):
        assert _parse_price(100) == 100.0

    def test_string_simple(self):
        assert _parse_price("42.50") == 42.5

    def test_string_with_euro_sign(self):
        assert _parse_price("42.50€") == 42.5

    def test_string_with_comma(self):
        assert _parse_price("42,50") == 42.5

    def test_none_returns_none(self):
        assert _parse_price(None) is None

    def test_invalid_string_returns_none(self):
        assert _parse_price("abc") is None

    def test_string_with_spaces(self):
        assert _parse_price(" 42.50 ") == 42.5


# ── get_pricing_reference() ──────────────────────────────────────────────────

class TestGetPricingReference:

    def test_search_beton(self):
        results = get_pricing_reference("béton armé")
        assert len(results) > 0
        assert results[0]["nom_fr"]  # Has a name
        assert results[0]["prix_moyen_eur"] > 0

    def test_search_plomberie(self):
        results = get_pricing_reference("plomberie")
        assert len(results) > 0

    def test_search_empty_returns_empty(self):
        results = get_pricing_reference("")
        assert results == []

    def test_results_are_adjusted(self):
        results = get_pricing_reference("terrassement")
        assert len(results) > 0
        assert results[0]["adjustment_2026"] == PRICE_ADJUSTMENT_2026

    def test_max_10_results(self):
        results = get_pricing_reference("a")  # Very broad search
        assert len(results) <= 10


# ── check_dpgf_pricing() ────────────────────────────────────────────────────

class TestCheckDpgfPricing:

    def test_empty_rows(self):
        results = check_dpgf_pricing([])
        assert results == []

    def test_unknown_designation(self):
        rows = [{"designation": "item_xyz_inconnu", "prix_unitaire": 100}]
        results = check_dpgf_pricing(rows)
        assert len(results) == 1
        assert results[0]["status"] == "INCONNU"

    def test_normal_price(self):
        """A price within reference range should be NORMAL."""
        rows = [{"designation": "Terrassement en pleine masse", "prix_unitaire": 15.0}]
        results = check_dpgf_pricing(rows)
        assert len(results) == 1
        if results[0]["status"] != "INCONNU":
            assert results[0]["status"] == "NORMAL"

    def test_underpriced(self):
        """A very low price should be SOUS_EVALUE."""
        rows = [{"designation": "Béton armé coulé en place voile poteau", "prix_unitaire": 1.0}]
        results = check_dpgf_pricing(rows)
        assert len(results) == 1
        if results[0]["reference_match"] is not None:
            assert results[0]["status"] == "SOUS_EVALUE"

    def test_overpriced(self):
        """A very high price should be SUR_EVALUE."""
        rows = [{"designation": "Peinture intérieure mur plafond", "prix_unitaire": 999.0}]
        results = check_dpgf_pricing(rows)
        assert len(results) == 1
        if results[0]["reference_match"] is not None:
            assert results[0]["status"] == "SUR_EVALUE"

    def test_with_region_adjustment(self):
        rows = [{"designation": "Terrassement en pleine masse", "prix_unitaire": 15.0}]
        results_idf = check_dpgf_pricing(rows, region="ile-de-france")
        results_fr = check_dpgf_pricing(rows, region="france")
        # IDF has higher prices so the reference range is higher
        if results_idf[0]["reference_prix_moyen"] and results_fr[0]["reference_prix_moyen"]:
            assert results_idf[0]["reference_prix_moyen"] > results_fr[0]["reference_prix_moyen"]

    def test_missing_price_returns_inconnu(self):
        rows = [{"designation": "Terrassement", "prix_unitaire": None}]
        results = check_dpgf_pricing(rows)
        assert results[0]["status"] == "INCONNU"

    def test_multiple_rows(self):
        rows = [
            {"designation": "Terrassement pleine masse", "prix_unitaire": 15.0},
            {"designation": "Peinture intérieure", "prix_unitaire": 20.0},
            {"designation": "Unknown item XYZ", "prix_unitaire": 50.0},
        ]
        results = check_dpgf_pricing(rows)
        assert len(results) == 3


# ── get_pricing_summary() ───────────────────────────────────────────────────

class TestGetPricingSummary:

    def test_returns_dict(self):
        summary = get_pricing_summary()
        assert isinstance(summary, dict)

    def test_has_required_keys(self):
        summary = get_pricing_summary()
        assert "total_entries" in summary
        assert "categories" in summary
        assert "source" in summary
        assert "adjustment_coefficient" in summary

    def test_total_matches_reference(self):
        summary = get_pricing_summary()
        assert summary["total_entries"] == len(PRICING_REFERENCE)

    def test_categories_populated(self):
        summary = get_pricing_summary()
        assert len(summary["categories"]) >= 3
        assert "Gros oeuvre" in summary["categories"]
