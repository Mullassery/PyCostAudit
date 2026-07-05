# 🚀 PyCostAudit Quick Start (5 minutes)

## Step 1: Install the Skill (30 seconds)
```bash
bash /Users/georgimullassery/PyCostAudit/install-skill.sh
source ~/.zshrc
```

## Step 2: View Your Costs (15 seconds)
```bash
cost-audit report
```

You'll see:
- 💰 Total cost today
- 📊 Breakdown by operation
- 📈 Weekly/monthly forecast

## Step 3: Try a Manual Track (10 seconds)
```bash
cost-audit track "my_operation" 2000 500
cost-audit report
```

See the cost update in real-time!

## Step 4: Check Forecast (5 seconds)
```bash
cost-audit forecast
```

## Step 5: Monitor Alerts (Optional)
```bash
cost-audit alerts
```

---

## 📊 What You Get

### Today (2026-07-06)
```
Total Cost:        $0.6562
Operations:        12
Tokens:            24,350
Avg Cost/Op:       $0.0547

Top Operations:
• code_review             $0.1050 (16.0%)
• browser_extension_setup $0.0750 (11.4%)
• code_generation         $0.0675 (10.3%)
```

### Weekly Forecast
```
Daily Average:     $0.6563
Weekly Forecast:   $4.59
Monthly Forecast:  $19.69
```

---

## 🔄 Automatic Tracking

The skill **automatically tracks** all your Claude Code operations:
- ✅ File edits → tracked
- ✅ Code writes → tracked  
- ✅ Bash commands → tracked
- ✅ File reads → tracked

No manual setup needed after installation!

---

## 💡 Common Commands

| Command | Purpose |
|---------|---------|
| `cost-audit report` | Show today's costs |
| `cost-audit forecast` | Weekly/monthly estimate |
| `cost-audit track <op> <in> <out>` | Manually track operation |
| `cost-audit alerts` | Check budget alerts |

---

## 🎯 Next Steps

- 📱 Try the **CLI Monitor**: `python3 pycostaudit_monitor.py`
- 🌐 Install **Browser Extension** in Chrome
- 📊 Deploy **Web Dashboard**: `docker-compose up`

---

## ❓ Troubleshooting

**"command not found: cost-audit"**
```bash
source ~/.zshrc  # Reload shell
```

**"No operations showing"**
```bash
cost-audit track "test" 1000 500  # Manual track to verify
```

**"Wrong cost?"**
Check pricing model in SKILL_GUIDE.md

---

## 📖 Full Documentation

See: `SKILL_GUIDE.md` for complete reference
