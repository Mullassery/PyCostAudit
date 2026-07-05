# Design: Real-time Alerting (Phase 2D) - Slack & Twilio

**Status**: Design (Ready for implementation)  
**Timeline**: Week 3-4  
**Owner**: Integrations Developer  
**Channels**: Slack (primary) + Twilio SMS (secondary)

---

## Overview

Real-time alerting system that detects cost spikes and budget breaches, notifying teams via Slack (primary) and Twilio SMS (urgent/critical only).

**Use Cases**:
- Budget threshold breach (75% spent)
- Cost anomaly detected (3-sigma deviation)
- Unusual spike (2x daily average in 1 hour)
- Critical alert (90%+ of budget spent)

---

## Architecture

```
┌──────────────────────────────────────────┐
│    CostTracker (Phase 2B)                │
│    Emits: new cost event                 │
└─────────────┬──────────────────────────┘
              ↓
┌──────────────────────────────────────────┐
│    Alert Engine                          │
│  ┌────────────────────────────────────┐  │
│  │ 1. Check budget threshold          │  │
│  │ 2. Detect anomaly (3-sigma)        │  │
│  │ 3. Check for recent spikes         │  │
│  │ 4. Suppress duplicates             │  │
│  │ 5. Route to channels               │  │
│  └────────────────────────────────────┘  │
└──────┬──────────────────┬────────────────┘
       ↓                  ↓
┌──────────────┐    ┌────────────────┐
│ Slack Channel│    │ Twilio SMS     │
│ (primary)    │    │ (critical only)│
└──────────────┘    └────────────────┘
```

---

## Alert Types & Severity

| Alert Type | Trigger | Severity | Slack | SMS |
|---|---|---|---|---|
| Budget Threshold | 75% of budget spent | HIGH | ✓ | ✗ |
| Budget Exceeded | 100%+ of budget spent | CRITICAL | ✓ | ✓ |
| Cost Anomaly | 3-sigma deviation | MEDIUM | ✓ | ✗ |
| Daily Spike | 2x daily avg in 1 hour | HIGH | ✓ | ✗ |
| Unusual Provider | New provider with high cost | MEDIUM | ✓ | ✗ |
| Model Change | Cost increased for same model | LOW | ✓ | ✗ |

---

## Core Components

### 1. Alert Policy Engine

```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class AlertSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class AlertType(Enum):
    BUDGET_THRESHOLD = "budget_threshold"
    BUDGET_EXCEEDED = "budget_exceeded"
    COST_ANOMALY = "cost_anomaly"
    DAILY_SPIKE = "daily_spike"
    UNUSUAL_PROVIDER = "unusual_provider"

@dataclass
class AlertPolicy:
    """User-configurable alert policy"""
    id: str
    name: str
    enabled: bool
    alert_type: AlertType
    severity: AlertSeverity
    
    # Thresholds
    budget_threshold_percent: float = 0.75  # 75% of budget
    anomaly_sigma: float = 3.0  # 3-sigma
    spike_multiplier: float = 2.0  # 2x average
    
    # Channels
    slack_enabled: bool = True
    slack_channel: str = "#cost-alerts"
    sms_enabled: bool = False  # Only for CRITICAL
    sms_phone: str = None
    
    # Suppression
    cooldown_minutes: int = 60  # Don't repeat same alert within 60 min
    max_alerts_per_day: int = 20  # Max alerts per day

class AlertEngine:
    """Core alerting logic"""
    
    def __init__(self):
        self.policies: Dict[str, AlertPolicy] = {}
        self.alert_history = []
        self.suppression_cache = {}
    
    def evaluate_cost(self, cost: Cost) -> List[Alert]:
        """Evaluate a new cost against all policies"""
        alerts = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            # Check if this alert type should trigger
            if policy.alert_type == AlertType.BUDGET_THRESHOLD:
                if self._check_budget_threshold(cost, policy):
                    alerts.append(self._create_alert(policy, cost))
            
            elif policy.alert_type == AlertType.COST_ANOMALY:
                if self._check_anomaly(cost, policy):
                    alerts.append(self._create_alert(policy, cost))
            
            elif policy.alert_type == AlertType.DAILY_SPIKE:
                if self._check_spike(cost, policy):
                    alerts.append(self._create_alert(policy, cost))
        
        # Filter suppressed alerts
        alerts = [a for a in alerts if not self._is_suppressed(a)]
        
        return alerts
    
    def _check_budget_threshold(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Check if budget threshold exceeded"""
        total_spent = self._get_total_spent_this_month()
        budget = self._get_budget()
        percent_used = total_spent / budget
        return percent_used >= policy.budget_threshold_percent
    
    def _check_anomaly(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Detect 3-sigma anomaly"""
        daily_average = self._get_daily_average()
        daily_std_dev = self._get_daily_std_dev()
        
        threshold = daily_average + (policy.anomaly_sigma * daily_std_dev)
        total_today = self._get_total_today()
        
        return total_today > threshold
    
    def _check_spike(self, cost: Cost, policy: AlertPolicy) -> bool:
        """Detect sudden cost spike"""
        hourly_average = self._get_hourly_average(last_7_days=True)
        total_this_hour = self._get_total_this_hour()
        
        return total_this_hour > (hourly_average * policy.spike_multiplier)
    
    def _is_suppressed(self, alert: Alert) -> bool:
        """Check if alert should be suppressed"""
        key = f"{alert.type}_{alert.provider}"
        
        if key not in self.suppression_cache:
            return False
        
        last_alert_time, count = self.suppression_cache[key]
        
        # Check cooldown
        if (now() - last_alert_time).minutes < alert.policy.cooldown_minutes:
            return True
        
        # Check max alerts per day
        if count >= alert.policy.max_alerts_per_day:
            return True
        
        return False
    
    def _create_alert(self, policy: AlertPolicy, cost: Cost) -> Alert:
        """Create an alert object"""
        return Alert(
            id=uuid4(),
            type=policy.alert_type,
            severity=policy.severity,
            provider=cost.provider,
            message=self._format_message(policy, cost),
            timestamp=now(),
            policy=policy,
            cost_data=cost
        )

@dataclass
class Alert:
    """Alert object to be sent to channels"""
    id: str
    type: AlertType
    severity: AlertSeverity
    provider: str
    message: str
    timestamp: datetime
    policy: AlertPolicy
    cost_data: Cost
```

---

### 2. Slack Integration

```python
import slack_sdk
from slack_sdk.errors import SlackApiError

class SlackAlertChannel:
    """Send alerts to Slack"""
    
    def __init__(self, bot_token: str):
        self.client = slack_sdk.WebClient(token=bot_token)
        self.bot_token = bot_token
    
    def send_alert(self, alert: Alert, channel: str = "#cost-alerts"):
        """Send alert to Slack channel"""
        
        color = self._get_color_for_severity(alert.severity)
        
        # Build message block
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
                        "text": f"*Provider:*\n{alert.provider}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Cost:*\n${alert.cost_data.total_cost:.2f}"
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
                        "url": "https://pycostaudit.example.com/dashboard"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Mute Alerts"
                        },
                        "action_id": "mute_alerts"
                    }
                ]
            }
        ]
        
        try:
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
            return response['ts']  # Message timestamp
        except SlackApiError as e:
            print(f"Error sending Slack alert: {e}")
            raise
    
    def _get_color_for_severity(self, severity: AlertSeverity) -> str:
        """Map severity to color"""
        return {
            AlertSeverity.LOW: "#36a64f",      # Green
            AlertSeverity.MEDIUM: "#ffa500",   # Orange
            AlertSeverity.HIGH: "#ff6600",     # Dark orange
            AlertSeverity.CRITICAL: "#ff0000"  # Red
        }[severity]
    
    def update_alert(self, channel: str, ts: str, alert: Alert):
        """Update an alert message (e.g., when resolved)"""
        self.client.chat_update(
            channel=channel,
            ts=ts,
            blocks=[...]  # New blocks
        )

class SlackInteractivityHandler:
    """Handle Slack button clicks and interactions"""
    
    def handle_mute_alerts(self, user_id: str, duration_minutes: int = 60):
        """Mute alerts for a user"""
        self.suppression_cache[user_id] = {
            'muted_until': now() + timedelta(minutes=duration_minutes)
        }
```

---

### 3. Twilio SMS Integration

```python
from twilio.rest import Client

class TwilioAlertChannel:
    """Send critical alerts via SMS (Twilio)"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number  # Twilio phone number
    
    def send_critical_alert(self, alert: Alert, to_numbers: List[str]):
        """Send critical alert via SMS"""
        
        # Only send CRITICAL and BUDGET_EXCEEDED
        if alert.severity != AlertSeverity.CRITICAL and \
           alert.type != AlertType.BUDGET_EXCEEDED:
            return
        
        message_text = f"""
🚨 PyCostAudit Alert
{alert.type.value}: {alert.provider}
Cost: ${alert.cost_data.total_cost:.2f}
{alert.message[:80]}...
View: https://pycostaudit.example.com
        """.strip()
        
        for to_number in to_numbers:
            try:
                self.client.messages.create(
                    body=message_text,
                    from_=self.from_number,
                    to=to_number
                )
            except Exception as e:
                print(f"Error sending SMS to {to_number}: {e}")
    
    def send_acknowledgment(self, to_number: str):
        """Send SMS confirmation that alert was processed"""
        self.client.messages.create(
            body="✓ Cost alert received and processed",
            from_=self.from_number,
            to=to_number
        )
```

---

## Alert Message Templates

### Slack Message Template

**Budget Threshold Alert**:
```
🚨 BUDGET ALERT

You've reached 75% of your monthly budget.

Budget: $500.00
Spent: $375.00 (75%)
Remaining: $125.00
Days left: 15

Daily burn rate: $18/day
Projected end-of-month: $445

[View Dashboard] [Update Budget]
```

**Cost Anomaly Alert**:
```
⚠️ COST ANOMALY DETECTED

Your spending pattern is unusual.

Daily average: $12
Today's total: $45
Deviation: 3.75 sigma

Breakdown:
• OpenAI GPT-4: $35 (increased 3x)
• Bedrock: $8
• Gemini: $2

[View Breakdown] [Investigate]
```

**Daily Spike Alert**:
```
📈 COST SPIKE DETECTED

Unusual spending in the last hour.

Hourly average: $1.50
This hour: $3.10
Spike: 2.07x

Top cost drivers:
1. OpenAI GPT-4 (vision): $2.50
2. Bedrock Claude 3: $0.60

[View Real-time] [View Trends]
```

### SMS Message Template

```
🚨 CRITICAL ALERT
Budget exceeded: $510/$500
Cost spike: +$87 in 1 hour
View: pycostaudit.io
```

---

## Implementation Plan

### Phase 1: Core Alerting Engine (Days 1-2)
- [ ] Implement `AlertEngine` class
- [ ] Create alert policies (budget, anomaly, spike)
- [ ] Build alert evaluation logic
- [ ] Add suppression/cooldown system
- [ ] Store alert history

### Phase 2: Slack Integration (Days 3-4)
- [ ] Set up Slack app + bot token
- [ ] Implement `SlackAlertChannel`
- [ ] Create message formatting (blocks)
- [ ] Add interactive buttons (view dashboard, mute)
- [ ] Test with real Slack workspace

### Phase 3: Twilio Integration (Days 4-5)
- [ ] Set up Twilio account + credentials
- [ ] Implement `TwilioAlertChannel`
- [ ] Create SMS message templates
- [ ] Add phone number management
- [ ] Test with real SMS

### Phase 4: Dashboard Integration (Days 5-6)
- [ ] Add alert policy management to dashboard
- [ ] Show alert history
- [ ] Allow users to mute/snooze alerts
- [ ] Real-time alert notifications in UI
- [ ] Alert settings page

---

## Configuration

### Environment Variables

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_ALERT_CHANNEL=#cost-alerts

# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=+1234567890

# Alert Settings
DEFAULT_ALERT_COOLDOWN_MINUTES=60
MAX_ALERTS_PER_DAY=20
ANOMALY_SIGMA=3.0
SPIKE_MULTIPLIER=2.0
```

### Alert Policies (YAML)

```yaml
policies:
  budget_threshold:
    enabled: true
    severity: HIGH
    threshold_percent: 0.75
    slack_channel: "#cost-alerts"
    sms_enabled: false
    cooldown_minutes: 120
  
  cost_anomaly:
    enabled: true
    severity: MEDIUM
    sigma: 3.0
    slack_channel: "#cost-alerts"
    sms_enabled: false
    cooldown_minutes: 60
  
  daily_spike:
    enabled: true
    severity: HIGH
    multiplier: 2.0
    slack_channel: "#cost-alerts"
    sms_enabled: false
    cooldown_minutes: 60
  
  budget_exceeded:
    enabled: true
    severity: CRITICAL
    slack_channel: "#cost-alerts"
    sms_enabled: true
    sms_numbers:
      - "+1234567890"
      - "+0987654321"
    cooldown_minutes: 15
```

---

## Testing

### Unit Tests

```python
def test_budget_threshold_alert():
    engine = AlertEngine()
    policy = AlertPolicy(alert_type=AlertType.BUDGET_THRESHOLD)
    
    # Cost at 75% of budget should trigger
    alert = engine.evaluate_cost(high_cost)
    assert len(alert) > 0
    assert alert[0].type == AlertType.BUDGET_THRESHOLD

def test_slack_message_formatting():
    slack = SlackAlertChannel(token="...")
    alert = create_test_alert()
    
    blocks = slack._format_blocks(alert)
    assert blocks[0]['type'] == 'header'
    assert 'BUDGET ALERT' in blocks[0]['text']['text']

def test_sms_only_for_critical():
    twilio = TwilioAlertChannel(...)
    
    # Medium alert should NOT send SMS
    twilio.send_critical_alert(medium_alert, ["+123456"])
    assert not twilio.messages_sent
    
    # Critical alert SHOULD send SMS
    twilio.send_critical_alert(critical_alert, ["+123456"])
    assert len(twilio.messages_sent) == 1
```

### Integration Tests

```python
def test_end_to_end_alert_flow():
    # Trigger high cost
    cost = Cost(provider='openai', total_cost=500.00)
    
    # Engine detects budget breach
    alerts = engine.evaluate_cost(cost)
    assert len(alerts) == 1
    
    # Slack notification sent
    slack_messages = slack_mock.get_messages()
    assert len(slack_messages) == 1
    
    # SMS sent only for CRITICAL
    sms_messages = twilio_mock.get_messages()
    assert len(sms_messages) == 1
```

---

## Success Criteria

- ✓ Budget threshold alerts trigger at 75%+ spent
- ✓ Anomaly detection (3-sigma) working
- ✓ Slack messages formatted correctly (blocks + colors)
- ✓ SMS sent only for CRITICAL alerts
- ✓ Cooldown/suppression preventing spam
- ✓ All integration tests passing
- ✓ <5 second latency from cost to Slack notification

---

## Next Steps

1. Implement Alert Engine (core logic)
2. Set up Slack app and get bot token
3. Set up Twilio account and get credentials
4. Implement Slack integration
5. Implement Twilio integration
6. Integration with Phase 2C (dashboard alert management)
