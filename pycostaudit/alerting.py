"""
Real-time alerting system for cost monitoring.
Supports Slack and Twilio SMS alerts.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import uuid
from collections import defaultdict

from .cost_model import Cost


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AlertType(Enum):
    """Alert types"""
    BUDGET_THRESHOLD = "budget_threshold"
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_ANOMALY = "cost_anomaly"
    DAILY_SPIKE = "daily_spike"
    UNUSUAL_PROVIDER = "unusual_provider"


@dataclass
class AlertPolicy:
    """User-configurable alert policy"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    enabled: bool = True
    alert_type: AlertType = AlertType.BUDGET_THRESHOLD
    severity: AlertSeverity = AlertSeverity.HIGH

    # Thresholds
    budget_threshold_percent: float = 0.75  # 75% of budget
    anomaly_sigma: float = 3.0  # 3-sigma deviation
    spike_multiplier: float = 2.0  # 2x average

    # Channels
    slack_enabled: bool = True
    slack_channel: str = "#cost-alerts"
    sms_enabled: bool = False  # Only for CRITICAL
    sms_phone: Optional[str] = None

    # Suppression
    cooldown_minutes: int = 60
    max_alerts_per_day: int = 20


@dataclass
class Alert:
    """Alert object to be sent to channels"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: AlertType = AlertType.BUDGET_THRESHOLD
    severity: AlertSeverity = AlertSeverity.HIGH
    provider: str = ""
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    policy: Optional[AlertPolicy] = None
    cost_data: Optional[Cost] = None
    details: Dict[str, Any] = field(default_factory=dict)


class AlertChannel(ABC):
    """Abstract base class for alert channels"""

    @abstractmethod
    def send_alert(self, alert: Alert) -> bool:
        """Send alert to this channel"""
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate channel credentials"""
        pass


class SlackAlertChannel(AlertChannel):
    """Slack alert channel"""

    def __init__(self, bot_token: str, default_channel: str = "#cost-alerts"):
        """Initialize Slack channel

        Args:
            bot_token: Slack bot token (starts with xoxb-)
            default_channel: Default channel to send alerts to
        """
        self.bot_token = bot_token
        self.default_channel = default_channel
        self._client = None

    @property
    def client(self):
        """Lazy-load Slack client"""
        if self._client is None:
            try:
                import slack_sdk
                self._client = slack_sdk.WebClient(token=self.bot_token)
            except ImportError:
                raise ImportError("slack-sdk not installed. Run: pip install slack-sdk")
        return self._client

    def send_alert(
        self,
        alert: Alert,
        channel: Optional[str] = None
    ) -> bool:
        """Send alert to Slack"""
        if not alert.policy or not alert.policy.slack_enabled:
            return False

        channel = channel or alert.policy.slack_channel or self.default_channel

        try:
            color = self._get_color_for_severity(alert.severity)

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {alert.type.value.replace('_', ' ').title()}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{alert.severity.name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Provider:*\n{alert.provider or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Cost:*\n${alert.cost_data.total_cost:.2f}" if alert.cost_data else "*Cost:*\nN/A"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:*\n{alert.message}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Dashboard"
                            },
                            "url": "https://pycostaudit.example.com/dashboard",
                            "action_id": "view_dashboard"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Mute Alerts"
                            },
                            "action_id": f"mute_alerts_{alert.id}"
                        }
                    ]
                }
            ]

            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                attachments=[
                    {
                        "color": color,
                        "text": f"Alert ID: {alert.id}"
                    }
                ]
            )

            return response['ok']

        except Exception as e:
            print(f"Error sending Slack alert: {e}")
            return False

    def validate_credentials(self) -> bool:
        """Validate Slack credentials"""
        try:
            response = self.client.auth_test()
            return response['ok']
        except Exception:
            return False

    @staticmethod
    def _get_color_for_severity(severity: AlertSeverity) -> str:
        """Map severity to color"""
        return {
            AlertSeverity.LOW: "#36a64f",      # Green
            AlertSeverity.MEDIUM: "#ffa500",   # Orange
            AlertSeverity.HIGH: "#ff6600",     # Dark orange
            AlertSeverity.CRITICAL: "#ff0000"  # Red
        }[severity]


class TwilioAlertChannel(AlertChannel):
    """Twilio SMS alert channel"""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str
    ):
        """Initialize Twilio channel

        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio phone number (e.g., +1234567890)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self._client = None

    @property
    def client(self):
        """Lazy-load Twilio client"""
        if self._client is None:
            try:
                from twilio.rest import Client
                self._client = Client(self.account_sid, self.auth_token)
            except ImportError:
                raise ImportError("twilio not installed. Run: pip install twilio")
        return self._client

    def send_alert(self, alert: Alert) -> bool:
        """Send critical alert via SMS"""
        # Only send SMS for CRITICAL alerts
        if alert.severity != AlertSeverity.CRITICAL and \
           alert.type != AlertType.BUDGET_EXCEEDED:
            return False

        if not alert.policy or not alert.policy.sms_enabled or not alert.policy.sms_phone:
            return False

        try:
            message_text = self._format_sms_message(alert)

            response = self.client.messages.create(
                body=message_text,
                from_=self.from_number,
                to=alert.policy.sms_phone
            )

            return response.sid is not None

        except Exception as e:
            print(f"Error sending SMS alert: {e}")
            return False

    def validate_credentials(self) -> bool:
        """Validate Twilio credentials"""
        try:
            # Try a simple API call to validate
            self.client.api.accounts(self.account_sid).fetch()
            return True
        except Exception:
            return False

    @staticmethod
    def _format_sms_message(alert: Alert) -> str:
        """Format alert as SMS message"""
        cost_str = f"${alert.cost_data.total_cost:.2f}" if alert.cost_data else "N/A"

        return f"""
🚨 PyCostAudit Alert
{alert.type.value.replace('_', ' ').title()}
{alert.provider or 'N/A'}: {cost_str}
{alert.message[:50]}...
View: https://pycostaudit.io
        """.strip()


class AlertEngine:
    """Core alerting logic"""

    def __init__(self):
        self.policies: Dict[str, AlertPolicy] = {}
        self.alert_history: List[Alert] = []
        self.suppression_cache: Dict[str, tuple] = {}
        self.channels: Dict[str, AlertChannel] = {}

        # Statistics for anomaly detection
        self.daily_costs: List[float] = []
        self.hourly_costs: List[float] = []

    def register_channel(self, name: str, channel: AlertChannel):
        """Register an alert channel"""
        self.channels[name] = channel

    def create_policy(
        self,
        name: str,
        alert_type: AlertType,
        **kwargs
    ) -> AlertPolicy:
        """Create and register an alert policy"""
        policy = AlertPolicy(name=name, alert_type=alert_type, **kwargs)
        self.policies[policy.id] = policy
        return policy

    def evaluate_cost(self, cost: Cost) -> List[Alert]:
        """Evaluate a new cost against all policies"""
        alerts = []

        for policy in self.policies.values():
            if not policy.enabled:
                continue

            # Check each alert type
            if policy.alert_type == AlertType.BUDGET_THRESHOLD:
                if self._check_budget_threshold(cost, policy):
                    alerts.append(self._create_alert(policy, cost, AlertType.BUDGET_THRESHOLD))

            elif policy.alert_type == AlertType.COST_ANOMALY:
                if self._check_anomaly(cost, policy):
                    alerts.append(self._create_alert(policy, cost, AlertType.COST_ANOMALY))

            elif policy.alert_type == AlertType.DAILY_SPIKE:
                if self._check_spike(cost, policy):
                    alerts.append(self._create_alert(policy, cost, AlertType.DAILY_SPIKE))

        # Filter suppressed alerts
        alerts = [a for a in alerts if not self._is_suppressed(a)]

        # Send alerts to all registered channels
        for alert in alerts:
            self._send_alert(alert)
            self.alert_history.append(alert)

        return alerts

    def _check_budget_threshold(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Check if budget threshold exceeded"""
        # This would integrate with a budget tracker
        # For now, return False (would be implemented with full integration)
        return False

    def _check_anomaly(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Detect 3-sigma anomaly"""
        if len(self.daily_costs) < 3:
            return False

        import statistics

        avg = statistics.mean(self.daily_costs)
        stdev = statistics.stdev(self.daily_costs) if len(self.daily_costs) > 1 else 0

        threshold = avg + (policy.anomaly_sigma * stdev)

        return cost.total_cost > threshold

    def _check_spike(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Detect sudden cost spike"""
        if len(self.hourly_costs) < 2:
            return False

        import statistics

        avg = statistics.mean(self.hourly_costs)
        return cost.total_cost > (avg * policy.spike_multiplier)

    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed"""
        key = f"{alert.type.value}_{alert.provider}"

        if key not in self.suppression_cache:
            return False

        last_alert_time, count = self.suppression_cache[key]

        # Check cooldown
        if (datetime.now() - last_alert_time).total_seconds() < alert.policy.cooldown_minutes * 60:
            return True

        # Check max alerts per day
        if count >= alert.policy.max_alerts_per_day:
            return True

        return False

    def _create_alert(
        self,
        policy: AlertPolicy,
        cost: Cost,
        alert_type: AlertType
    ) -> Alert:
        """Create an alert object"""
        message = self._format_alert_message(alert_type, cost, policy)

        return Alert(
            type=alert_type,
            severity=policy.severity,
            provider=cost.provider,
            message=message,
            policy=policy,
            cost_data=cost,
        )

    def _send_alert(self, alert: Alert):
        """Send alert to all registered channels"""
        for channel in self.channels.values():
            try:
                channel.send_alert(alert)
            except Exception as e:
                print(f"Error sending alert to channel: {e}")

    def _format_alert_message(
        self,
        alert_type: AlertType,
        cost: Cost,
        policy: AlertPolicy
    ) -> str:
        """Format alert message based on type"""
        if alert_type == AlertType.BUDGET_THRESHOLD:
            return f"Budget threshold reached ({policy.budget_threshold_percent*100:.0f}%)"
        elif alert_type == AlertType.BUDGET_EXCEEDED:
            return "Budget exceeded!"
        elif alert_type == AlertType.COST_ANOMALY:
            return f"Cost anomaly detected: {cost.total_cost:.2f} (3-sigma deviation)"
        elif alert_type == AlertType.DAILY_SPIKE:
            return f"Daily spending spike detected: {cost.total_cost:.2f}"
        else:
            return f"Alert: {alert_type.value}"

    def get_alert_history(
        self,
        alert_type: Optional[AlertType] = None,
        provider: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alert history"""
        results = self.alert_history

        if alert_type:
            results = [a for a in results if a.type == alert_type]

        if provider:
            results = [a for a in results if a.provider == provider]

        return results[-limit:]

    def clear_history(self):
        """Clear alert history"""
        self.alert_history.clear()

    def update_daily_costs(self, costs: List[float]):
        """Update daily cost statistics for anomaly detection"""
        self.daily_costs = costs

    def update_hourly_costs(self, costs: List[float]):
        """Update hourly cost statistics for spike detection"""
        self.hourly_costs = costs
