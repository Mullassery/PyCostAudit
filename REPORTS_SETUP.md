# PyCostAudit Automated Reports - Setup Guide

Generate and deliver daily/weekly cost reports with HTML emails and trend analysis.

## Features

- ✅ **Daily Reports** - Cost breakdown, budget status, 7-day trend
- ✅ **Weekly Reports** - Aggregated costs, daily chart, top operations
- ✅ **HTML Emails** - Beautiful formatted reports with charts
- ✅ **Recommendations** - Actionable optimization suggestions
- ✅ **Budget Tracking** - Visual progress bars and alerts
- ✅ **Scheduled Delivery** - GitHub Actions or APScheduler

---

## Quick Start (3 minutes)

### 1. Configure SMTP

Set email credentials:

```bash
export PYCOSTAUDIT_SMTP_HOST=smtp.gmail.com
export PYCOSTAUDIT_SMTP_PORT=587
export PYCOSTAUDIT_SMTP_USER=your_email@gmail.com
export PYCOSTAUDIT_SMTP_PASSWORD=your_app_password
export PYCOSTAUDIT_FROM_EMAIL=your_email@gmail.com
```

### 2. Generate Daily Report

```bash
python -m pycostaudit.reports_cli daily \
  --user-id your_email@example.com \
  --email your_email@example.com
```

### 3. Generate Weekly Report

```bash
python -m pycostaudit.reports_cli weekly \
  --user-id your_email@example.com \
  --email your_email@example.com
```

---

## Setup Guide

### Email Configuration

#### Gmail (Recommended)

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security
   - Enable "2-Step Verification"

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or your OS)
   - Copy the generated 16-character password

3. **Set Environment Variables**

```bash
export PYCOSTAUDIT_SMTP_HOST=smtp.gmail.com
export PYCOSTAUDIT_SMTP_PORT=587
export PYCOSTAUDIT_SMTP_USER=your_email@gmail.com
export PYCOSTAUDIT_SMTP_PASSWORD=xxxx xxxx xxxx xxxx
export PYCOSTAUDIT_FROM_EMAIL=your_email@gmail.com
```

#### SendGrid (Alternative)

```bash
export PYCOSTAUDIT_SMTP_HOST=smtp.sendgrid.net
export PYCOSTAUDIT_SMTP_PORT=587
export PYCOSTAUDIT_SMTP_USER=apikey
export PYCOSTAUDIT_SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxx
export PYCOSTAUDIT_FROM_EMAIL=noreply@yourdomain.com
```

#### Custom SMTP Server

```bash
export PYCOSTAUDIT_SMTP_HOST=mail.yourserver.com
export PYCOSTAUDIT_SMTP_PORT=587
export PYCOSTAUDIT_SMTP_USER=username
export PYCOSTAUDIT_SMTP_PASSWORD=password
export PYCOSTAUDIT_FROM_EMAIL=reports@yourserver.com
```

### Test Email Configuration

```bash
python -m pycostaudit.reports_cli daily \
  --user-id user123 \
  --email test@example.com \
  --preview
```

Output:
```
📧 HTML Report Preview:
============================================================
<html>
    <body style="...">
        <!-- Report HTML -->
============================================================
Total size: 12345 bytes
```

---

## Usage

### Generate Daily Report

```bash
python -m pycostaudit.reports_cli daily --user-id user123
```

Output:
```
📊 Daily Report
============================================================
Date: 2026-07-06
Cost: $45.23
Operations: 42

Top Operations:
  File Read: $25.00
  Api Call: $15.00
  Browser Op: $5.23

Budget: 45.2% used ($45.23/$100.00)
```

### Generate Daily Report (Send Email)

```bash
python -m pycostaudit.reports_cli daily \
  --user-id user123 \
  --email user@example.com
```

Output:
```
✅ Report sent to user@example.com
```

### Generate Weekly Report

```bash
python -m pycostaudit.reports_cli weekly --user-id user123
```

Output:
```
📊 Weekly Report
============================================================
Period: 2026-06-29 to 2026-07-06
Total Cost: $287.45
Daily Average: $41.06
Operations: 287

Top Operations:
  File Read: $156.00
  Api Call: $89.00
  Browser Op: $42.45

Trend: UP 12.3%

Budget: 57.5% used ($287.45/$500.00)
```

### Preview Report HTML

```bash
python -m pycostaudit.reports_cli daily \
  --user-id user123 \
  --preview
```

Shows first 500 characters of HTML and total size.

### Specific Date

```bash
python -m pycostaudit.reports_cli daily \
  --user-id user123 \
  --date 2026-07-05 \
  --email user@example.com
```

---

## Scheduling

### Option 1: GitHub Actions (Recommended)

Create `.github/workflows/daily-report.yml`:

```yaml
name: Daily PyCostAudit Report
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - run: pip install pycostaudit
      
      - run: python -m pycostaudit.reports_cli daily --user-id ${{ secrets.USER_ID }} --email ${{ secrets.EMAIL }}
        env:
          PYCOSTAUDIT_SMTP_HOST: ${{ secrets.SMTP_HOST }}
          PYCOSTAUDIT_SMTP_PORT: ${{ secrets.SMTP_PORT }}
          PYCOSTAUDIT_SMTP_USER: ${{ secrets.SMTP_USER }}
          PYCOSTAUDIT_SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          PYCOSTAUDIT_FROM_EMAIL: ${{ secrets.FROM_EMAIL }}
```

Create `.github/workflows/weekly-report.yml`:

```yaml
name: Weekly PyCostAudit Report
on:
  schedule:
    - cron: '0 9 * * 1'  # 9 AM UTC every Monday

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - run: pip install pycostaudit
      
      - run: python -m pycostaudit.reports_cli weekly --user-id ${{ secrets.USER_ID }} --email ${{ secrets.EMAIL }}
        env:
          PYCOSTAUDIT_SMTP_HOST: ${{ secrets.SMTP_HOST }}
          PYCOSTAUDIT_SMTP_PORT: ${{ secrets.SMTP_PORT }}
          PYCOSTAUDIT_SMTP_USER: ${{ secrets.SMTP_USER }}
          PYCOSTAUDIT_SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          PYCOSTAUDIT_FROM_EMAIL: ${{ secrets.FROM_EMAIL }}
```

Then set secrets in GitHub:
- `USER_ID`: your_email@example.com
- `EMAIL`: your_email@example.com
- `SMTP_HOST`: smtp.gmail.com
- `SMTP_PORT`: 587
- `SMTP_USER`: your_email@gmail.com
- `SMTP_PASSWORD`: app_password
- `FROM_EMAIL`: your_email@gmail.com

### Option 2: APScheduler (Python)

```python
from apscheduler.schedulers.background import BackgroundScheduler
from pycostaudit.database import DatabaseManager
from pycostaudit.backend_service import BackendService
from pycostaudit.reports_service import ReportsService

def send_daily_report():
    db = DatabaseManager()
    db.connect()
    backend = BackendService()
    backend.initialize()
    service = ReportsService(db, backend)
    
    report = service.generate_daily_report("user123")
    service.send_report_email("user@example.com", report)
    
    db.disconnect()
    print("✅ Daily report sent")

def send_weekly_report():
    db = DatabaseManager()
    db.connect()
    backend = BackendService()
    backend.initialize()
    service = ReportsService(db, backend)
    
    report = service.generate_weekly_report("user123")
    service.send_report_email("user@example.com", report)
    
    db.disconnect()
    print("✅ Weekly report sent")

# Start scheduler
scheduler = BackgroundScheduler()

# Daily report at 9 AM UTC
scheduler.add_job(send_daily_report, 'cron', hour=9, minute=0, name='daily-report')

# Weekly report at 9 AM UTC on Monday
scheduler.add_job(send_weekly_report, 'cron', day_of_week='mon', hour=9, minute=0, name='weekly-report')

scheduler.start()

# Keep scheduler running
try:
    while True:
        pass
except KeyboardInterrupt:
    scheduler.shutdown()
```

### Option 3: Cron (Linux/macOS)

```bash
# Daily report at 9 AM
0 9 * * * python -m pycostaudit.reports_cli daily --user-id user123 --email user@example.com

# Weekly report every Monday at 9 AM
0 9 * * 1 python -m pycostaudit.reports_cli weekly --user-id user123 --email user@example.com
```

---

## Report Contents

### Daily Report

**Includes:**
- Cost spent today
- Budget status and progress bar
- Top 5 operations by cost
- 7-day trend analysis
- Optimization recommendations (if applicable)

**Example Email:**
```
PyCostAudit Daily Report

Daily Budget
Spent Today: $45.23
Budget Limit: $100.00
Budget Used: 45.2%

Cost Breakdown
File Read: $25.00
Api Call: $15.00
Browser Op: $5.23

7-Day Trend
Average daily cost: $35.50
Trend: UP 5.3%

Recommendations
💡 Consider batching file read operations
```

### Weekly Report

**Includes:**
- Total cost for the week
- Daily average cost
- 7-day chart showing daily costs
- Top operations by cost
- Weekly trend (up/down/stable)
- Budget status for the period

**Example Email:**
```
PyCostAudit Weekly Report

Weekly Total
Total Spent: $287.45
Daily Average: $41.06
Operations: 287

Daily Trend
[Chart showing 7 daily costs]

Top Operations
File Read: $156.00
Api Call: $89.00
Browser Op: $42.45

Trend: UP 12.3%

Budget: 57.5% used ($287.45/$500.00)
```

---

## Recommendations

Reports automatically generate recommendations based on:

- **High-cost operations** - Operations over $50
- **Expensive file formats** - PDF URLs (3.6x more expensive than disk)
- **Spending spikes** - When daily cost is 50%+ above average
- **Budget trends** - When spending is increasing week-over-week

---

## Troubleshooting

### Email Not Received

**Check SMTP connection:**
```bash
python -c "
import smtplib
import os

smtp_host = os.getenv('PYCOSTAUDIT_SMTP_HOST', 'smtp.gmail.com')
smtp_port = int(os.getenv('PYCOSTAUDIT_SMTP_PORT', '587'))
smtp_user = os.getenv('PYCOSTAUDIT_SMTP_USER')
smtp_password = os.getenv('PYCOSTAUDIT_SMTP_PASSWORD')

try:
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.quit()
    print('✅ SMTP connection OK')
except Exception as e:
    print(f'❌ {e}')
"
```

**Common issues:**
- App password not generated (Gmail)
- SMTP credentials incorrect
- Firewall blocking SMTP port
- Email marked as spam (add to contacts)

### Report Has No Data

**Check if data exists:**
```bash
python -c "
from pycostaudit.backend_service import BackendService

service = BackendService()
service.initialize()

summary = service.get_daily_summary('user123')
print(f'Today cost: \${summary[\"total_cost\"]:.2f}')
print(f'Operations: {summary[\"num_operations\"]}')
"
```

If both are 0, costs haven't been tracked yet.

---

## Integration with Alerts

Reports work alongside Budget Alerts:

- **Alerts**: Real-time notifications when budget thresholds hit
- **Reports**: Scheduled summaries with trend analysis and recommendations

Combine them for complete cost visibility:

```bash
# Set daily budget and alerts
python -m pycostaudit.alerts_cli set_budget \
  --user-id user123 \
  --daily 100 \
  --slack-webhook https://hooks.slack.com/...

# Schedule daily reports
0 9 * * * python -m pycostaudit.reports_cli daily --user-id user123 --email user@example.com
```

---

## Examples

### Startup Team

Daily reports at 9 AM, weekly at Monday 9 AM:

```bash
# Schedule daily
0 9 * * * python -m pycostaudit.reports_cli daily --user-id ops@startup.com --email ops@startup.com

# Schedule weekly
0 9 * * 1 python -m pycostaudit.reports_cli weekly --user-id ops@startup.com --email ops@startup.com
```

### Solo Developer

Weekly report only:

```bash
# Schedule weekly on Sunday at 5 PM
0 17 * * 0 python -m pycostaudit.reports_cli weekly --user-id dev@example.com --email dev@example.com
```

### Enterprise

Multiple teams receiving separate reports:

```bash
# Finance team - weekly on Monday
0 8 * * 1 python -m pycostaudit.reports_cli weekly --user-id finance@company.com --email finance@company.com

# Engineering team - daily
0 9 * * * python -m pycostaudit.reports_cli daily --user-id eng@company.com --email eng@company.com
```

---

## API Reference

```python
from pycostaudit.reports_service import ReportsService
from pycostaudit.database import DatabaseManager
from pycostaudit.backend_service import BackendService

db = DatabaseManager()
db.connect()
backend = BackendService()
backend.initialize()
service = ReportsService(db, backend)

# Generate daily report
report = service.generate_daily_report(user_id="user123")

# Generate weekly report
report = service.generate_weekly_report(user_id="user123")

# Render as HTML
html = service.render_html_report(report)

# Send via email
success = service.send_report_email("user@example.com", report)

db.disconnect()
```

---

## FAQ

**Q: Can I customize report format?**
A: Yes, modify `_render_daily_html()` and `_render_weekly_html()` methods in `reports_service.py`

**Q: How are recommendations calculated?**
A: See `_generate_recommendations()` method - based on cost thresholds and spending patterns

**Q: Can I send to multiple recipients?**
A: Run the CLI multiple times with different `--email` values

**Q: What timezone are reports in?**
A: UTC (all timestamps in UTC, adjust cron time accordingly)

**Q: Can I export reports as PDF?**
A: Install `weasyprint` and modify `render_html_report()` to generate PDF

---

## Support

- GitHub Issues: https://github.com/Mullassery/PyCostAudit/issues
- Documentation: https://github.com/Mullassery/PyCostAudit#readme
