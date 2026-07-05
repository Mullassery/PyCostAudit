# PyCostAudit Dual Monitoring Guide
## Complete Setup & Usage for Skill + CLI Monitor

---

## ✅ Setup Status

```
✅ Claude Code Skill installed
   Location: ~/.local/bin/cost-audit
   
✅ CLI Monitor configured
   Location: ~/.local/bin/cost-monitor
   
✅ Configuration files created
   Location: ~/.config/pycostaudit/
   
✅ Shared data source
   Location: ~/.pycostaudit/skill_data.json
   
✅ Command aliases configured
   Location: ~/.zshrc / ~/.bashrc
```

---

## 🎯 Quick Start (30 seconds)

### 1. Reload Shell
```bash
source ~/.zshrc
```

### 2. View Your Costs
```bash
cost-report
```

### 3. Start Real-Time Monitoring
```bash
cost-monitor
```

---

## 📊 Complete Command Reference

### Skill Commands (On-Demand)

| Command | Purpose | Example |
|---------|---------|---------|
| `cost-report` | View today's costs | `cost-report` |
| `cost-forecast` | Weekly/monthly forecast | `cost-forecast` |
| `cost-track <op> <in> <out>` | Track operation | `cost-track "debugging" 2000 500` |
| `cost-quick <op>` | Quick track (defaults) | `cost-quick "testing"` |
| `cost-alerts` | Check budget alerts | `cost-alerts` |

### Monitor Commands (Real-Time)

| Command | Purpose | Options |
|---------|---------|---------|
| `cost-monitor` | Start dashboard | `--refresh 2` (1-5 seconds) |
| `cost-dashboard` | Both skill + monitor | N/A |

### Aliases Available

```bash
cost-report              # cost-audit report
cost-forecast            # cost-audit forecast
cost-track              # cost-audit track
cost-alerts             # cost-audit alerts
cost-monitor            # Start real-time monitor
cost-dashboard          # Start both together
cost-quick <op>         # Quick track operation
```

---

## 🔄 Typical Workflows

### Workflow 1: Daily Cost Check

**Morning (2 minutes)**
```bash
# Start day by checking progress
cost-report

# Output shows:
# Total Cost: $1.1587
# Operations: 20
# Weekly Forecast: $8.11
```

**During Day (Continuous)**
```bash
# Start monitor in separate terminal
cost-monitor
# Watches costs continuously, updates every 2 seconds
```

**End of Day (1 minute)**
```bash
# Final check
cost-report
# Compare to morning report
# See cost increase for the day
```

---

### Workflow 2: Monitor Expensive Operation

**Setup**
```bash
# Terminal 1: Start monitoring
cost-monitor

# Terminal 2: Check starting cost
cost-report
```

**Work**
```bash
# Do your expensive operation
# Watch Terminal 1 for cost updates in real-time
# Understand impact immediately
```

**Analysis**
```bash
# Terminal 2: Track the operation manually
cost-track "expensive_refactor" 5000 1500

# See cost breakdown
cost-report
```

---

### Workflow 3: Budget Tracking

**Setup**
```bash
# Start continuous monitoring
cost-monitor

# In another terminal, check alerts
cost-alerts
```

**Monitor**
```bash
# Monitor watches all operations
# Alerts show budget status
# Know when you're approaching limits
```

**Control**
```bash
# When near budget:
cost-forecast
# Plan rest of budget allocation
```

---

### Workflow 4: Session Analysis

**Session Start**
```bash
# Record baseline
cost-report > ~/before.txt

# Start monitoring
cost-monitor &
MONITOR_PID=$!
```

**Session Work**
```bash
# Do all your work
# Monitor updates continuously
# Track specific expensive ops
cost-track "complex_operation" 3000 800
```

**Session End**
```bash
# Stop monitoring
kill $MONITOR_PID

# Compare before/after
cost-report > ~/after.txt
diff ~/before.txt ~/after.txt
```

---

## 💻 Using Both Simultaneously

### Terminal Setup (Recommended)

**Terminal 1: Skill Commands**
```bash
# Use for on-demand reports
cost-report
cost-forecast
cost-track "operation" 2000 500
cost-alerts
# ... quick commands ...
```

**Terminal 2: Monitor**
```bash
# Start monitor once, leave running
cost-monitor
# Auto-updates every 2 seconds
# Shows trends in real-time
```

**Result**: Perfect combination!
- Real-time updates in Terminal 2
- On-demand reports in Terminal 1
- Both reading same data source

---

### Multi-Monitor Setup

```bash
# Terminal 1: Fast refresh (1 second)
cost-monitor --refresh 1
```

```bash
# Terminal 2: Slow refresh (5 seconds)
cost-monitor --refresh 5
```

```bash
# Terminal 3: Skill commands
cost-report
cost-track "operation" 2000 500
```

Use whichever dashboard refresh rate you prefer!

---

## 📈 Data Sharing

Both Skill and Monitor read/write to the same data file:

```
~/.pycostaudit/skill_data.json
```

This means:
- ✅ Track in Skill → Monitor shows instantly
- ✅ Monitor sees updates → Skill reflects them
- ✅ No data conflicts
- ✅ Single source of truth

---

## 🎓 Advanced Usage

### Auto-Track Operations

The skill has hooks configured in `.claude/settings.json` to automatically track Claude Code operations:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|Bash|Read",
        "hooks": [...]
      }
    ]
  }
}
```

This means:
- ✅ Every Edit tracked automatically
- ✅ Every Write tracked automatically
- ✅ Bash commands tracked
- ✅ File reads tracked
- ✅ All reflected in Monitor in real-time

### Custom Quick Track

Create your own operation:
```bash
cost-quick "my_operation"
# Uses default: 1000 input, 250 output tokens
```

Or track with custom tokens:
```bash
cost-track "my_operation" 2000 500
```

### Batch Operations

Track multiple operations:
```bash
cost-track "op1" 1000 250
cost-track "op2" 1500 400
cost-track "op3" 2000 500

# Monitor shows all three aggregated
cost-report
```

### Budget Management

Check if you're on budget:
```bash
cost-alerts
```

Shows:
- Daily budget status
- Weekly trajectory
- Monthly forecast
- Any threshold breaches

### Forecast Planning

```bash
cost-forecast
# Shows: Daily avg, Weekly est, Monthly est

# Plan your work:
# If monthly forecast is high, reduce scope
# If daily average is low, you have room
```

---

## 🔧 Configuration

### Edit Configuration

```bash
nano ~/.config/pycostaudit/config.json
```

Options:
- `default_refresh`: Monitor refresh rate (2-5 seconds)
- `daily_budget`: Daily limit ($50 default)
- `show_sparklines`: ASCII trends (true/false)
- `color_output`: Colored text (true/false)

### Change Pricing Model

Edit `pycostaudit_skill.py`:
```python
# Line 64-65
input_cost = (tokens_input / 1_000_000) * 15.00   # Change this
output_cost = (tokens_output / 1_000_000) * 75.00  # And this
```

Current pricing (Claude Opus 4.8):
- Input: $15.00 per 1M tokens
- Output: $75.00 per 1M tokens

---

## 📊 What You See

### Skill Report
```
📊 PyCostAudit - Claude Code Cost Tracking

📈 TODAY'S COSTS (2026-07-06)
  Total Cost:        $1.1587
  Operations:        20
  Tokens:            43,450
  Avg Cost/Op:       $0.0579

📂 Cost by Operation:
  • api_integration          $  0.1650 ( 14.2%)
  • optimization             $  0.1410 ( 12.2%)
  ...

🤖 Cost by Model:
  • claude-opus-4-8          $  1.1587 (100.0%)

📅 Weekly Forecast:
  Daily Average:     $1.1588
  Weekly Forecast:   $8.11
  Monthly Forecast:  $34.76
```

### Monitor Dashboard
```
💰 PYCOSTAUDIT CLI MONITOR
════════════════════════════════════════

📈 TODAY'S OVERVIEW
├─ Total Cost:      $    1.1587
├─ Operations:              20
├─ Tokens Used:         43,450
└─ Avg Cost/Op:     $    0.0579

📂 Cost by Operation (Top 5):
  api_integration      $  0.1650  14.2% ███████
  optimization         $  0.1410  12.2% ██████
  ...

📈 Weekly Forecast:
  Daily Average:     $    1.1588
  Weekly Forecast:   $      8.11
  Monthly Forecast:  $     34.76

⏱️  Last Updated: 02:13:09 | Next refresh: 2s
```

---

## 📁 File Structure

```
~/.pycostaudit/
├── skill_data.json           # Shared data store
├── pycostaudit.db            # SQLite backup

~/.local/bin/
├── cost-audit                # Skill symlink
├── cost-monitor              # Monitor launcher
└── cost-audit-dashboard      # Parallel launcher

~/.config/pycostaudit/
├── config.json               # Settings
└── quick-reference.txt       # Command reference

~/.local/share/pycostaudit/
└── activity.log              # Activity log
```

---

## 🚨 Troubleshooting

### Commands not found
```bash
# Reload shell
source ~/.zshrc

# Or verify PATH
echo $PATH | grep .local/bin

# Or use full path
python3 /Users/georgimullassery/PyCostAudit/pycostaudit_skill.py report
```

### Monitor not updating
```bash
# Restart monitor
pkill -f cost-monitor
cost-monitor

# Or check data file
cat ~/.pycostaudit/skill_data.json
```

### Wrong costs shown
```bash
# Verify configuration
cat ~/.config/pycostaudit/config.json

# Check pricing in skill
grep -n "15.00\|75.00" /Users/georgimullassery/PyCostAudit/pycostaudit_skill.py
```

### Data not persisting
```bash
# Check permissions
ls -la ~/.pycostaudit/
ls -la ~/.config/pycostaudit/

# Verify write access
touch ~/.pycostaudit/test.txt
```

---

## 🎯 Best Practices

1. **Always reload shell after setup**
   ```bash
   source ~/.zshrc
   ```

2. **Keep Monitor running during work**
   ```bash
   cost-monitor &
   ```

3. **Check alerts before expensive ops**
   ```bash
   cost-alerts
   ```

4. **Use quick-track for manual ops**
   ```bash
   cost-quick "operation_name"
   ```

5. **Review forecast at end of week**
   ```bash
   cost-forecast
   ```

6. **Archive reports periodically**
   ```bash
   cost-report > ~/reports/$(date +%Y-%m-%d).txt
   ```

---

## 🔄 Typical Daily Schedule

```
09:00 AM  cost-report                 # Morning check
09:05 AM  cost-monitor &              # Start monitoring
          ... work during day ...
12:00 PM  cost-report                 # Mid-day review
          ... more work ...
05:00 PM  cost-alerts                 # Check budget status
05:30 PM  cost-forecast               # Weekly outlook
06:00 PM  cost-report                 # Final report
          # Compare to 09:00 AM report
```

---

## ✅ Verification Checklist

- [x] Commands installed: `cost-audit`, `cost-monitor`
- [x] Aliases configured: `cost-report`, `cost-forecast`, etc.
- [x] Data file exists: `~/.pycostaudit/skill_data.json`
- [x] Config created: `~/.config/pycostaudit/config.json`
- [x] Logging enabled: `~/.local/share/pycostaudit/activity.log`
- [x] Shell reloaded: `source ~/.zshrc`
- [x] Commands tested: Both Skill and Monitor working

---

## 🚀 Next Steps

1. ✅ Use Skill for quick checks: `cost-report`
2. ✅ Use Monitor for continuous tracking: `cost-monitor`
3. ⬜ Try Browser Extension for web-based tracking
4. ⬜ Deploy FastAPI backend for team dashboards
5. ⬜ Set up custom budget alerts
6. ⬜ Create automated reports

---

## 📞 Quick Reference

**View costs right now:**
```bash
cost-report
```

**Watch costs live:**
```bash
cost-monitor
```

**Plan your budget:**
```bash
cost-forecast
```

**Track an operation:**
```bash
cost-track "operation" 2000 500
```

**Check alerts:**
```bash
cost-alerts
```

---

That's it! You now have complete real-time cost monitoring for your Claude Code work. 🎉

Questions? See `SKILL_GUIDE.md` or `INTEGRATION_COMPARISON.md` for more details.
