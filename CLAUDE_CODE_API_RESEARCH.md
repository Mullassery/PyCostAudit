# Claude Code API Research & Deep Integration Opportunities

**Goal:** Discover how to integrate PyCostAudit deeply into Claude Code for seamless cost tracking

---

## 📊 Current Integration Status

✅ **What We Have:**
- Read `~/.claude/history.jsonl` for session history
- Detect user's active projects
- Display options in terminal
- Interactive navigation

❌ **What We're Missing:**
- Real-time cost tracking during sessions
- Integration into Claude Code's native UI
- Webhook/callback system for cost events
- Direct API for Claude Code settings
- Native status line integration

---

## 🔍 Claude Code Architecture

### What We Know From History File

The `~/.claude/history.jsonl` contains:
```json
{
  "display": "User's query/task",
  "pastedContents": {},
  "timestamp": 1781460678093,
  "project": "/Users/georgimullassery/PyCostAudit",
  "sessionId": "uuid"
}
```

**Missing from history file:**
- Token counts (input/output)
- Model used (Claude 3.5 Sonnet, Haiku, etc.)
- Cost per session
- Tool invocations (file reads, executions, etc.)
- Exact prompt/response tokens

### What Claude Code Could Provide

If Claude Code exposed APIs:
1. **Real-time cost data:**
   - Actual tokens used per request
   - Model selection (Sonnet vs Haiku)
   - Time of day (for rate calculations)

2. **Event webhooks:**
   - On session start: collect starting metrics
   - On session end: log final costs
   - On tool use: track operation costs

3. **Status line integration:**
   - Show running cost: "💰 $0.23 today"
   - Show monthly total: "📊 $14.22 this month"
   - Show anomaly alerts: "🚨 Cost spike detected"

4. **Configuration API:**
   - Set budget limits
   - Choose cost tracking preferences
   - Select notification channels

---

## 🚀 Potential Deep Integration Points

### 1. **Claude Code Status Bar**
```
Current: [No integration]

Possible:
├─ Show cost badge: "💰 $0.24 | 2h 15m"
├─ Show project focus: "StatGuard | 55 sessions"
├─ Show budget status: "Budget: 67% used"
└─ Click for: Quick cost analysis
```

**Implementation:**
- Need status line API access
- Real-time cost calculation
- Minute-by-minute tracking

### 2. **Claude Code Skill/Plugin**
```
Current: Could work as CLI tool

Possible:
├─ Run as Claude Code native skill
├─ Get API token from Claude Code
├─ Access: /v1/usage endpoint directly
├─ Real costs, not estimates
└─ Show results in side panel
```

**Would require:**
- Claude Code plugin SDK
- OAuth/credential pass-through
- UI component library

### 3. **Real-Time Webhooks**
```
Current: Read history after fact

Possible:
├─ On Claude API call: Webhook with tokens
├─ On operation: Track file reads, GitHub ops
├─ Immediate cost attribution
├─ Real-time anomaly alerts
└─ Instant budget warnings
```

**Would require:**
- Claude Code event system
- Webhook/callback endpoints
- Real-time message delivery

### 4. **Settings Integration**
```
Current: Static user projects

Possible:
├─ Read from Claude Code settings:
│  ├─ Selected plan (Pro/Max/Enterprise)
│  ├─ Budget preferences
│  └─ Cost tracking options
├─ Write back to settings:
│  ├─ Recommended optimizations
│  └─ Cost alerts
```

### 5. **Model Selection Visibility**
```
Current: Estimate based on prompts

Possible:
├─ Know exact model for each prompt
├─ Track Sonnet vs Haiku usage ratio
├─ Suggest automatic model switching
├─ Calculate per-model costs accurately
└─ ROI of "Sonnet for this, Haiku for that"
```

---

## 🔗 External API Possibilities

### Anthropic API Integration

**Current:**
- Pricing model hardcoded (Sonnet $3/$15 per 1M)

**Possible:**
- Call `https://api.anthropic.com/v1/usage` endpoint
  - Real usage dashboard data
  - Actual token counts
  - Historical billing data
  - Per-model cost breakdown

**Would Need:**
- User's Anthropic API key
- Permission to call usage endpoint
- OAuth flow in Claude Code

**Implementation Complexity:** Medium
- Hit Anthropic Usage API
- Cache results (avoid rate limits)
- Show real costs vs estimates

---

## 💡 Recommended Integration Roadmap

### Phase 1: Deepen Current Integration (Next)
**What:** Extract more from what we have
- Parse more data from history entries
- Better project/tool detection
- Conversation flow tracking
- Build predictive models

**Effort:** 2-4 hours

### Phase 2: Add Real Cost Data (Soon)
**What:** Connect to actual cost sources
- Call Anthropic Usage API with user key
- Real token counts
- Accurate model attribution
- Historical trend data from API

**Effort:** 6-10 hours
**Prerequisite:** Claude Code credential system

### Phase 3: Status Bar Integration (Later)
**What:** Native Claude Code UI
- Show cost badge in status bar
- Real-time updates
- Click for quick analysis
- Alert on anomalies

**Effort:** 8-15 hours
**Prerequisite:** Claude Code plugin SDK

### Phase 4: Full Plugin System (Future)
**What:** Native Claude Code skill
- Dedicated UI panel
- Settings integration
- Webhook system
- Scheduled reports

**Effort:** 20-40 hours
**Prerequisite:** Claude Code plugin documentation

---

## 🔍 What Would Unlock Better Integration

### 1. Claude Code History File Enhancement
**If extended to include:**
- `tokens_used`: {input: X, output: Y}
- `model_used`: "claude-3-5-sonnet"
- `cost_usd`: 0.0123
- `tool_calls`: [{type, cost}, ...]

**Impact:** 100% accurate costs, no estimation needed

### 2. Claude Code Webhook System
**If available:**
- `onSessionStart`: Signal to track
- `onSessionEnd`: Finalize costs
- `onToolInvoke`: Atomic operation tracking
- `onError`: Error cost tracking

**Impact:** Real-time cost tracking, instant anomaly detection

### 3. Claude Code Plugin API
**If available:**
- Access to settings panel
- Real-time status updates
- Native UI components
- Credential management

**Impact:** Seamless user experience, no terminal needed

### 4. Anthropic Usage API Access
**If exposed in Claude Code:**
- Automatic usage retrieval
- No user key needed
- Historical data access
- Accurate billing

**Impact:** Real costs, not estimates; full accuracy

---

## 🎯 Current Best Practices (Without APIs)

Given current constraints, optimize by:

1. **Better history parsing:**
   - Detect more signal from display text
   - Infer complexity from prompt length
   - Track conversation patterns
   - Build ML model for token estimation

2. **Hybrid approach:**
   - User provides API key optionally
   - Use real costs if available
   - Fall back to estimates if not
   - Store and learn from both

3. **Local optimization:**
   - Store full session context
   - Track all operations
   - Build time-series analysis
   - Enable local anomaly detection

4. **Integration readiness:**
   - Design for plugin API (when available)
   - Structure code for webhooks (when available)
   - Modular so it works standalone or integrated
   - No hard dependencies on external APIs

---

## 📝 Next Steps to Improve Integration

### Immediate (This Week)
1. **Add user API key support (optional)**
   - Let users provide Anthropic API key
   - Call actual usage endpoint
   - Compare estimates vs actual
   - Show accuracy metrics

2. **Enhance project detection**
   - Parse git repos in display text
   - Track branch names
   - Detect tool-specific patterns
   - Better operation classification

3. **Build cost estimation accuracy**
   - ML model on token patterns
   - Calibrate with real data
   - Reduce estimation error

### Short Term (Next 2 Weeks)
4. **Design for plugin architecture**
   - Create abstraction layer for CLI/plugin
   - Prepare for status bar integration
   - Structure for webhook support
   - Plan credential management

5. **Add Anthropic Usage API integration**
   - Document how users can enable it
   - Add opt-in cost verification
   - Show comparison view

### Medium Term (Next Month)
6. **Monitor for Claude Code Plugin SDK**
   - Subscribe to Claude Code documentation
   - Prepare for status bar integration
   - Design native UI mockups

7. **Build webhook-ready system**
   - Create event system
   - Prepare for real-time cost tracking
   - Design alert architecture

---

## 🎨 UI/UX Vision (With Deeper Integration)

### Current State
```
Terminal:
$ python3 -m pycostaudit
📊 Your costs...
```

### With Status Bar
```
Claude Code Status Bar:
[Files] [Search] [Terminal] [💰 $0.23 today | 15m] [Errors]
                                     ↑ Click for breakdown
```

### With Plugin Panel
```
Claude Code Left Sidebar:
┌─ Files
├─ Search  
├─ PyCostAudit  ← New native panel
│  ├─ Today: $0.23 ✓
│  ├─ Budget: 12% used
│  ├─ Projects: 6 active
│  ├─ Anomalies: None
│  └─ Forecast: $25.09/month
└─ Extensions
```

### With Real-Time Updates
```
Live during session:
"Running code analysis... 📊 Cost: $0.07 (Sonnet)"
"Reading files... 📊 Cost: $0.002 (Haiku could save 30%)"
"Finding results... 📊 Cost: $0.03 (Total: $0.102)"
```

---

## 🔐 Privacy & Security Considerations

### If using Anthropic API key:
- Store securely (Claude Code credential system)
- Only use for read-only usage queries
- No access to prompts/completions
- Audit logging for compliance

### Local-only approach:
- All data stays local
- No external API calls
- No credential exposure
- Full user privacy

---

## Summary

**Current:** We have a working tool that reads local history and estimates costs

**Possible:** Deep integration into Claude Code with real-time tracking and status bar

**Blocked by:** 
- Claude Code plugin API not yet public
- Anthropic usage webhook system not yet exposed  
- Claude Code status bar integration API not yet available

**Recommendation:**
- Build current tool to be plugin-ready
- Document how users can enable Anthropic API integration
- Monitor for Claude Code plugin documentation
- Ship current version now, plugin version when APIs available

---

**Next:** Implement optional Anthropic API key support for real cost data
