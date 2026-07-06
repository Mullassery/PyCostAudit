# PyCostAudit Budget Alerts - Setup Guide

Real-time budget monitoring with Slack, Email, and SMS notifications.

## Features

- ✅ **Daily/Weekly/Monthly Budgets** - Set spending limits per period
- ✅ **Multi-Channel Notifications** - Slack, Email, SMS (optional)
- ✅ **Customizable Thresholds** - Alert at 75%, critical at 90% (adjustable)
- ✅ **Alert Suppression** - Prevent alert spam with configurable cooldown
- ✅ **Alert History** - Full audit trail of all alerts
- ✅ **Statistics** - Track alert trends over time

---

## Quick Start (5 minutes)

### 1. Configure Your Budget

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id your_email@example.com \
  --daily 50 \
  --weekly 300 \
  --monthly 1000 \
  --slack-webhook https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### 2. View Configuration

```bash
python -m pycostaudit.alerts_cli show_config --user-id your_email@example.com
```

### 3. Check Current Alerts

```bash
python -m pycostaudit.alerts_cli check --user-id your_email@example.com --period daily
```

---

## Setup Guide

### Slack Integration

#### Step 1: Create Slack App

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. App Name: `PyCostAudit`
4. Choose workspace
5. Click "Create App"

#### Step 2: Enable Webhooks

1. Go to "Incoming Webhooks"
2. Toggle "Activate Incoming Webhooks" ON
3. Click "Add New Webhook to Workspace"
4. Select channel (e.g., `#cost-alerts`)
5. Click "Allow"
6. Copy the webhook URL

#### Step 3: Configure PyCostAudit

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id your_email@example.com \
  --daily 50 \
  --slack-webhook https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX
```

#### Test Slack Alert

```bash
# This will send a test alert to your Slack channel
python -m pycostaudit.alerts_cli check --user-id your_email@example.com
```

Expected output in Slack:
```
🚨 PyCostAudit: Budget Threshold
Current Cost: $XX.XX
Budget Limit: $XX.XX
Severity: HIGH
```

---

### Email Integration

#### Prerequisites

- Email address where you want to receive alerts
- SMTP credentials (Gmail, SendGrid, custom server)

#### Step 1: Configure SMTP

Set environment variables:

```bash
# Gmail example (use App Password, not your regular password)
export PYCOSTAUDIT_SMTP_HOST=smtp.gmail.com
export PYCOSTAUDIT_SMTP_PORT=587
export PYCOSTAUDIT_SMTP_USER=your_email@gmail.com
export PYCOSTAUDIT_SMTP_PASSWORD=your_app_password
export PYCOSTAUDIT_FROM_EMAIL=your_email@gmail.com
```

#### Step 2: Enable PyCostAudit Email

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id your_email@example.com \
  --daily 50 \
  --email your_email@example.com
```

#### Step 3: Test Email Alert

```bash
python -m pycostaudit.alerts_cli check --user-id your_email@example.com
```

Check your inbox for the alert email.

---

### SMS Integration (Optional - Twilio)

#### Step 1: Create Twilio Account

1. Go to [Twilio Console](https://www.twilio.com/console)
2. Create account
3. Get your Account SID and Auth Token
4. Purchase a phone number

#### Step 2: Configure Environment

```bash
export TWILIO_ACCOUNT_SID=your_account_sid
export TWILIO_AUTH_TOKEN=your_auth_token
export TWILIO_PHONE_NUMBER=+1234567890
```

#### Step 3: Enable SMS Alerts

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id your_email@example.com \
  --daily 50 \
  --sms +1234567890
```

SMS alerts only trigger on CRITICAL alerts (budget exceeded by >10%).

---

## Usage

### Set Budget and Notifications

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id user123 \
  --daily 100 \
  --weekly 500 \
  --monthly 2000 \
  --slack-webhook https://hooks.slack.com/... \
  --email user@example.com \
  --notify-at 0.75
```

**Parameters:**
- `--user-id`: Unique identifier (email recommended)
- `--daily`: Daily budget in USD
- `--weekly`: Weekly budget in USD
- `--monthly`: Monthly budget in USD
- `--slack-webhook`: Slack incoming webhook URL
- `--email`: Email address for alerts
- `--sms`: Phone number for SMS (requires Twilio)
- `--notify-at`: Threshold percentage (0.75 = 75%, default)

### Check Current Budget Status

```bash
python -m pycostaudit.alerts_cli check \
  --user-id user123 \
  --period daily
```

Output:
```
✅ No alerts triggered
   Current cost: $45.23
```

Or with alerts:
```
🚨 1 alert(s) triggered:
   [HIGH] Daily budget 85.0% used ($85.00/$100.00)
```

### View Alert History

```bash
python -m pycostaudit.alerts_cli history \
  --user-id user123 \
  --limit 20 \
  --type budget_threshold
```

Output:
```
Alert History (20 recent):

✅ [HIGH] Budget Threshold
   Message: Daily budget 85.0% used ($85.00/$100.00)
   Time: 2024-07-06 14:30:00 UTC
   Channels: Slack, Email

⏳ [HIGH] Budget Threshold
   Message: Daily budget 75.0% used ($75.00/$100.00)
   Time: 2024-07-06 10:15:00 UTC
   Channels: Slack
```

### View Alert Statistics

```bash
python -m pycostaudit.alerts_cli stats --user-id user123 --days 7
```

Output:
```
Alert Statistics (last 7 days):

Total alerts: 14

By Type:
  Budget Threshold: 12
  Budget Exceeded: 2

By Severity:
  HIGH: 12
  CRITICAL: 2
```

### Acknowledge an Alert

```bash
python -m pycostaudit.alerts_cli acknowledge \
  --user-id user123 \
  --alert-id 550e8400-e29b-41d4-a716-446655440000
```

### Show Current Configuration

```bash
python -m pycostaudit.alerts_cli show_config --user-id user123
```

Output:
```
Budget Configuration:

User: user123
Status: Enabled

Budgets:
  Daily:   $100.0
  Weekly:  $500.0
  Monthly: $2000.0

Alert Thresholds:
  Alert at:   75% of budget
  Critical at: 90% of budget

Notification Channels:
  Slack:  Configured
  Email:  Configured (user@example.com)
  SMS:    Not configured

Notification Preferences:
  Budget threshold: Enabled
  Anomalies:        Enabled
  Spikes:           Enabled

Alert Suppression:
  Cooldown: 60 minutes
  Max alerts per day: 20
```

---

## Alert Types

| Alert Type | Trigger | Severity | Default Channel |
|---|---|---|---|
| **Budget Threshold** | Cost >= 75% of budget | HIGH | All |
| **Budget Exceeded** | Cost >= 90% of budget | CRITICAL | All + SMS |
| **Anomaly Detected** | Cost deviates 3σ from baseline | HIGH | Slack + Email |
| **Spending Spike** | Daily cost > 2x average | HIGH | Slack + Email |

---

## Alert Suppression

Prevent alert spam with cooldown periods:

```bash
# Default: 1 hour cooldown, max 20 alerts/day
# Configure in database or code
```

### How It Works

1. First alert for "budget_threshold" is sent
2. Same alert type suppressed for 60 minutes
3. Counter resets if not suppressed

This prevents duplicate alerts while allowing new alert types through.

---

## Troubleshooting

### Slack Alerts Not Received

**Check webhook URL:**
```bash
curl -X POST \
  -H 'Content-type: application/json' \
  --data '{"text":"Test from PyCostAudit"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**Should see:**
- ✅ "ok" response
- ✅ Message in Slack channel

**If 404 error:**
- Webhook URL is incorrect
- Generate new webhook in Slack settings

### Email Alerts Not Received

**Check SMTP credentials:**
```bash
# Test connection
python -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your_email@gmail.com', 'your_app_password')
    print('✅ SMTP connection OK')
except Exception as e:
    print(f'❌ {e}')
"
```

**Common issues:**
- App password (not Gmail password) required for Gmail
- 2FA must be enabled on Gmail
- SMTP port wrong (587 for TLS, 465 for SSL)
- Credentials in environment variables

### SMS Not Sending

**Prerequisites:**
```bash
# All three required
echo $TWILIO_ACCOUNT_SID
echo $TWILIO_AUTH_TOKEN  
echo $TWILIO_PHONE_NUMBER
```

**SMS only triggers on CRITICAL alerts** (budget exceeded by >10%)

To test: Trigger a critical alert with cost > 90% of budget

---

## Integration with Backend Service

Alerts automatically trigger when costs are tracked:

```python
from pycostaudit.backend_service import BackendService

service = BackendService()
service.initialize()

# Track a cost - automatically checks alerts
cost = service.track_cost(
    user_id="user123",
    call_data={"model": "claude-3-5-sonnet"},
    response_data={"usage": {"prompt_tokens": 1000, "completion_tokens": 100}}
)

# Manually check budget
alerts = service.backend_service._check_alert_triggers("user123", cost)
```

---

## API Reference

### AlertsService Methods

```python
from pycostaudit.alerts_service import AlertsService

# Evaluate budget and trigger alerts
alerts = service.evaluate_budget(
    user_id="user123",
    current_cost=75.0,
    period="daily"  # daily, weekly, monthly
)

# Get alert history
history = service.get_alert_history(
    user_id="user123",
    limit=50,
    alert_type="budget_threshold"
)

# Get statistics
stats = service.get_alert_stats(
    user_id="user123",
    days=7
)

# Acknowledge alert
success = service.acknowledge_alert(alert_id="...")
```

---

## Best Practices

✅ **Set realistic budgets** - Account for your actual usage patterns
✅ **Enable multiple channels** - Slack for realtime, Email for backup
✅ **Review history weekly** - Spot trends before they become issues  
✅ **Adjust thresholds** - Start at 75%/90%, refine based on needs
✅ **Test alerts** - Run `check` command to verify setup

---

## Examples

### Startup Team ($5k/month budget)

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id ops@startup.com \
  --daily 167 \
  --weekly 833 \
  --monthly 5000 \
  --slack-webhook https://hooks.slack.com/... \
  --email ops@startup.com \
  --notify-at 0.80
```

### Solo Developer ($100/month budget)

```bash
python -m pycostaudit.alerts_cli set_budget \
  --user-id dev@example.com \
  --daily 3.33 \
  --monthly 100 \
  --email dev@example.com \
  --notify-at 0.75
```

### Enterprise (Multi-department)

```bash
# Finance team alerts
python -m pycostaudit.alerts_cli set_budget \
  --user-id finance@company.com \
  --monthly 50000 \
  --slack-webhook https://hooks.slack.com/... \
  --sms +1234567890 \
  --notify-at 0.85

# Engineering team alerts  
python -m pycostaudit.alerts_cli set_budget \
  --user-id eng@company.com \
  --daily 500 \
  --weekly 3000 \
  --monthly 15000 \
  --slack-webhook https://hooks.slack.com/...
```

---

## FAQ

**Q: How often are alerts checked?**
A: Alerts are evaluated every time a cost is tracked (real-time). Manual check via CLI anytime.

**Q: Can I disable alerts temporarily?**
A: Yes, set configuration `enabled=false` in database or wait for cooldown period.

**Q: What if I change my budget mid-period?**
A: New budget applies immediately for threshold calculations.

**Q: Can I export alert history?**
A: Yes, `get_alert_history()` returns JSON-serializable objects.

---

## Support

- GitHub Issues: https://github.com/Mullassery/PyCostAudit/issues
- Documentation: https://github.com/Mullassery/PyCostAudit#readme
