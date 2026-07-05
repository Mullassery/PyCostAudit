# ClaudeBeacon Roadmap

## Understanding Claude Code Integration

### How Claude Code Actually Works
1. **Session Context** — Claude maintains state within a session (can reference previous messages)
2. **Tool Execution** — Claude calls tools/commands to interact with codebase
3. **Session Boundary** — Context is LOST when session closes (biggest pain point)
4. **MCP Protocol** — Model Context Protocol allows external tools to extend Claude
5. **Hooks System** — Pre/post-commit hooks can enforce behaviors (but has 190+ gaps)

### Market Gaps We're Solving
| Gap | Impact | User Segment | Timeline |
|-----|--------|--------------|----------|
| **Session memory loss** | 100% of users re-explain codebase each session | Everyone | MVP |
| **No observability** | Enterprise can't audit/debug Claude decisions | Enterprise | Phase 2 |
| **Token waste** | Users don't know what costs tokens | Cost-conscious | Phase 1 |
| **Repeated mistakes** | Claude makes same errors across sessions | All | Phase 1 |
| **No context hints** | Claude doesn't automatically use CLAUDE.md | Power users | MVP |

---

## Phase 1: MVP (Weeks 1-2) — Memory + Token Visibility

### Goal
Get users to see Claude remembering their codebase + understand token costs

### Features

#### 1.1 Auto-Load CLAUDE.md on Session Start
**Why:** Users already write CLAUDE.md; Claude ignores it
**What:**
- Hook into Claude Code's session initialization
- Auto-inject CLAUDE.md context at start of session
- Display summary: "Loaded: 15KB context from CLAUDE.md"

**Impact:** ⭐⭐⭐⭐ (Quick win, immediately useful)

**Implementation:**
```rust
// beacon-core/src/memory.rs
pub fn load_claude_md() -> Result<ProjectContext> {
    let path = Path::new("CLAUDE.md");
    let content = std::fs::read_to_string(path)?;
    Ok(ProjectContext::from_markdown(&content))
}
```

```python
# python/__init__.py
class Beacon:
    def auto_load(self) -> Dict:
        """Auto-load CLAUDE.md on session start"""
        context = self._core.load_claude_md()
        self.save_memory(context)
        return {"status": "loaded", "size_kb": len(context)}
```

#### 1.2 Session Context Persistence
**Why:** Each session, Claude starts fresh even if it just finished work
**What:**
- Save session summary at end of session
- Retrieve + inject at start of next session
- Keep last 5 sessions (user can pick which to load)

**Impact:** ⭐⭐⭐⭐⭐ (Solves #1 pain point)

**Implementation:**
```rust
// beacon-core/src/memory.rs
pub async fn save_session(&mut self, session: SessionContext) -> Result<()> {
    // Summarize current session (keep important bits, drop noise)
    let summary = session.summarize(max_tokens: 500);
    
    // Store with timestamp + auto-load flag
    self.storage.insert("sessions", &SessionRecord {
        id: uuid(),
        timestamp: now(),
        summary: summary,
        files_modified: session.files_modified,
        decisions: session.key_decisions,
    }).await
}
```

#### 1.3 Token Counter + Cost Estimator
**Why:** Users have no idea what costs tokens; observability leads to optimization
**What:**
- Track every tool call + token usage
- Show: "Last Claude action used 2,450 tokens ($0.12)"
- Daily/weekly breakdown
- Cost by tool type (file reads vs AI calls)

**Impact:** ⭐⭐⭐⭐ (Data-driven optimization)

**Implementation:**
```rust
// beacon-core/src/observability.rs
pub struct TokenUsage {
    tool_call: String,
    tokens_used: i32,
    cost_usd: f32,
    timestamp: DateTime,
}

pub async fn log_token_usage(&mut self, usage: TokenUsage) -> Result<()> {
    self.storage.insert("token_usage", &usage).await
}

pub async fn get_cost_summary(&self, period: Duration) -> Result<CostBreakdown> {
    // Returns: {"reads": $0.05, "ai_calls": $0.35, "total": $0.40}
}
```

**MVP Deliverables:**
- ✅ Auto-load CLAUDE.md
- ✅ Session memory persistence (5 sessions)
- ✅ Token counter + daily cost report
- ✅ Python API to query all above
- ✅ Basic CLI: `beacon observe --cost`

**Success Metrics:**
- Users save codebase context to disk
- Users understand token costs
- Positive GitHub feedback (target: 50 stars)

---

## Phase 2: Observability (Weeks 3-4) — See What Claude Does

### Goal
Give users visibility into Claude's decisions + prevent common mistakes

### Features

#### 2.1 Tool Call Tracing
**Why:** Users can't debug if Claude makes wrong API call or edits wrong file
**What:**
- Log every tool call: name, arguments, response, latency
- Show decision tree: "Why did Claude call this tool?"
- Visual timeline of session

**Impact:** ⭐⭐⭐⭐ (Debug/audit)

**Implementation:**
```rust
// beacon-core/src/observability.rs
pub struct ToolCall {
    tool_name: String,
    args: serde_json::Value,
    response: serde_json::Value,
    latency_ms: i32,
    tokens_used: i32,
    status: ToolStatus, // success, error, timeout
}

pub async fn trace_tool_call(&mut self, call: ToolCall) -> Result<()> {
    self.storage.insert("tool_calls", &call).await
}
```

#### 2.2 Error Prevention Hooks
**Why:** Claude makes predictable mistakes (e.g., overwriting production files)
**What:**
- Hooks to catch dangerous operations before they happen
- Smart defaults: "Don't run migrations without confirmation"
- Suggest safer alternatives

**Impact:** ⭐⭐⭐⭐⭐ (Prevents data loss)

**Implementation:**
```rust
// beacon-core/src/mcp.rs
pub async fn should_allow_operation(&self, op: Operation) -> Result<bool> {
    match op {
        Operation::DeleteFile(path) if path.contains("production") => Ok(false),
        Operation::RunScript(script) if script.contains("rm -rf") => {
            self.audit.warn("Dangerous operation attempted");
            Ok(false)
        }
        _ => Ok(true),
    }
}
```

#### 2.3 Audit Logging (Compliance-Ready)
**Why:** Enterprises need immutable records of what Claude did
**What:**
- Every action logged: who, what, when, outcome
- Immutable append-only (can't be deleted)
- Export to PDF for compliance audits
- Optional encryption + retention policies

**Impact:** ⭐⭐⭐ (Enterprise feature, high revenue potential)

**Implementation:**
```rust
// beacon-core/src/audit.rs
pub struct AuditEvent {
    timestamp: DateTime,
    user: String,
    action: String,
    resource: String,
    outcome: AuditOutcome,
    context: serde_json::Value,
}

pub async fn log_event(&mut self, event: AuditEvent) -> Result<()> {
    // Write to append-only log (SQLite journal mode)
    self.storage.append_immutable("audit_log", &event).await
}
```

**Phase 2 Deliverables:**
- ✅ Tool call tracing + timeline visualization
- ✅ Error prevention hooks (10 critical rules)
- ✅ Immutable audit logging
- ✅ Compliance report export (PDF)
- ✅ Enterprise dashboard

**Success Metrics:**
- Target: 500+ stars (now solving real problems)
- Enterprise customers starting to evaluate

---

## Phase 3: Proactive Assistance (Weeks 5-6) — Claude Gets Smarter

### Goal
Claude learns from history and makes better decisions next time

### Features

#### 3.1 Decision History + Patterns
**Why:** Claude repeats mistakes if it doesn't know they were mistakes
**What:**
- Track Claude's decisions + outcomes
- "You tried this approach 3 times; it failed each time"
- Suggest alternative approaches based on history

**Impact:** ⭐⭐⭐ (Quality improvement)

#### 3.2 Code Quality Enforcement
**Why:** Claude doesn't know project's coding standards
**What:**
- Auto-check: linting, formatting, tests
- Suggest fixes before committing
- Learn project conventions from git history

**Impact:** ⭐⭐⭐⭐ (Prevents code review cycles)

#### 3.3 Git Integration
**Why:** Users want to see what Claude changed + approve before committing
**What:**
- Pre-commit review: show diff + ask for approval
- Commit message suggestions based on changes
- Track which commits were "Claude-generated"

**Impact:** ⭐⭐⭐⭐ (Clear accountability)

---

## Phase 4: Enterprise Features (Week 7+) — Monetize

### Features
- Multi-user session sharing (team context)
- PostgreSQL backend (multi-tenant)
- API for programmatic access
- Webhook notifications
- Custom hooks marketplace

### Revenue Model
- Free tier: Single-user, SQLite
- Pro: Teams, PostgreSQL, audit logs ($20/month)
- Enterprise: Custom hooks, compliance reporting, SLA

---

## Technical Prioritization

### Must Do (MVP)
1. Auto-load CLAUDE.md ← Start here (easiest, highest impact)
2. Session memory persistence
3. Token counter + cost breakdown
4. Basic observability (tool call logging)

### Should Do (Phase 2)
1. Error prevention hooks (5-10 critical rules)
2. Audit logging (immutable records)
3. Decision history tracking

### Nice To Have (Phase 3+)
1. Code quality enforcement
2. Git integration
3. AI-powered suggestions

---

## Claude Code Integration Strategy

### How ClaudeBeacon Integrates

```
User in Claude Code:
    ↓
"@beacon observe"  ← Claude Code skill/command
    ↓
Python API (claude_beacon.Beacon)
    ↓
Rust Core (PyO3 binding)
    ↓
SQLite with observability data
    ↓
Returns: Tool calls, tokens, recommendations
```

### Why This Wins

1. **No external dependencies** — Runs locally in Claude Code
2. **Zero latency** — Rust performance + Python convenience
3. **Privacy** — Data stays on user's machine
4. **Compliance** — No cloud = no regulatory issues
5. **Viral potential** — Solves real pain point (like caveman)

---

## Getting to First 1000 Stars

### Week 1-2: MVP Launch
- Share on Reddit r/ClaudeCode
- Tweet with comparison to competitors
- Show before/after (Claude forgetting vs remembering)
- Target: 100 stars

### Week 3-4: Phase 2 Launch
- Add "This prevented X data loss incidents" testimonials
- Enterprise compliance features
- Target: 500 stars

### Week 5+: Community
- Showcase user stories
- Feature marketplace for custom hooks
- Build integrations (GitHub, Slack, etc.)
- Target: 1000+ stars

---

## Implementation Order

```
WEEK 1
├── Auto-load CLAUDE.md
├── Session persistence (save/load)
└── Token counter

WEEK 2
├── Observability tracker (tool calls)
├── Cost breakdown
└── CLI: beacon observe

WEEK 3
├── Error prevention hooks
├── Audit logging
└── Compliance reports

WEEK 4+
├── Decision history
├── Code quality checks
└── Git integration
```

---

## Success Criteria

| Milestone | Target | Timeline |
|-----------|--------|----------|
| MVP complete | 3 GitHub stars (friends) | Week 2 |
| Core features complete | 50 stars | Week 3 |
| Enterprise ready | 200 stars | Week 4 |
| Community adoption | 500+ stars | Week 5 |
| Production use | 1000+ stars | Week 6 |

