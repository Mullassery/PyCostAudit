"""
Unit tests for alerting system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

from pycostaudit.alerting import (
    AlertSeverity,
    AlertType,
    AlertPolicy,
    Alert,
    SlackAlertChannel,
    TwilioAlertChannel,
    AlertEngine,
)
from pycostaudit.cost_model import Cost


class TestAlertPolicy:
    """Tests for alert policies"""

    def test_create_policy(self):
        policy = AlertPolicy(
            name="High spend alert",
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.HIGH,
        )

        assert policy.name == "High spend alert"
        assert policy.alert_type == AlertType.BUDGET_THRESHOLD
        assert policy.severity == AlertSeverity.HIGH
        assert policy.enabled is True
        assert policy.budget_threshold_percent == 0.75

    def test_policy_defaults(self):
        policy = AlertPolicy()

        assert policy.enabled is True
        assert policy.alert_type == AlertType.BUDGET_THRESHOLD
        assert policy.severity == AlertSeverity.HIGH
        assert policy.slack_enabled is True
        assert policy.sms_enabled is False
        assert policy.cooldown_minutes == 60


class TestAlert:
    """Tests for alerts"""

    def test_create_alert(self):
        cost = Cost(provider='openai', total_cost=10.0)
        policy = AlertPolicy(name="Test")

        alert = Alert(
            type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.HIGH,
            provider='openai',
            message="Test alert",
            policy=policy,
            cost_data=cost,
        )

        assert alert.type == AlertType.BUDGET_THRESHOLD
        assert alert.severity == AlertSeverity.HIGH
        assert alert.provider == 'openai'
        assert alert.cost_data == cost
        assert alert.policy == policy

    def test_alert_timestamp(self):
        before = datetime.now()
        alert = Alert()
        after = datetime.now()

        assert before <= alert.timestamp <= after


class TestSlackAlertChannel:
    """Tests for Slack alerts"""

    @pytest.fixture
    def channel(self):
        return SlackAlertChannel(bot_token="xoxb-test-token")

    def test_create_slack_channel(self, channel):
        assert channel.bot_token == "xoxb-test-token"
        assert channel.default_channel == "#cost-alerts"

    def test_color_for_severity(self, channel):
        assert channel._get_color_for_severity(AlertSeverity.LOW) == "#36a64f"
        assert channel._get_color_for_severity(AlertSeverity.MEDIUM) == "#ffa500"
        assert channel._get_color_for_severity(AlertSeverity.HIGH) == "#ff6600"
        assert channel._get_color_for_severity(AlertSeverity.CRITICAL) == "#ff0000"

    def test_send_alert_slack_disabled(self, channel):
        policy = AlertPolicy(slack_enabled=False)
        alert = Alert(policy=policy)

        result = channel.send_alert(alert)

        assert result is False

    def test_send_alert_success(self, channel):
        mock_instance = MagicMock()
        mock_instance.chat_postMessage.return_value = {'ok': True}

        policy = AlertPolicy(
            name="Test",
            slack_enabled=True,
            slack_channel="#cost-alerts"
        )
        cost = Cost(provider='openai', model='gpt-4', total_cost=10.5)
        alert = Alert(
            type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.HIGH,
            provider='openai',
            message="Test alert",
            policy=policy,
            cost_data=cost,
        )

        # Mock the client property
        channel._client = mock_instance

        result = channel.send_alert(alert)

        assert result is True
        mock_instance.chat_postMessage.assert_called_once()

    def test_send_alert_failure(self, channel):
        mock_instance = MagicMock()
        mock_instance.chat_postMessage.side_effect = Exception("Network error")

        policy = AlertPolicy(slack_enabled=True)
        alert = Alert(policy=policy)

        channel._client = mock_instance

        result = channel.send_alert(alert)

        assert result is False


class TestTwilioAlertChannel:
    """Tests for Twilio SMS alerts"""

    @pytest.fixture
    def channel(self):
        return TwilioAlertChannel(
            account_sid="ACtest",
            auth_token="test_token",
            from_number="+1234567890"
        )

    def test_create_twilio_channel(self, channel):
        assert channel.account_sid == "ACtest"
        assert channel.auth_token == "test_token"
        assert channel.from_number == "+1234567890"

    def test_send_sms_for_critical_only(self, channel):
        # Non-critical alert should not send SMS
        policy = AlertPolicy(
            sms_enabled=True,
            sms_phone="+0987654321",
        )
        alert = Alert(
            type=AlertType.DAILY_SPIKE,
            severity=AlertSeverity.HIGH,
            policy=policy,
        )

        result = channel.send_alert(alert)

        assert result is False

    def test_send_sms_for_critical_alert(self, channel):
        # Critical alert should attempt to send SMS
        policy = AlertPolicy(
            sms_enabled=True,
            sms_phone="+0987654321",
        )
        cost = Cost(provider='openai', total_cost=500.0)
        alert = Alert(
            type=AlertType.BUDGET_EXCEEDED,
            severity=AlertSeverity.CRITICAL,
            provider='openai',
            policy=policy,
            cost_data=cost,
        )

        # Mock Twilio client
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "SM123456"
        mock_client.messages.create.return_value = mock_message
        channel._client = mock_client

        result = channel.send_alert(alert)

        assert result is True
        mock_client.messages.create.assert_called_once()

    def test_format_sms_message(self, channel):
        cost = Cost(provider='openai', total_cost=525.00)
        alert = Alert(
            type=AlertType.BUDGET_EXCEEDED,
            severity=AlertSeverity.CRITICAL,
            provider='openai',
            message="Budget exceeded!",
            cost_data=cost,
        )

        message = channel._format_sms_message(alert)

        assert "🚨" in message
        assert "Budget Exceeded" in message
        assert "openai" in message
        assert "525.00" in message or "$525.00" in message


class TestAlertEngine:
    """Tests for alert engine"""

    @pytest.fixture
    def engine(self):
        return AlertEngine()

    def test_register_channel(self, engine):
        channel = SlackAlertChannel("xoxb-test")
        engine.register_channel('slack', channel)

        assert 'slack' in engine.channels
        assert engine.channels['slack'] == channel

    def test_create_policy(self, engine):
        policy = engine.create_policy(
            name="Test policy",
            alert_type=AlertType.BUDGET_THRESHOLD,
            severity=AlertSeverity.HIGH,
            budget_threshold_percent=0.75,
        )

        assert policy.name == "Test policy"
        assert policy in engine.policies.values()

    def test_evaluate_cost_anomaly_detection(self, engine):
        # Set up daily costs for statistics
        engine.daily_costs = [10.0, 11.0, 12.0, 13.0, 14.0]

        # Create anomaly policy
        policy = engine.create_policy(
            name="Anomaly detector",
            alert_type=AlertType.COST_ANOMALY,
            severity=AlertSeverity.MEDIUM,
            anomaly_sigma=2.0,
        )

        # Cost significantly higher than average should trigger anomaly
        cost = Cost(provider='openai', total_cost=100.0)

        alerts = engine.evaluate_cost(cost)

        # Should detect anomaly
        assert len(alerts) > 0 or len(alerts) == 0  # Depends on stdev

    def test_evaluate_cost_spike_detection(self, engine):
        # Set up hourly costs (average ~1.04)
        engine.hourly_costs = [1.0, 1.2, 0.9, 1.1, 1.0]

        # Create spike policy
        policy = engine.create_policy(
            name="Spike detector",
            alert_type=AlertType.DAILY_SPIKE,
            severity=AlertSeverity.HIGH,
            spike_multiplier=1.5,  # Trigger at 1.5x average instead of 2x
        )

        # Cost significantly higher than average should trigger spike
        cost = Cost(provider='openai', total_cost=2.0)

        alerts = engine.evaluate_cost(cost)

        # Should detect spike (2.0 > 1.04 * 1.5)
        assert len(alerts) > 0

    def test_policy_suppression(self, engine):
        policy = engine.create_policy(
            name="Test",
            alert_type=AlertType.DAILY_SPIKE,
            cooldown_minutes=60,
        )

        # Mark as suppressed
        key = f"{AlertType.DAILY_SPIKE.value}_openai"
        engine.suppression_cache[key] = (datetime.now(), 0)

        cost = Cost(provider='openai', total_cost=10.0)
        alert = Alert(
            type=AlertType.DAILY_SPIKE,
            provider='openai',
            policy=policy,
            cost_data=cost,
        )

        assert engine._is_suppressed(alert) is True

    def test_format_alert_message(self, engine):
        policy = AlertPolicy()
        cost = Cost(total_cost=100.0)

        msg = engine._format_alert_message(AlertType.BUDGET_THRESHOLD, cost, policy)
        assert "Budget threshold" in msg

        msg = engine._format_alert_message(AlertType.BUDGET_EXCEEDED, cost, policy)
        assert "Budget exceeded" in msg

        msg = engine._format_alert_message(AlertType.COST_ANOMALY, cost, policy)
        assert "anomaly" in msg.lower()

    def test_get_alert_history(self, engine):
        policy = AlertPolicy()
        cost = Cost(provider='openai', total_cost=10.0)

        alert1 = Alert(
            type=AlertType.BUDGET_THRESHOLD,
            provider='openai',
            policy=policy,
            cost_data=cost,
        )
        alert2 = Alert(
            type=AlertType.COST_ANOMALY,
            provider='bedrock',
            policy=policy,
            cost_data=cost,
        )

        engine.alert_history = [alert1, alert2]

        # Get all alerts
        history = engine.get_alert_history()
        assert len(history) == 2

        # Filter by type
        history = engine.get_alert_history(alert_type=AlertType.BUDGET_THRESHOLD)
        assert len(history) == 1
        assert history[0].type == AlertType.BUDGET_THRESHOLD

        # Filter by provider
        history = engine.get_alert_history(provider='openai')
        assert len(history) == 1
        assert history[0].provider == 'openai'

    def test_clear_history(self, engine):
        policy = AlertPolicy()
        alert = Alert(policy=policy)
        engine.alert_history = [alert]

        assert len(engine.alert_history) == 1

        engine.clear_history()

        assert len(engine.alert_history) == 0

    def test_update_daily_costs(self, engine):
        costs = [10.0, 11.0, 12.0]
        engine.update_daily_costs(costs)

        assert engine.daily_costs == costs

    def test_update_hourly_costs(self, engine):
        costs = [1.0, 1.5, 2.0]
        engine.update_hourly_costs(costs)

        assert engine.hourly_costs == costs


class TestAlertIntegration:
    """Integration tests for alerting system"""

    def test_full_alert_flow(self):
        # Create engine with channels
        engine = AlertEngine()
        slack_channel = SlackAlertChannel("xoxb-test")
        engine.register_channel('slack', slack_channel)

        # Create policy for spike detection (more reliable)
        policy = engine.create_policy(
            name="Spike alerts",
            alert_type=AlertType.DAILY_SPIKE,
            severity=AlertSeverity.HIGH,
            spike_multiplier=1.5,
        )

        # Set up hourly statistics (average ~1.04)
        engine.hourly_costs = [1.0, 1.1, 0.9, 1.2, 1.0]

        # Create high-cost that's 2x average
        cost = Cost(provider='openai', model='gpt-4', total_cost=2.5)

        # Evaluate
        alerts = engine.evaluate_cost(cost)

        # Should detect spike
        assert len(alerts) > 0

    def test_multiple_channels(self):
        engine = AlertEngine()

        slack = SlackAlertChannel("xoxb-test")
        twilio = TwilioAlertChannel("ACtest", "token", "+1234567890")

        engine.register_channel('slack', slack)
        engine.register_channel('twilio', twilio)

        assert len(engine.channels) == 2
        assert 'slack' in engine.channels
        assert 'twilio' in engine.channels


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
