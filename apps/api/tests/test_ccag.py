"""Tests pour les modules CCAG — Travaux, FCS, PI, TIC (2021)."""
import pytest

from app.services.ccag_travaux_2021 import (
    CCAG_ARTICLES,
    COMMON_DEROGATIONS,
    CcagArticle,
    CcagDerogation,
    get_ccag_context_for_analyzer,
    get_ccag_article,
    get_ccag_articles_by_category,
    get_common_derogations,
)
from app.services.ccag_fcs_2021 import (
    CCAG_FCS_ARTICLES,
    get_ccag_fcs_context,
)
from app.services.ccag_pi_2021 import (
    CCAG_PI_ARTICLES,
    get_ccag_pi_context,
)
from app.services.ccag_tic_2021 import (
    CCAG_TIC_ARTICLES,
    get_ccag_tic_context,
)


# ══════════════════════════════════════════════════════════════════════════════
# CCAG-Travaux 2021
# ══════════════════════════════════════════════════════════════════════════════

class TestCcagTravaux:
    """Tests for CCAG-Travaux 2021 module."""

    def test_articles_populated(self):
        assert len(CCAG_ARTICLES) >= 20

    def test_all_entries_are_ccag_article(self):
        for article in CCAG_ARTICLES:
            assert isinstance(article, CcagArticle)

    def test_article_required_fields(self):
        for article in CCAG_ARTICLES:
            assert article.article, f"Missing article number"
            assert article.title, f"Missing title for {article.article}"
            assert article.standard_value, f"Missing standard_value for {article.article}"
            assert article.category, f"Missing category for {article.article}"
            assert article.legal_source, f"Missing legal_source for {article.article}"

    def test_articles_are_frozen(self):
        article = CCAG_ARTICLES[0]
        with pytest.raises(AttributeError):
            article.title = "modified"

    def test_key_articles_present(self):
        """Verify critical articles are in the database."""
        article_nums = {a.article for a in CCAG_ARTICLES}
        assert "14.1" in article_nums  # Avance forfaitaire
        assert "19.1" in article_nums  # Pénalités de retard
        assert "14.3" in article_nums  # Retenue de garantie
        assert "11.6" in article_nums  # Délai de paiement


class TestGetCcagArticle:

    def test_existing_article(self):
        article = get_ccag_article("14.1")
        assert article is not None
        assert article.article == "14.1"
        assert "Avance" in article.title

    def test_nonexistent_article(self):
        assert get_ccag_article("99.99") is None

    def test_penalites_article(self):
        article = get_ccag_article("19.1")
        assert article is not None
        assert article.category == "penalites"


class TestGetCcagArticlesByCategory:

    def test_penalites_category(self):
        articles = get_ccag_articles_by_category("penalites")
        assert len(articles) >= 1
        for a in articles:
            assert a.category == "penalites"

    def test_paiement_category(self):
        articles = get_ccag_articles_by_category("paiement")
        assert len(articles) >= 3

    def test_unknown_category_empty(self):
        articles = get_ccag_articles_by_category("nonexistent")
        assert articles == []


class TestGetCcagContext:

    def test_ccap_context(self):
        ctx = get_ccag_context_for_analyzer("ccap")
        assert isinstance(ctx, str)
        assert len(ctx) > 200
        assert "CCAG-Travaux 2021" in ctx
        assert "DÉFAVORABLE" in ctx or "dérogation" in ctx.lower()

    def test_ae_context(self):
        ctx = get_ccag_context_for_analyzer("ae")
        assert isinstance(ctx, str)
        assert len(ctx) > 100

    def test_conflict_context(self):
        ctx = get_ccag_context_for_analyzer("conflict")
        assert isinstance(ctx, str)
        assert len(ctx) > 100

    def test_cctp_context(self):
        ctx = get_ccag_context_for_analyzer("cctp")
        assert isinstance(ctx, str)
        assert len(ctx) > 50

    def test_unknown_type_defaults_to_ccap(self):
        ctx = get_ccag_context_for_analyzer("unknown")
        assert isinstance(ctx, str)
        assert len(ctx) > 100

    def test_context_contains_table_headers(self):
        ctx = get_ccag_context_for_analyzer("ccap")
        assert "Article" in ctx
        assert "Standard" in ctx


class TestCommonDerogations:

    def test_derogations_populated(self):
        assert len(COMMON_DEROGATIONS) >= 10

    def test_all_entries_are_ccag_derogation(self):
        for d in COMMON_DEROGATIONS:
            assert isinstance(d, CcagDerogation)

    def test_derogation_required_fields(self):
        for d in COMMON_DEROGATIONS:
            assert d.article_ccag
            assert d.theme
            assert d.derogation_courante
            assert d.evaluation
            assert d.risque in {"elevé", "modéré", "faible"}

    def test_get_common_derogations_returns_dicts(self):
        results = get_common_derogations()
        assert isinstance(results, list)
        assert len(results) == len(COMMON_DEROGATIONS)
        for r in results:
            assert isinstance(r, dict)
            assert "article_ccag" in r
            assert "theme" in r
            assert "risque" in r


# ══════════════════════════════════════════════════════════════════════════════
# CCAG-FCS 2021
# ══════════════════════════════════════════════════════════════════════════════

class TestCcagFCS:
    """Tests for CCAG-FCS 2021 module."""

    def test_articles_populated(self):
        assert len(CCAG_FCS_ARTICLES) >= 10

    def test_all_are_ccag_article(self):
        for article in CCAG_FCS_ARTICLES:
            assert isinstance(article, CcagArticle)

    def test_has_fcs_specific_articles(self):
        titles = {a.title for a in CCAG_FCS_ARTICLES}
        assert any("FCS" in t for t in titles)

    def test_context_function(self):
        ctx = get_ccag_fcs_context()
        assert isinstance(ctx, str)
        assert "Fournitures Courantes" in ctx
        assert len(ctx) > 100

    def test_articles_have_legal_source(self):
        for a in CCAG_FCS_ARTICLES:
            assert "CCAG-FCS" in a.legal_source or "CCP" in a.legal_source


# ══════════════════════════════════════════════════════════════════════════════
# CCAG-PI 2021
# ══════════════════════════════════════════════════════════════════════════════

class TestCcagPI:
    """Tests for CCAG-PI 2021 module."""

    def test_articles_populated(self):
        assert len(CCAG_PI_ARTICLES) >= 10

    def test_all_are_ccag_article(self):
        for article in CCAG_PI_ARTICLES:
            assert isinstance(article, CcagArticle)

    def test_has_pi_specific_articles(self):
        titles = {a.title for a in CCAG_PI_ARTICLES}
        assert any("PI" in t for t in titles)

    def test_has_propriete_intellectuelle(self):
        categories = {a.category for a in CCAG_PI_ARTICLES}
        assert "propriete_intellectuelle" in categories

    def test_context_function(self):
        ctx = get_ccag_pi_context()
        assert isinstance(ctx, str)
        assert "Prestations Intellectuelles" in ctx
        assert len(ctx) > 100


# ══════════════════════════════════════════════════════════════════════════════
# CCAG-TIC 2021
# ══════════════════════════════════════════════════════════════════════════════

class TestCcagTIC:
    """Tests for CCAG-TIC 2021 module."""

    def test_articles_populated(self):
        assert len(CCAG_TIC_ARTICLES) >= 10

    def test_all_are_ccag_article(self):
        for article in CCAG_TIC_ARTICLES:
            assert isinstance(article, CcagArticle)

    def test_has_tic_specific_articles(self):
        titles = {a.title for a in CCAG_TIC_ARTICLES}
        assert any("TIC" in t for t in titles)

    def test_has_securite_category(self):
        categories = {a.category for a in CCAG_TIC_ARTICLES}
        assert "securite" in categories

    def test_has_reversibilite(self):
        categories = {a.category for a in CCAG_TIC_ARTICLES}
        assert "reversibilite" in categories

    def test_context_function(self):
        ctx = get_ccag_tic_context()
        assert isinstance(ctx, str)
        assert "Technologies" in ctx or "TIC" in ctx
        assert len(ctx) > 100


# ══════════════════════════════════════════════════════════════════════════════
# Cross-module consistency
# ══════════════════════════════════════════════════════════════════════════════

class TestCrossModuleConsistency:
    """Verify consistency across all CCAG modules."""

    def test_all_modules_share_ccag_article_type(self):
        """All modules use the same CcagArticle dataclass."""
        for a in CCAG_FCS_ARTICLES:
            assert type(a).__name__ == "CcagArticle"
        for a in CCAG_PI_ARTICLES:
            assert type(a).__name__ == "CcagArticle"
        for a in CCAG_TIC_ARTICLES:
            assert type(a).__name__ == "CcagArticle"

    def test_all_have_paiement_category(self):
        """All CCAG modules should have payment-related articles."""
        for articles, name in [
            (CCAG_ARTICLES, "Travaux"),
            (CCAG_FCS_ARTICLES, "FCS"),
            (CCAG_PI_ARTICLES, "PI"),
            (CCAG_TIC_ARTICLES, "TIC"),
        ]:
            categories = {a.category for a in articles}
            assert "paiement" in categories, f"{name} missing paiement category"

    def test_all_have_penalites(self):
        """All CCAG modules should have penalties articles."""
        for articles, name in [
            (CCAG_ARTICLES, "Travaux"),
            (CCAG_FCS_ARTICLES, "FCS"),
            (CCAG_PI_ARTICLES, "PI"),
            (CCAG_TIC_ARTICLES, "TIC"),
        ]:
            categories = {a.category for a in articles}
            assert "penalites" in categories, f"{name} missing penalites category"
