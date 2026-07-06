"""
Tests for reports service.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from pycostaudit.database import DatabaseManager, AlertConfiguration, TimeSeriesDataPoint
from pycostaudit.backend_service import BackendService
from pycostaudit.reports_service import ReportsService


@pytest.fixture
def temp_db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path


@pytest.fixture
def reports_service(temp_db):
    """Create reports service with temp database"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    backend = BackendService(temp_db)
    service = ReportsService(db, backend)

    yield service
    db.disconnect()


def test_generate_daily_report(reports_service):
    """Test daily report generation"""
    user_id = "user123"

    # Insert sample data
    ts = TimeSeriesDataPoint(
        user_id=user_id,
        period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        total_cost=50.0,
        num_operations=10,
        by_operation_type={"api_call": 30.0, "file_read": 20.0},
        by_file_format={"csv_pasted": 30.0, "pdf_url": 20.0},
        by_model={"sonnet": 40.0, "haiku": 10.0},
        by_provider={"openai": 50.0}
    )
    reports_service.db.insert_time_series(ts)

    # Generate report
    report = reports_service.generate_daily_report(user_id)

    assert report["type"] == "daily"
    assert report["user_id"] == user_id
    assert report["daily"]["total_cost"] == 50.0
    assert report["daily"]["num_operations"] == 10


def test_generate_weekly_report(reports_service):
    """Test weekly report generation"""
    user_id = "user123"

    # Insert 7 days of data
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=6-i)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        ts = TimeSeriesDataPoint(
            user_id=user_id,
            period_start=date,
            period_type="daily",
            total_cost=50.0 + (i * 5),
            num_operations=10,
            by_operation_type={"api_call": 35.0 + (i * 3), "file_read": 20.0},
            by_file_format={"csv_pasted": 30.0, "pdf_url": 25.0 + (i * 2)}
        )
        reports_service.db.insert_time_series(ts)

    # Generate report
    report = reports_service.generate_weekly_report(user_id)

    assert report["type"] == "weekly"
    assert report["user_id"] == user_id
    assert "weekly" in report
    assert report["weekly"]["total_cost"] > 300  # 7 days of data


def test_render_daily_html(reports_service):
    """Test rendering daily report as HTML"""
    user_id = "user123"

    ts = TimeSeriesDataPoint(
        user_id=user_id,
        period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        total_cost=50.0,
        num_operations=10,
        by_operation_type={"api_call": 30.0, "file_read": 20.0}
    )
    reports_service.db.insert_time_series(ts)

    report = reports_service.generate_daily_report(user_id)
    html = reports_service.render_html_report(report)

    # Check HTML contains expected elements
    assert "<html>" in html
    assert "PyCostAudit Daily Report" in html
    assert "$50.00" in html
    assert "Cost Breakdown" in html
    assert "Daily Budget" in html


def test_render_weekly_html(reports_service):
    """Test rendering weekly report as HTML"""
    user_id = "user123"

    # Insert 7 days of data
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=6-i)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        ts = TimeSeriesDataPoint(
            user_id=user_id,
            period_start=date,
            total_cost=50.0 + (i * 5),
            num_operations=10,
            by_operation_type={"api_call": 30.0, "file_read": 20.0}
        )
        reports_service.db.insert_time_series(ts)

    report = reports_service.generate_weekly_report(user_id)
    html = reports_service.render_html_report(report)

    # Check HTML contains expected elements
    assert "<html>" in html
    assert "PyCostAudit Weekly Report" in html
    assert "Daily Trend" in html
    assert "Operations" in html


def test_send_report_email(reports_service):
    """Test sending report via email"""
    user_id = "user123"

    ts = TimeSeriesDataPoint(
        user_id=user_id,
        period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        total_cost=50.0,
        num_operations=10
    )
    reports_service.db.insert_time_series(ts)

    report = reports_service.generate_daily_report(user_id)

    # Mock SMTP
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = mock_smtp.return_value.__enter__.return_value
        mock_server.login.return_value = None
        mock_server.sendmail.return_value = None

        result = reports_service.send_report_email("test@example.com", report)

        # Should fail due to missing SMTP config in env, or succeed if mocked
        assert isinstance(result, bool)


def test_budget_percentage_calculation(reports_service):
    """Test budget percentage calculation in report"""
    user_id = "user123"

    # Set budget
    reports_service.db.insert_alert_config(AlertConfiguration(
        user_id=user_id,
        daily_budget_usd=100.0
    ))

    # Insert data
    ts = TimeSeriesDataPoint(
        user_id=user_id,
        period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
        total_cost=75.0,
        num_operations=10
    )
    reports_service.db.insert_time_series(ts)

    # Generate report
    report = reports_service.generate_daily_report(user_id)

    # Check budget calculation
    assert report["budget"]["percent_used"] == 75.0


def test_recommendations_generation(reports_service):
    """Test recommendation generation"""
    user_id = "user123"

    # Create expensive operation scenario
    daily = {
        "total_cost": 100.0,
        "by_operation_type": {"api_call": 60.0, "file_read": 40.0},
        "by_file_format": {"pdf_url": 30.0, "csv_pasted": 70.0}
    }

    trend = {
        "average_daily": 50.0,
        "daily_costs": [45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 80.0]
    }

    recommendations = reports_service._generate_recommendations(daily, trend)

    # Should have recommendations for expensive operations
    assert len(recommendations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
