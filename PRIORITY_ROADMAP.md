# PyCostAudit Priority Roadmap

**Current Status:** v0.7.0 - Claude Code integration framework complete  
**Checkpoint:** Local repo with real Claude Code history integration

---

## 🎯 Immediate Priorities (Next 2 Weeks)

### P0: Core Cost Calculations (CRITICAL)
**Why:** Analyses currently show placeholder "[Analysis would run here]"  
**Impact:** Makes PyCostAudit actually useful for real cost tracking

- [ ] **P0.1** Implement real cost calculation engine
  - Read actual Claude Code API pricing (Anthropic rates)
  - Calculate costs from token usage patterns in history
  - Support multiple models (Sonnet, Haiku, Opus)
  - Store calculations in local SQLite

- [ ] **P0.2** Wire up "Detect anomalies" (Option #4)
  - Use real project costs from P0.1
  - Identify spending spikes per project
  - Show which days/sessions were expensive
  - Compare to project baseline

- [ ] **P0.3** Wire up "Which projects cost most?" (Option #3)
  - Show real cost breakdown by project
  - Statguard vs ClusterAudienceKit vs PrismNote costs
  - Current month, last 30 days options
  - Most valuable for your immediate use

---

### P1: Project-Specific Cost Data (HIGH)
**Why:** You work on 6 projects - need to see which drain budget  
**Impact:** Direct answer to "where does my money go?"

- [ ] **P1.1** Calculate cost per project (from real data)
  - StatGuard: total cost + cost per session
  - ClusterAudienceKit: cost trend over time
  - All 6 projects tracked individually
  - Store in SQLite for historical comparison

- [ ] **P1.2** Wire up "90-day forecast" (Option #10)
  - Use actual StatGuard/PrismNote/etc costs
  - Project them forward by project
  - Warn if any project trending upward
  - Suggest which to optimize first

- [ ] **P1.3** Wire up "Personalized recommendations" (Option #6)
  - Analyze YOUR specific usage patterns
  - "You use StatGuard heavily (55 sessions)"
  - "Could save $X by switching to Haiku for certain tasks"
  - Real ROI calculations per recommendation

---

### P2: Most-Used Analyses First (HIGH)
**Why:** Start with what's most valuable, not all 34 at once  
**Impact:** Users get immediate value, discover other options later

Implement in this order (by typical value):

1. **Option #4: Detect anomalies** ← Most urgent
   - Find cost spikes
   - Alert on unusual patterns
   
2. **Option #3: Which projects cost most?** ← Most valuable
   - Per-project breakdown
   - Identify optimization targets

3. **Option #6: Personalized recommendations** ← Most actionable
   - Based on YOUR usage
   - ROI-ranked suggestions

4. **Option #20: Set monthly budget** ← Most protective
   - Lock in spending limit
   - Track burn rate

5. **Option #10: 90-day forecast** ← Most planning
   - Quarterly projection
   - What-if scenarios

Leave others (#7-34) as "framework ready" for later.

---

## 📊 Medium Term (Weeks 3-4)

### P3: Real Data Backend Integration
- [ ] Connect to Anthropic API for real token usage
- [ ] Implement multi-provider support (AWS Bedrock, Azure, GCP)
- [ ] Real-time cost tracking vs. retroactive analysis
- [ ] API authentication + secure credential storage

### P4: Reporting & Export
- [ ] Wire up "Weekly report" (Option #11) - use reportlab
- [ ] Wire up "Export to Slack" (Option #13) - Slack webhook
- [ ] Wire up "Email reports" (Option #14) - SMTP
- [ ] PDF/Excel export with real data

### P5: Persistence & History
- [ ] Store cost calculations in SQLite (already in schema)
- [ ] Build historical trends (compare week-to-week)
- [ ] Enable "show last 30 days average" patterns
- [ ] Audit trail for compliance

---

## 🏢 Later (Weeks 5+)

### P6: Enterprise Features (From Task #8-10)
- [ ] Task #8: Multi-org support + department tracking
- [ ] Task #9: SOC 2/HIPAA/GDPR compliance audit system
- [ ] Task #10: OpenTelemetry export (Prometheus/Datadog)
- [ ] Task #7: Advanced filtering with 12 operators

These are valuable but can wait until core analyses work.

---

## 🔧 Technical Dependencies

### Required for P0-P1:
- SQLite database ready ✅ (already in schema)
- User context loading ✅ (reading history correctly)
- Project detection ✅ (6 projects detected)
- Interactive CLI ✅ (routing to analyses)

### Needed to implement:
- Anthropic pricing model (rates for different models)
- Token counter logic (estimate from history)
- Cost calculation formulas
- Trend analysis (anomaly detection algorithm)
- Recommendation engine (ROI ranking)

---

## 📈 Success Metrics

### By end of P0:
- [ ] User runs "4" (anomalies) → sees real cost anomalies in YOUR projects
- [ ] User runs "3" (projects) → sees actual breakdown (StatGuard: $X, PrismNote: $Y)
- [ ] User runs "6" (recommendations) → gets real ROI suggestions for YOUR usage

### By end of P1:
- [ ] User sees project trends ("StatGuard costs increasing")
- [ ] User sees forecasts ("You'll spend $X next month")
- [ ] User gets actionable advice ("Switch StatGuard to Haiku: save $Y/month")

### By end of P2:
- [ ] Most used analyses are fully functional
- [ ] Users can export reports (PDF/Slack/Email)
- [ ] Historical data shows value (trends over time)

---

## 🚀 Implementation Order (Do in This Sequence)

**Week 1:**
1. Implement cost calculation engine (P0.1)
2. Wire up anomaly detection (P0.2)
3. Wire up project costs (P1.1)
4. Test with YOUR real data

**Week 2:**
1. Wire up forecasting (P1.2)
2. Wire up recommendations (P1.3)
3. Implement other top-5 analyses
4. Test all together

**Week 3-4:**
1. Add reporting (P4)
2. Add history tracking (P5)
3. Add real Anthropic API (P3)
4. Polish UI/UX

**Week 5+:**
1. Enterprise features (P6)
2. Advanced features (P6)
3. Performance optimization
4. Production hardening

---

## 💡 Key Principle

**Real data only. No dummy results.**

Every analysis should use ACTUAL data from:
- Your Claude Code history ✅ (1,142 sessions loaded)
- Your project patterns ✅ (6 projects detected)
- Your usage trends (NEW - implement in P0-P1)

Test with YOUR real usage, not simulated data.

---

## 📝 Local Testing Checklist

Before marking any priority complete:

- [ ] Test with real data from ~/.claude/history.jsonl
- [ ] Verify results make sense for YOUR projects
- [ ] Check that options are shown after analysis
- [ ] Verify no dead ends in workflow
- [ ] Run multiple analyses in sequence
- [ ] Test error cases

---

## ⏱️ Estimated Timeline

| Phase | Tasks | Effort | Timeline |
|-------|-------|--------|----------|
| **P0** | Core calculations | 8-12 hours | Week 1 |
| **P1** | Project data | 6-8 hours | Week 1-2 |
| **P2** | Top 5 analyses | 12-16 hours | Week 2 |
| **P3** | Real APIs | 6-10 hours | Week 3-4 |
| **P4** | Reporting | 8-12 hours | Week 3-4 |
| **P5** | Persistence | 4-6 hours | Week 4 |
| **P6** | Enterprise | 20-30 hours | Week 5+ |

**Total to "production ready":** ~50-70 hours of development

---

## 🎯 End Goal

After all priorities complete:

```
User installs PyCostAudit
        ↓
Loads their Claude Code history
        ↓
Shows: "You spent $X on StatGuard, $Y on PrismNote"
        ↓
Suggests: "Anomalies detected in StatGuard - save $Z"
        ↓
User clicks option → sees detailed breakdown
        ↓
Gets recommendation → "Switch to Haiku, save 30%"
        ↓
Sets budget → "Alert if any project exceeds limit"
        ↓
Exports report → Shares with team
```

**All with REAL data. All in Claude Code terminal. No dead ends.**

---

**Start with P0 - that's where the immediate value is.**
