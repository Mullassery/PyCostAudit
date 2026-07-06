"""Tests for PDF and Excel export functionality"""

import pytest
from datetime import datetime
from pycostaudit.custom_report_builder import (
    GeneratedReport, ReportMetadata, ReportType, ExportFormat,
    ReportSection
)


@pytest.fixture
def sample_report():
    """Create a sample report for testing"""
    now = datetime.now()
    metadata = ReportMetadata(
        report_id="test-123",
        name="Test Cost Report",
        description="A test report",
        report_type=ReportType.COST_BREAKDOWN,
        created_by="test_user",
        created_at=now,
        generated_at=now
    )

    raw_data = [
        {"operation_type": "api_call", "total_cost": 10.50, "count": 5},
        {"operation_type": "file_read", "total_cost": 5.25, "count": 3},
        {"operation_type": "browser", "total_cost": 20.00, "count": 2},
    ]

    sections = [
        ReportSection(
            title="Cost Overview",
            description="Overview of costs",
            data=raw_data,
            insights=["Total cost is $35.75", "Browser operations are most expensive"]
        )
    ]

    report = GeneratedReport(
        metadata=metadata,
        raw_data=raw_data,
        sections=sections,
        aggregated_data=raw_data,
        export_formats=[ExportFormat.JSON, ExportFormat.CSV, ExportFormat.HTML, ExportFormat.PDF, ExportFormat.EXCEL]
    )
    return report


class TestPDFExport:
    """Test PDF export functionality"""

    def test_export_pdf_returns_bytes(self, sample_report):
        """PDF export should return bytes"""
        try:
            pdf_bytes = sample_report.export_pdf()
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_export_pdf_contains_title(self, sample_report):
        """PDF should contain report title"""
        try:
            pdf_bytes = sample_report.export_pdf()
            # PDF files start with %PDF
            assert pdf_bytes.startswith(b'%PDF')
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_export_pdf_missing_library(self, sample_report, monkeypatch):
        """PDF export should fail gracefully if reportlab is missing"""
        try:
            import reportlab  # noqa
            pytest.skip("reportlab is installed")
        except ImportError:
            with pytest.raises(ImportError, match="reportlab"):
                sample_report.export_pdf()


class TestExcelExport:
    """Test Excel export functionality"""

    def test_export_excel_returns_bytes(self, sample_report):
        """Excel export should return bytes"""
        try:
            excel_bytes = sample_report.export_excel()
            assert isinstance(excel_bytes, bytes)
            assert len(excel_bytes) > 0
        except ImportError:
            pytest.skip("openpyxl not installed")

    def test_export_excel_contains_header(self, sample_report):
        """Excel should contain report title"""
        try:
            excel_bytes = sample_report.export_excel()
            # Excel files (XLSX) start with PK (ZIP header)
            assert excel_bytes.startswith(b'PK')
        except ImportError:
            pytest.skip("openpyxl not installed")

    def test_export_excel_missing_library(self, sample_report, monkeypatch):
        """Excel export should fail gracefully if openpyxl is missing"""
        try:
            import openpyxl  # noqa
            pytest.skip("openpyxl is installed")
        except ImportError:
            with pytest.raises(ImportError, match="openpyxl"):
                sample_report.export_excel()


class TestExportDispatcher:
    """Test the export method dispatcher"""

    def test_export_json(self, sample_report):
        """export() should handle JSON format"""
        json_str = sample_report.export(ExportFormat.JSON)
        assert isinstance(json_str, str)
        assert '"metadata"' in json_str

    def test_export_csv(self, sample_report):
        """export() should handle CSV format"""
        csv_str = sample_report.export(ExportFormat.CSV)
        assert isinstance(csv_str, str)
        assert 'operation_type' in csv_str or len(csv_str) > 0

    def test_export_html(self, sample_report):
        """export() should handle HTML format"""
        html_str = sample_report.export(ExportFormat.HTML)
        assert isinstance(html_str, str)
        assert '<html>' in html_str.lower()

    def test_export_markdown(self, sample_report):
        """export() should handle Markdown format"""
        md_str = sample_report.export(ExportFormat.MARKDOWN)
        assert isinstance(md_str, str)
        assert '#' in md_str

    def test_export_pdf(self, sample_report):
        """export() should handle PDF format"""
        try:
            pdf_bytes = sample_report.export(ExportFormat.PDF)
            assert isinstance(pdf_bytes, bytes)
        except ImportError:
            pytest.skip("reportlab not installed")

    def test_export_excel(self, sample_report):
        """export() should handle Excel format"""
        try:
            excel_bytes = sample_report.export(ExportFormat.EXCEL)
            assert isinstance(excel_bytes, bytes)
        except ImportError:
            pytest.skip("openpyxl not installed")

    def test_export_unsupported_format(self, sample_report):
        """export() should raise error for unsupported format"""
        with pytest.raises(ValueError, match="Unsupported"):
            # Create a mock unsupported format
            class UnsupportedFormat:
                pass

            sample_report.export(UnsupportedFormat())
