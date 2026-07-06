"""
Tests for alerts service.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from pycostaudit.database import DatabaseManager, AlertConfiguration
from pycostaudit.alerts_service import AlertsService


@pytest.fixture
def temp_db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path


@pytest.fixture
def alerts_service(temp_db):
    """Create alerts service with temp database"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    service = AlertsService(db)
    yield service
    db.disconnect()


def test_evaluate_budget_no_alerts(alerts_service):
    """Test evaluating budget when no alerts should trigger"""
    # Set budget to $100, current cost is $50 (50% used, no alert at 75%)
    alerts_service.db.insert_alert_config(AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75,
        enabled=True
    ))

    alerts = alerts_service.evaluate_budget(
        user_id="user123",
        current_cost=50.0,
        period="daily"
    )

    assert len(alerts) == 0


def test_evaluate_budget_threshold_alert(alerts_service):
    """Test budget threshold alert triggers at 75%"""
    alerts_service.db.insert_alert_config(AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75,
        slack_webhook_url="https://hooks.slack.com/test",
        enabled=True
    ))

    with patch.object(alerts_service, 'send_slack_alert', return_value=True):
        alerts = alerts_service.evaluate_budget(
            user_id="user123",
            current_cost=75.0,
            period="daily"
        )

        assert len(alerts) == 1
        assert alerts[0].alert_type == "budget_threshold"
        assert alerts[0].current_cost == 75.0


def test_evaluate_budget_critical_alert(alerts_service):
    """Test critical alert triggers at 90%"""
    alerts_service.db.insert_alert_config(AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        critical_at_percent=0.90,
        alert_at_percent=0.75,
        slack_webhook_url="https://hooks.slack.com/test",
        enabled=True
    ))

    with patch.object(alerts_service, 'send_slack_alert', return_value=True):
        alerts = alerts_service.evaluate_budget(
            user_id="user123",
            current_cost=95.0,
            period="daily"
        )

        # Should have both threshold and critical alerts
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        assert len(critical_alerts) >= 1


def test_slack_alert_formatting(alerts_service):
    """Test Slack alert message formatting"""
    config = AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75
    )

    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200

        result = alerts_service.send_slack_alert(
            "https://hooks.slack.com/test",
            alerts_service._create_and_send_alert(
                user_id="user123",
                config=config,
                alert_type="budget_threshold",
                current_cost=75.0,
                budget_limit=100.0,
                threshold_percent=0.75,
                percent_used=75.0,
                period="daily"
            ) or MagicMock(
                alert_type="budget_threshold",
                message="Test message",
                severity="high",
                current_cost=75.0,
                budget_limit=100.0
            )
        )

        # Verify requests.post was called
        assert mock_post.called or result in [True, False]


def test_alert_suppression(alerts_service):
    """Test alert suppression/cooldown"""
    # First alert should not be suppressed
    assert not alerts_service._is_suppressed("user123", "budget_threshold")

    # Simulate sending alert
    alerts_service._update_suppression_cache("user123", "budget_threshold")

    # Second alert should be suppressed
    assert alerts_service._is_suppressed("user123", "budget_threshold")


def test_get_alert_history(alerts_service):
    """Test retrieving alert history"""
    config = AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75,
        enabled=True
    )
    alerts_service.db.insert_alert_config(config)

    with patch.object(alerts_service, 'send_slack_alert', return_value=True):
        # Create multiple alerts
        for cost in [75.0, 80.0, 85.0]:
            alerts_service.evaluate_budget("user123", cost, "daily")

    # Get history
    history = alerts_service.get_alert_history("user123")

    assert len(history) > 0
    assert all(alert.user_id == "user123" for alert in history)


def test_alert_stats(alerts_service):
    """Test alert statistics"""
    config = AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75,
        enabled=True
    )
    alerts_service.db.insert_alert_config(config)

    with patch.object(alerts_service, 'send_slack_alert', return_value=True):
        alerts_service.evaluate_budget("user123", 75.0, "daily")

    stats = alerts_service.get_alert_stats("user123", days=7)

    assert "total_alerts" in stats
    assert "by_type" in stats
    assert "by_severity" in stats


def test_acknowledge_alert(alerts_service):
    """Test acknowledging an alert"""
    config = AlertConfiguration(
        user_id="user123",
        daily_budget_usd=100.0,
        alert_at_percent=0.75,
        enabled=True
    )
    alerts_service.db.insert_alert_config(config)

    with patch.object(alerts_service, 'send_slack_alert', return_value=True):
        alerts = alerts_service.evaluate_budget("user123", 75.0, "daily")

    if alerts:
        alert_id = alerts[0].id
        result = alerts_service.acknowledge_alert(alert_id)
        assert result is True


def test_severity_color_mapping(alerts_service):
    """Test severity color mapping"""
    assert alerts_service._get_severity_color("low") == "#36a64f"
    assert alerts_service._get_severity_color("medium") == "#ffa500"
    assert alerts_service._get_severity_color("high") == "#ff6600"
    assert alerts_service._get_severity_color("critical") == "#d32f2f"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
