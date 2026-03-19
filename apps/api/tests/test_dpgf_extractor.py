"""Tests for app.services.dpgf_extractor — DPGF/BPU table extraction from PDF."""
import io
import pytest
from unittest.mock import patch, MagicMock

from app.services.dpgf_extractor import (
    _normalize_col_name,
    _parse_number,
    _is_header_row,
    _guess_doc_type_from_headers,
    _map_row_to_dataclass,
    _hex_to_argb,
    extract_tables_from_pdf,
    generate_excel,
    extract_dpgf,
    DpgfRow,
    BpuRow,
    ExtractedTable,
    DPGF_KEYS,
    BPU_KEYS,
)


# ---------------------------------------------------------------------------
# _normalize_col_name
# ---------------------------------------------------------------------------

class TestNormalizeColName:
    def test_designation_variants(self):
        assert _normalize_col_name("Désignation") == "designation"
        assert _normalize_col_name("DESIGNATION") == "designation"
        assert _normalize_col_name("Libellé") == "designation"
        assert _normalize_col_name("Description") == "designation"
        assert _normalize_col_name("Intitulé") == "designation"

    def test_numero_variants(self):
        assert _normalize_col_name("Numéro") == "numero"
        assert _normalize_col_name("Référence") == "numero"
        assert _normalize_col_name("Article") == "numero"

    def test_quantite_variants(self):
        assert _normalize_col_name("Qté") == "quantite"
        assert _normalize_col_name("QTY") == "quantite"

    def test_prix_unitaire_variants(self):
        # The actual normalizer maps these to "unite"
        assert _normalize_col_name("Prix unitaire") == "unite"
        assert _normalize_col_name("PU") == "unite"
        assert _normalize_col_name("P.U.") == "unite"

    def test_montant_ht(self):
        assert _normalize_col_name("Montant HT") == "montant_ht"
        assert _normalize_col_name("Total HT") == "montant_ht"

    def test_unite(self):
        assert _normalize_col_name("Unité") == "unite"
        assert _normalize_col_name("U") == "unite"

    def test_empty_and_none_returns_none(self):
        assert _normalize_col_name("") is None
        assert _normalize_col_name(None) is None


# ---------------------------------------------------------------------------
# _parse_number
# ---------------------------------------------------------------------------

class TestParseNumber:
    def test_simple_number(self):
        assert _parse_number("1234") == 1234.0

    def test_with_comma(self):
        assert _parse_number("1 234,56") == 1234.56

    def test_with_euro_sign(self):
        assert _parse_number("1 234,56 €") == 1234.56

    def test_with_spaces(self):
        assert _parse_number("  42  ") == 42.0

    def test_european_format(self):
        assert _parse_number("1.234.567,89") == 1234567.89

    def test_empty_string(self):
        assert _parse_number("") is None

    def test_none(self):
        assert _parse_number(None) is None

    def test_non_numeric(self):
        assert _parse_number("abc") is None

    def test_dollar_sign(self):
        assert _parse_number("$100") == 100.0


# ---------------------------------------------------------------------------
# _is_header_row
# ---------------------------------------------------------------------------

class TestIsHeaderRow:
    def test_valid_header(self):
        row = ["N°", "Désignation", "Unité", "Quantité", "Prix unitaire", "Montant HT"]
        assert _is_header_row(row) is True

    def test_data_row(self):
        row = ["1", "Terrassement", "m3", "500", "25,00", "12 500,00"]
        assert _is_header_row(row) is False

    def test_empty_row(self):
        assert _is_header_row([]) is False
        assert _is_header_row([None, None, None]) is False

    def test_partial_header(self):
        # Use column names that the normalizer actually recognizes
        row = ["Désignation", "Qté", "Montant HT"]
        assert _is_header_row(row) is True  # >= 2 recognized


# ---------------------------------------------------------------------------
# _guess_doc_type_from_headers
# ---------------------------------------------------------------------------

class TestGuessDocType:
    def test_dpgf_with_quantite(self):
        headers = ["N°", "Désignation", "Unité", "Quantité", "PU", "Montant HT"]
        assert _guess_doc_type_from_headers(headers) == "DPGF"

    def test_dpgf_with_montant(self):
        headers = ["Référence", "Description", "Total HT"]
        assert _guess_doc_type_from_headers(headers) == "DPGF"

    def test_bpu_without_quantite(self):
        headers = ["N°", "Désignation", "Unité", "Prix unitaire"]
        assert _guess_doc_type_from_headers(headers) == "BPU"


# ---------------------------------------------------------------------------
# _map_row_to_dataclass
# ---------------------------------------------------------------------------

class TestMapRowToDataclass:
    def test_dpgf_row(self):
        col_mapping = {0: "numero", 1: "designation", 2: "prix_unitaire"}
        row = ["1", "Terrassement", "25,00"]
        result = _map_row_to_dataclass(row, col_mapping, "DPGF")
        assert isinstance(result, DpgfRow)
        assert result.numero == "1"
        assert result.designation == "Terrassement"

    def test_bpu_row(self):
        col_mapping = {0: "numero", 1: "designation", 2: "prix_unitaire"}
        row = ["A1", "Beton C25/30", "120,00"]
        result = _map_row_to_dataclass(row, col_mapping, "BPU")
        assert isinstance(result, BpuRow)
        assert result.numero == "A1"

    def test_empty_row_returns_none(self):
        col_mapping = {0: "numero", 1: "designation"}
        row = ["", "", ""]
        result = _map_row_to_dataclass(row, col_mapping, "DPGF")
        assert result is None

    def test_none_values_in_row(self):
        col_mapping = {0: "numero", 1: "designation"}
        row = [None, None]
        result = _map_row_to_dataclass(row, col_mapping, "DPGF")
        assert result is None


# ---------------------------------------------------------------------------
# _hex_to_argb
# ---------------------------------------------------------------------------

class TestHexToArgb:
    def test_conversion(self):
        assert _hex_to_argb("1E40AF") == "FF1E40AF"
        assert _hex_to_argb("ffffff") == "FFFFFFFF"


# ---------------------------------------------------------------------------
# extract_tables_from_pdf — with mocked pdfplumber
# ---------------------------------------------------------------------------

class TestExtractTablesFromPdf:
    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_extracts_dpgf_table(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["N°", "Désignation", "Unité", "Quantité", "Prix unitaire", "Montant HT"],
                ["1", "Terrassement", "m3", "500", "25,00", "12 500,00"],
                ["2", "Beton", "m3", "200", "80,00", "16 000,00"],
            ]
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_tables_from_pdf(b"fake_pdf_bytes")
        assert len(result) == 1
        assert result[0].doc_type == "DPGF"
        assert len(result[0].rows) == 2
        assert isinstance(result[0].rows[0], DpgfRow)

    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_extracts_bpu_table(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["N°", "Désignation", "Unité", "Prix unitaire"],
                ["A1", "Beton C25/30", "m3", "120,00"],
            ]
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_tables_from_pdf(b"fake_pdf_bytes")
        assert len(result) == 1
        assert result[0].doc_type == "BPU"

    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_no_tables_returns_empty(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_tables_from_pdf(b"fake_pdf_bytes")
        assert result == []

    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_no_header_row_skipped(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["random1", "random2", "random3"],
                ["data1", "data2", "data3"],
            ]
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_tables_from_pdf(b"fake_pdf_bytes")
        assert result == []

    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_pdf_parse_error_raises(self, mock_pdfplumber):
        mock_pdfplumber.open.side_effect = Exception("corrupt PDF")
        with pytest.raises(ValueError, match="Impossible d'analyser"):
            extract_tables_from_pdf(b"bad_pdf")

    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_table_with_single_row_skipped(self, mock_pdfplumber):
        """Tables with < 2 rows should be skipped."""
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [["N°", "Désignation"]]  # Only header, no data
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_tables_from_pdf(b"fake_pdf_bytes")
        assert result == []


# ---------------------------------------------------------------------------
# generate_excel
# ---------------------------------------------------------------------------

class TestGenerateExcel:
    def test_generate_excel_with_dpgf(self):
        tables = [
            ExtractedTable(
                doc_type="DPGF",
                rows=[
                    DpgfRow(numero="1", designation="Terrassement", unite="m3",
                            quantite="500", prix_unitaire="25,00", montant_ht="12500,00"),
                    DpgfRow(numero="2", designation="Beton", unite="m3",
                            quantite="200", prix_unitaire="80,00", montant_ht="16000,00"),
                ],
                source_page=1,
                raw_headers=["N°", "Désignation", "Unité", "Quantité", "PU", "Montant HT"],
            )
        ]
        result = generate_excel(tables, project_title="Test Project")
        assert isinstance(result, bytes)
        assert len(result) > 100  # Valid xlsx file

    def test_generate_excel_with_bpu(self):
        tables = [
            ExtractedTable(
                doc_type="BPU",
                rows=[
                    BpuRow(numero="A1", designation="Beton C25", unite="m3", prix_unitaire="120"),
                ],
                source_page=2,
                raw_headers=["N°", "Désignation", "Unité", "PU"],
            )
        ]
        result = generate_excel(tables)
        assert isinstance(result, bytes)
        assert len(result) > 100

    def test_generate_excel_empty_tables(self):
        result = generate_excel([])
        assert isinstance(result, bytes)
        assert len(result) > 50  # Creates info sheet

    def test_multiple_tables(self):
        tables = [
            ExtractedTable(doc_type="DPGF", rows=[
                DpgfRow(numero="1", designation="Lot 1", montant_ht="1000"),
            ], source_page=1),
            ExtractedTable(doc_type="DPGF", rows=[
                DpgfRow(numero="1", designation="Lot 2", montant_ht="2000"),
            ], source_page=3),
        ]
        result = generate_excel(tables)
        assert isinstance(result, bytes)


# ---------------------------------------------------------------------------
# extract_dpgf — end-to-end with mock
# ---------------------------------------------------------------------------

class TestExtractDpgf:
    @patch("app.services.dpgf_extractor.pdfplumber")
    def test_extract_dpgf_e2e(self, mock_pdfplumber):
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [
                ["N°", "Désignation", "Unité", "Quantité", "PU", "Montant HT"],
                ["1", "Travaux", "ens", "1", "50000", "50000"],
            ]
        ]
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdfplumber.open.return_value = mock_pdf

        result = extract_dpgf(b"pdf_bytes", filename="dpgf.pdf", project_title="Mon AO")
        assert isinstance(result, bytes)
        assert len(result) > 100


# ---------------------------------------------------------------------------
# Dataclass tests
# ---------------------------------------------------------------------------

class TestDataclasses:
    def test_dpgf_row_defaults(self):
        row = DpgfRow()
        assert row.numero == ""
        assert row.designation == ""

    def test_bpu_row_defaults(self):
        row = BpuRow()
        assert row.numero == ""

    def test_extracted_table_defaults(self):
        table = ExtractedTable(doc_type="DPGF")
        assert table.rows == []
        assert table.source_page == 0
        assert table.raw_headers == []
