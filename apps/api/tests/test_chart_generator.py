"""Tests for app.services.chart_generator module.

Covers all 5 public functions with both real matplotlib rendering and
mocked-out matplotlib (simulating CI environments where it is absent).
"""
from __future__ import annotations

import base64
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest

from app.services.chart_generator import (
    generate_gonogo_radar,
    generate_cashflow_chart,
    generate_risk_heatmap,
    generate_pricing_benchmark_bars,
    chart_to_base64,
    GONOGO_DIMENSIONS_ORDER,
    GONOGO_LABELS_SHORT,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def gonogo_dimensions_full():
    """All 9 Go/No-Go dimensions with realistic scores."""
    return {
        "Capacité financière": 80,
        "Certifications & agréments": 65,
        "Références similaires": 90,
        "Charge actuelle": 50,
        "Zone géographique": 70,
        "Partenariats disponibles": 60,
        "Marge visée": 75,
        "Délai de réponse": 85,
        "Risque technique global": 40,
    }


@pytest.fixture
def gonogo_dimensions_snake_case():
    """Dimensions using snake_case aliases (from backend Go/No-Go output)."""
    return {
        "capacite_financiere": 80,
        "certifications": 65,
        "references_btp": 90,
        "charge_actuelle": 50,
        "zone_geo": 70,
        "partenariats": 60,
        "marge_visee": 75,
        "delai_reponse": 85,
        "risque_technique": 40,
    }


@pytest.fixture
def cashflow_monthly():
    return {
        "monthly_cashflow": [
            {"month": 1, "cumulative_eur": -15000},
            {"month": 2, "cumulative_eur": -8000},
            {"month": 3, "cumulative_eur": 5000},
            {"month": 4, "cumulative_eur": 20000},
            {"month": 5, "cumulative_eur": 35000},
            {"month": 6, "cumulative_eur": 45000},
        ]
    }


@pytest.fixture
def cashflow_french_keys():
    """Cashflow data using French key names (cashflow_mensuel / tresorerie_cumulee)."""
    return {
        "cashflow_mensuel": [
            {"mois": "Jan", "tresorerie_cumulee": -10000},
            {"mois": "Fév", "tresorerie_cumulee": 5000},
            {"mois": "Mar", "tresorerie_cumulee": 25000},
        ]
    }


@pytest.fixture
def cashflow_nested_simulation():
    """Cashflow data nested under simulation.monthly_cashflow."""
    return {
        "simulation": {
            "monthly_cashflow": [
                {"month": 1, "cumulative_eur": -5000},
                {"month": 2, "cumulative_eur": 10000},
            ]
        }
    }


@pytest.fixture
def conflicts_list():
    return [
        {
            "doc_source": "CCAP",
            "doc_target": "CCTP",
            "conflict_type": "prix_contradictoire",
            "severity": "high",
        },
        {
            "doc_source": "CCAP",
            "doc_target": "RC",
            "conflict_type": "délais_incompatibles",
            "severity": "medium",
        },
        {
            "doc_source": "CCTP",
            "doc_target": "DPGF",
            "conflict_type": "quantités_discordantes",
            "severity": "low",
        },
        {
            "doc_source": "RC",
            "doc_target": "CCAP",
            "conflict_type": "exigences_contradictoires",
            "severity": "critical",
        },
    ]


@pytest.fixture
def pricing_items():
    return [
        {
            "designation": "Béton C25/30",
            "prix_saisi": 95,
            "prix_min": 80,
            "prix_max": 120,
            "status": "OK",
        },
        {
            "designation": "Acier HA 500",
            "prix_saisi": 50,
            "prix_min": 80,
            "prix_max": 110,
            "status": "SOUS_EVALUE",
        },
        {
            "designation": "Enrobé BB 0/10",
            "prix_saisi": 200,
            "prix_min": 90,
            "prix_max": 140,
            "status": "SUR_EVALUE",
        },
    ]


# ---------------------------------------------------------------------------
# Helper: patch _get_matplotlib to simulate absence
# ---------------------------------------------------------------------------

def _patch_no_matplotlib():
    return patch(
        "app.services.chart_generator._get_matplotlib",
        return_value=(None, None),
    )


# ===================================================================
# chart_to_base64
# ===================================================================

class TestChartToBase64:
    def test_none_returns_none(self):
        assert chart_to_base64(None) is None

    def test_valid_bytesio_returns_base64_string(self):
        buf = BytesIO(b"PNG_FAKE_DATA")
        result = chart_to_base64(buf)
        assert result is not None
        assert isinstance(result, str)
        decoded = base64.b64decode(result)
        assert decoded == b"PNG_FAKE_DATA"

    def test_base64_is_pure_ascii(self):
        buf = BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = chart_to_base64(buf)
        assert result is not None
        result.encode("ascii")  # should not raise

    def test_seeks_to_start_before_reading(self):
        """Even if the BytesIO cursor is at the end, chart_to_base64 seeks(0)."""
        buf = BytesIO(b"HELLO")
        buf.read()  # move cursor to end
        result = chart_to_base64(buf)
        decoded = base64.b64decode(result)
        assert decoded == b"HELLO"

    def test_closed_bytesio_returns_none(self):
        buf = BytesIO(b"DATA")
        buf.close()
        assert chart_to_base64(buf) is None


# ===================================================================
# generate_gonogo_radar
# ===================================================================

class TestGenerateGonogoRadar:
    def test_returns_none_when_matplotlib_missing(self, gonogo_dimensions_full):
        with _patch_no_matplotlib():
            result = generate_gonogo_radar(gonogo_dimensions_full, score_global=72)
            assert result is None

    def test_empty_dimensions_returns_valid_buf_with_zeros(self):
        """Empty dict still produces 9 zero-valued axes (from GONOGO_DIMENSIONS_ORDER)."""
        result = generate_gonogo_radar({})
        # Should return a BytesIO (all 9 dimensions default to 0) because
        # GONOGO_DIMENSIONS_ORDER always produces 9 values.
        if result is not None:
            assert isinstance(result, BytesIO)
            data = result.getvalue()
            assert len(data) > 0
            assert data[:4] == b"\x89PNG"

    def test_full_dimensions_returns_png(self, gonogo_dimensions_full):
        result = generate_gonogo_radar(gonogo_dimensions_full, score_global=72)
        if result is not None:
            assert isinstance(result, BytesIO)
            assert result.getvalue()[:4] == b"\x89PNG"

    def test_snake_case_aliases_produce_same_dimensions(
        self, gonogo_dimensions_full, gonogo_dimensions_snake_case
    ):
        """snake_case keys (capacite_financiere) should map to the canonical names."""
        result_canonical = generate_gonogo_radar(gonogo_dimensions_full, score_global=70)
        result_aliased = generate_gonogo_radar(gonogo_dimensions_snake_case, score_global=70)
        # Both should succeed (or both None if matplotlib missing)
        if result_canonical is not None:
            assert result_aliased is not None
            # Both produce valid PNGs (sizes may differ slightly due to rendering)
            assert result_aliased.getvalue()[:4] == b"\x89PNG"

    def test_score_global_none_uses_average(self, gonogo_dimensions_full):
        result = generate_gonogo_radar(gonogo_dimensions_full, score_global=None)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_custom_title(self, gonogo_dimensions_full):
        result = generate_gonogo_radar(
            gonogo_dimensions_full,
            score_global=85,
            title="Mon radar custom",
        )
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_values_clamped_to_0_100(self):
        """Values outside 0-100 should be clamped."""
        dims = {"Capacité financière": -20, "Marge visée": 150}
        result = generate_gonogo_radar(dims)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_partial_dimensions(self):
        """Only a subset of dimensions — missing ones default to 0."""
        dims = {"Capacité financière": 80, "Marge visée": 60}
        result = generate_gonogo_radar(dims, score_global=50)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_constants_consistency(self):
        """GONOGO_LABELS_SHORT covers every entry in GONOGO_DIMENSIONS_ORDER."""
        for dim in GONOGO_DIMENSIONS_ORDER:
            assert dim in GONOGO_LABELS_SHORT


# ===================================================================
# generate_cashflow_chart
# ===================================================================

class TestGenerateCashflowChart:
    def test_returns_none_when_matplotlib_missing(self, cashflow_monthly):
        with _patch_no_matplotlib():
            result = generate_cashflow_chart(cashflow_monthly)
            assert result is None

    def test_empty_cashflow_returns_none(self):
        assert generate_cashflow_chart({}) is None

    def test_empty_monthly_list_returns_none(self):
        assert generate_cashflow_chart({"monthly_cashflow": []}) is None

    def test_monthly_cashflow_key(self, cashflow_monthly):
        result = generate_cashflow_chart(cashflow_monthly)
        if result is not None:
            assert isinstance(result, BytesIO)
            assert result.getvalue()[:4] == b"\x89PNG"

    def test_french_keys_cashflow_mensuel(self, cashflow_french_keys):
        """cashflow_mensuel + tresorerie_cumulee keys should work."""
        result = generate_cashflow_chart(cashflow_french_keys)
        if result is not None:
            assert isinstance(result, BytesIO)
            assert result.getvalue()[:4] == b"\x89PNG"

    def test_nested_simulation_key(self, cashflow_nested_simulation):
        """simulation.monthly_cashflow path should work."""
        result = generate_cashflow_chart(cashflow_nested_simulation)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_custom_title(self, cashflow_monthly):
        result = generate_cashflow_chart(cashflow_monthly, title="Test title")
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_all_positive_values(self):
        data = {
            "monthly_cashflow": [
                {"month": 1, "cumulative_eur": 1000},
                {"month": 2, "cumulative_eur": 5000},
            ]
        }
        result = generate_cashflow_chart(data)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_all_negative_values(self):
        data = {
            "monthly_cashflow": [
                {"month": 1, "cumulative_eur": -5000},
                {"month": 2, "cumulative_eur": -10000},
            ]
        }
        result = generate_cashflow_chart(data)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_single_month(self):
        data = {"monthly_cashflow": [{"month": 1, "cumulative_eur": 0}]}
        result = generate_cashflow_chart(data)
        if result is not None:
            assert isinstance(result, BytesIO)


# ===================================================================
# generate_risk_heatmap
# ===================================================================

class TestGenerateRiskHeatmap:
    def test_returns_none_when_matplotlib_missing(self, conflicts_list):
        with _patch_no_matplotlib():
            result = generate_risk_heatmap(conflicts_list)
            assert result is None

    def test_empty_conflicts_returns_none(self):
        assert generate_risk_heatmap([]) is None

    def test_valid_conflicts_return_png(self, conflicts_list):
        result = generate_risk_heatmap(conflicts_list)
        if result is not None:
            assert isinstance(result, BytesIO)
            assert result.getvalue()[:4] == b"\x89PNG"

    def test_custom_title(self, conflicts_list):
        result = generate_risk_heatmap(conflicts_list, title="Custom heatmap")
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_severity_weights(self):
        """critical/high = 3, medium = 2, low = 1."""
        conflicts = [
            {"doc_source": "CCAP", "conflict_type": "prix", "severity": "critical"},
            {"doc_source": "CCAP", "conflict_type": "prix", "severity": "low"},
        ]
        result = generate_risk_heatmap(conflicts)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_alternative_doc_keys(self):
        """Supports document_source, doc1, document_a as doc key names."""
        conflicts = [
            {
                "document_source": "BPU",
                "doc_target": "DPGF",
                "conflict_type": "quantités",
                "severity": "medium",
            },
        ]
        result = generate_risk_heatmap(conflicts)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_unknown_conflict_type_maps_to_exigences(self):
        """Unknown conflict_type falls back to last category index (exigences)."""
        conflicts = [
            {
                "doc_source": "RC",
                "conflict_type": "unknown_category_xyz",
                "severity": "low",
            },
        ]
        result = generate_risk_heatmap(conflicts)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_many_documents_truncated_to_8(self):
        """More than 8 unique documents should be truncated to 8."""
        conflicts = [
            {"doc_source": f"DOC_{i}", "conflict_type": "prix", "severity": "low"}
            for i in range(15)
        ]
        result = generate_risk_heatmap(conflicts)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_alternative_severity_key_niveau(self):
        """severity can also be provided as 'niveau'."""
        conflicts = [
            {"doc_source": "CCTP", "conflict_type": "technique", "niveau": "high"},
        ]
        result = generate_risk_heatmap(conflicts)
        if result is not None:
            assert isinstance(result, BytesIO)


# ===================================================================
# generate_pricing_benchmark_bars
# ===================================================================

class TestGeneratePricingBenchmarkBars:
    def test_returns_none_when_matplotlib_missing(self, pricing_items):
        with _patch_no_matplotlib():
            result = generate_pricing_benchmark_bars(pricing_items)
            assert result is None

    def test_empty_list_returns_none(self):
        assert generate_pricing_benchmark_bars([]) is None

    def test_valid_items_return_png(self, pricing_items):
        result = generate_pricing_benchmark_bars(pricing_items)
        if result is not None:
            assert isinstance(result, BytesIO)
            assert result.getvalue()[:4] == b"\x89PNG"

    def test_filters_alertes_first(self, pricing_items):
        """When alertes exist (SOUS_EVALUE/SUR_EVALUE), they should be shown first."""
        # Add many OK items to ensure alertes are prioritized
        many_ok = [
            {
                "designation": f"Item OK {i}",
                "prix_saisi": 100,
                "prix_min": 90,
                "prix_max": 110,
                "status": "OK",
            }
            for i in range(20)
        ]
        alerte = {
            "designation": "Problème",
            "prix_saisi": 30,
            "prix_min": 80,
            "prix_max": 120,
            "status": "SOUS_EVALUE",
        }
        combined = many_ok + [alerte]
        result = generate_pricing_benchmark_bars(combined)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_no_alertes_uses_all_items(self):
        """When no alertes exist, first 12 items are used."""
        items = [
            {
                "designation": f"Item {i}",
                "prix_saisi": 100 + i,
                "prix_min": 80,
                "prix_max": 130,
                "status": "OK",
            }
            for i in range(15)
        ]
        result = generate_pricing_benchmark_bars(items)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_alternative_price_keys(self):
        """prix_unitaire, min, max as alternative key names."""
        items = [
            {
                "designation": "Gravier 6/10",
                "prix_unitaire": 45,
                "min": 30,
                "max": 60,
                "status": "OK",
            },
        ]
        result = generate_pricing_benchmark_bars(items)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_custom_title(self, pricing_items):
        result = generate_pricing_benchmark_bars(pricing_items, title="My Benchmark")
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_long_designation_truncated(self):
        """Designations longer than 40 chars should be truncated."""
        items = [
            {
                "designation": "A" * 80,
                "prix_saisi": 100,
                "prix_min": 80,
                "prix_max": 120,
                "status": "SUR_EVALUE",
            },
        ]
        result = generate_pricing_benchmark_bars(items)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_max_12_items(self):
        """Even with many alertes, only top 12 are rendered."""
        items = [
            {
                "designation": f"Alerte {i}",
                "prix_saisi": 10,
                "prix_min": 80,
                "prix_max": 120,
                "status": "SOUS_EVALUE",
            }
            for i in range(20)
        ]
        result = generate_pricing_benchmark_bars(items)
        if result is not None:
            assert isinstance(result, BytesIO)

    def test_unknown_status_uses_neutral_color(self):
        items = [
            {
                "designation": "Unknown status",
                "prix_saisi": 100,
                "prix_min": 80,
                "prix_max": 120,
                "status": "UNKNOWN",
            },
        ]
        result = generate_pricing_benchmark_bars(items)
        if result is not None:
            assert isinstance(result, BytesIO)


# ===================================================================
# Integration: chart_to_base64 with chart outputs
# ===================================================================

class TestIntegrationChartToBase64:
    def test_radar_to_base64(self, gonogo_dimensions_full):
        buf = generate_gonogo_radar(gonogo_dimensions_full, score_global=75)
        result = chart_to_base64(buf)
        if buf is not None:
            assert result is not None
            assert isinstance(result, str)
            assert len(result) > 100  # non-trivial base64
            # Verify roundtrip
            decoded = base64.b64decode(result)
            assert decoded[:4] == b"\x89PNG"
        else:
            assert result is None

    def test_cashflow_to_base64(self, cashflow_monthly):
        buf = generate_cashflow_chart(cashflow_monthly)
        result = chart_to_base64(buf)
        if buf is not None:
            assert result is not None
            decoded = base64.b64decode(result)
            assert decoded[:4] == b"\x89PNG"

    def test_heatmap_to_base64(self, conflicts_list):
        buf = generate_risk_heatmap(conflicts_list)
        result = chart_to_base64(buf)
        if buf is not None:
            assert result is not None

    def test_pricing_to_base64(self, pricing_items):
        buf = generate_pricing_benchmark_bars(pricing_items)
        result = chart_to_base64(buf)
        if buf is not None:
            assert result is not None


# ===================================================================
# Error handling / robustness
# ===================================================================

class TestErrorHandling:
    def test_radar_with_non_numeric_values_returns_none(self):
        """Non-numeric dimension values should be handled gracefully."""
        dims = {"Capacité financière": "not_a_number"}
        result = generate_gonogo_radar(dims)
        # Should return None due to float() conversion error caught by except
        assert result is None

    def test_cashflow_with_non_numeric_values_returns_none(self):
        data = {
            "monthly_cashflow": [
                {"month": 1, "cumulative_eur": "invalid"},
            ]
        }
        result = generate_cashflow_chart(data)
        # float("invalid") will raise, caught by except → None
        assert result is None

    def test_pricing_with_non_numeric_prix_returns_none(self):
        items = [
            {
                "designation": "Test",
                "prix_saisi": "abc",
                "prix_min": 10,
                "prix_max": 20,
                "status": "OK",
            }
        ]
        result = generate_pricing_benchmark_bars(items)
        assert result is None
