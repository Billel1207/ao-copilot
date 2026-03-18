"""Tests for cashflow simulator — deterministic BFR calculation."""
import pytest
from app.services.cashflow_simulator import simulate_cashflow


class TestSimulateCashflow:
    """Tests for the cashflow simulator."""

    def test_basic_linear(self):
        """Linear 12-month project should produce valid cashflow."""
        result = simulate_cashflow(
            montant_total_ht=1_000_000,
            duree_mois=12,
            avance_pct=5.0,
            retenue_pct=5.0,
            delai_paiement_jours=30,
            marge_brute_pct=15.0,
            repartition="lineaire",
        )

        assert "monthly_cashflow" in result
        assert len(result["monthly_cashflow"]) == 12
        assert "bfr_eur" in result
        assert "peak_negative_cash" in result
        assert "risk_level" in result
        assert result["risk_level"] in ("FAIBLE", "MODÉRÉ", "ÉLEVÉ", "CRITIQUE")

    def test_avance_reduces_bfr(self):
        """Higher advance should reduce BFR (less cash needed upfront)."""
        result_no_avance = simulate_cashflow(
            montant_total_ht=500_000,
            duree_mois=6,
            avance_pct=0.0,
            retenue_pct=5.0,
        )
        result_with_avance = simulate_cashflow(
            montant_total_ht=500_000,
            duree_mois=6,
            avance_pct=10.0,
            retenue_pct=5.0,
        )
        # With advance, the cash crunch should be less severe
        assert result_with_avance["peak_negative_cash"] >= result_no_avance["peak_negative_cash"]

    def test_short_project(self):
        """1-month project should work without errors."""
        result = simulate_cashflow(
            montant_total_ht=50_000,
            duree_mois=1,
        )
        assert len(result["monthly_cashflow"]) == 1

    def test_long_project(self):
        """36-month project should produce valid results."""
        result = simulate_cashflow(
            montant_total_ht=5_000_000,
            duree_mois=36,
            repartition="front_loaded",
        )
        assert len(result["monthly_cashflow"]) == 36

    def test_front_loaded_profile(self):
        """Front-loaded profile should have higher early months."""
        result = simulate_cashflow(
            montant_total_ht=1_000_000,
            duree_mois=12,
            repartition="front_loaded",
        )
        cf = result["monthly_cashflow"]
        # First month should have more work than last month
        assert cf[0]["travaux_realises_ht"] >= cf[-1]["travaux_realises_ht"]

    def test_back_loaded_profile(self):
        """Back-loaded profile should have higher later months."""
        result = simulate_cashflow(
            montant_total_ht=1_000_000,
            duree_mois=12,
            repartition="back_loaded",
        )
        cf = result["monthly_cashflow"]
        assert cf[-1]["travaux_realises_ht"] >= cf[0]["travaux_realises_ht"]

    def test_zero_margin(self):
        """Zero margin project should still compute without errors."""
        result = simulate_cashflow(
            montant_total_ht=200_000,
            duree_mois=6,
            marge_brute_pct=0.0,
        )
        assert result is not None

    def test_cumulative_balance(self):
        """Cumulative balance should be consistent month over month."""
        result = simulate_cashflow(
            montant_total_ht=1_000_000,
            duree_mois=12,
        )
        cf = result["monthly_cashflow"]
        running = 0.0
        for m in cf:
            running += m["solde_mensuel"]
            assert abs(m["solde_cumule"] - running) < 1.0  # Allow float rounding
