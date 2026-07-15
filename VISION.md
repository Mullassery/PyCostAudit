# PyTokenCalc v0.7 — Product Vision & Scope

**One thing, done perfectly: Unified token counting across 20+ LLM providers.**

---

## Core Mission

PyTokenCalc solves a single, critical problem in multi-provider LLM development:

> **Developers need ONE unified API to count tokens accurately across all LLM providers, without writing provider-specific integration code.**

### The Problem We Solve

1. **Token counting fragmentation**: Each LLM provider has a different tokenizer
   - OpenAI: tiktoken (public library)
   - Claude: API-only (no public tokenizer)
   - Gemini: API-only (proprietary)
   - Llama/Mistral: HuggingFace transformers (1000+ models)
   - Groq/DeepInfra: Model-specific, varies by provider

2. **Developer burden**: Integrate 10+ libraries and APIs manually
   - No unified interface
   - No intelligent routing (when to use local vs API)
   - No caching → expensive API calls
   - Different error handling per provider

### Our Solution

**PyTokenCalc provides:**
- ✅ **Unified API**: One function for all 20+ providers
- ✅ **Smart routing**: Local fast tokenizers + cached API calls
- ✅ **Accurate counts**: 99%+ match vs official token counts
- ✅ **Zero configuration**: Works out of the box
- ✅ **Extensible**: Easy to add new tokenizers

---

## What PyTokenCalc IS

✅ **A Python library for:**
- Token counting (local + cached API)
- Batch operations
- Optional caching (in-memory + persistence)

✅ **Goals:**
- Single, clean API across all providers
- 99%+ accuracy vs official token counts
- <100ms latency (cached) for token counting
- Zero external service dependencies
- Minimal dependencies (pydantic only)

✅ **Supported:**
- 20+ cloud LLM APIs (Anthropic, OpenAI, Google, Mistral, etc.)
- 10+ open-source inference APIs (Groq, DeepInfra, Together, etc.)
- Python 3.9+
- All operating systems

---

## What PyTokenCalc is NOT

❌ **NOT intelligence/analytics** → Use OpenAnchor for this
  - Does not explain WHY tokens were consumed
  - Does not detect patterns or trends
  - Does not provide attribution (system prompt vs user input)
  - Does not recommend optimizations

❌ **NOT financial calculation** → Belongs in separate projects
  - Does not calculate costs (user provides pricing)
  - Does not track budgets
  - Does not generate reports/exports

❌ **NOT usage tracking/history** → Belongs in separate projects
  - Does not aggregate usage over time
  - Does not store historical data
  - Does not detect anomalies

❌ **NOT optimization/recommendations** → Use OpenAnchor for this
  - Does not suggest model changes
  - Does not recommend cost reductions
  - Does not perform A/B testing

❌ **NOT a service** → Pure library
  - No REST API server
  - No database server
  - No message queue or async workers

❌ **NOT monitoring/alerting** → Belongs in separate projects
  - No real-time dashboards
  - No notifications or integrations
  - No metrics collection or distributed tracing

---

## Scope Boundaries (LOCKED)

### STRICTLY IN-SCOPE (v0.7+)

#### Phase 1: Token Counting (✅ DONE)
- ✅ OpenAI: tiktoken (local)
- ✅ Llama/Mistral: HuggingFace transformers (local)
- ✅ Caching: In-memory LRU + optional persistence
- ✅ Vision: Placeholder (v0.8+)

#### Phase 2: Cloud API Integration (🚧 PLANNED v0.8)
- 🔜 Anthropic: Claude API token counting
- 🔜 Google: Gemini API token counting
- 🔜 Aggressive caching (reduce API calls 70-80%)

#### Phase 3: Vision/Multimodal (🚧 PLANNED v0.9)
- 🔜 Image token counting (Claude, GPT-4V, Gemini)
- 🔜 PDF token counting
- 🔜 Vision-specific accuracy improvements

### ⛔ STRICTLY OUT-OF-SCOPE (Will Not Implement)

❌ **Financial/analytics features** (belong in separate projects)
- Financial calculations
- Provider rate management
- Usage aggregation
- Budget enforcement
- Reports/exports

❌ **Services & Backends**
- REST API server
- Database server
- Message queue
- Scheduled jobs/cron
- Async workers

❌ **Monitoring & Alerting**
- Real-time dashboards
- Notifications
- Integrations (Slack, email, SMS)
- Metrics collection
- Distributed tracing

❌ **Advanced Features**
- ML-based token prediction
- Anomaly detection
- Optimization recommendations
- Model selection algorithms

---

## Design Principles

### 1. Single Responsibility
PyTokenCalc does ONE thing: count tokens accurately.
All other features → separate projects or user code.

### 2. Zero External Dependencies
- Core: only `pydantic` (data validation)
- Optional: `tiktoken`, `transformers` (for local tokenizers)
- NO service dependencies (no SMTP, Slack, databases, etc.)

### 3. Configurability Over Features
Let users extend PyTokenCalc rather than bloating the core:
- Custom tokenizers: subclass `TokenCounter`
- Custom caching: use `TokenCounterCache` API

### 4. Pure Library Mentality
- No global state (except singletons for config)
- No side effects (no writing logs, no connecting to services)
- No implicit behavior (explicit APIs only)
- User controls everything (threading, async, batching)

### 5. Name-Based Scope
- **Name**: PyTokenCalc ("Python Token Calculator")
- **Scope**: Count tokens. That's it.
- No financial calculation, no analytics, no optimization
- If the feature doesn't align with the name, it doesn't belong

---

## Relationship: PyTokenCalc ↔ OpenAnchor

### Deployment Models

**PyTokenCalc Standalone (Token Counting Only):**
```
Your Application
    ↓
PyTokenCalc (counts tokens via API or local cache)
    ├─ Provides accurate token counts
    ├─ Maintains database for token reconciliation
    └─ Handles provider switching
```

**PyTokenCalc + OpenAnchor (Integrated):**
```
Your Application
    ↓
OpenAnchor Middleware (analyzes and enriches)
    ├─ Calls PyTokenCalc for accurate counts
    ├─ Writes enrichments to PyTokenCalc's database
    └─ Provides intelligence & recommendations
    ↓
PyTokenCalc Database (single shared instance)
├─ token_events (PyTokenCalc: raw counts)
├─ token_attribution (OpenAnchor: 6D breakdown)
├─ pattern_detections (OpenAnchor: anomalies, trends)
├─ recommendations (OpenAnchor: optimizations)
└─ ... (OpenAnchor enrichment tables)
```

### Database Responsibility

**PyTokenCalc owns and maintains the database:**
- Creates and manages all storage infrastructure
- Stores token events (the source of truth)
- Handles reconciliation via repeated API calls if needed
- Works standalone (OpenAnchor is OPTIONAL)
- Can optionally provide database connection to OpenAnchor

**OpenAnchor enriches PyTokenCalc's database:**
- Reads from `token_events` (PyTokenCalc's table)
- Writes analysis tables (attribution, patterns, recommendations)
- Does NOT create or manage the database
- REQUIRES PyTokenCalc to be installed
- Cannot work without PyTokenCalc

### What PyTokenCalc Provides to OpenAnchor
PyTokenCalc is the **source of truth** for all token counts:
- **Total input token count** (exact number, NO breakdown by component)
- **Total output token count** (exact number, NO breakdown by component)
- **By modality breakdown** (text tokens, image tokens, etc - automatic)
- Model and provider metadata
- Timestamp and context (user_id, session_id, etc)
- **Database access** (when OpenAnchor needs to enrich data)

**CRITICAL:** PyTokenCalc provides TOTALS ONLY.  
OpenAnchor breaks down those totals by component (system prompt, user input, context, etc).

Example:
- PyTokenCalc returns: `{input_tokens: 3200, output_tokens: 450}`
- OpenAnchor analyzes: "3200 = 500 system + 1200 user + 1000 history + 500 overhead"

OpenAnchor consumes these totals and transforms them into intelligence.

### What PyTokenCalc Does NOT Do (OpenAnchor Responsibility)
❌ Explain WHY tokens were consumed (OpenAnchor's job)
❌ Detect patterns or anomalies (OpenAnchor's job)
❌ Provide attribution breakdown (OpenAnchor's job)
❌ Generate recommendations (OpenAnchor's job)
❌ Integrate with observability platforms (OpenAnchor's job)

---

## Related But Separate Projects

These features belong in separate projects that *use* PyTokenCalc:

| Feature | Who Does It | Notes |
|---------|---------|--------|
| **Token intelligence** | **OpenAnchor** | Attribution, patterns, recommendations |
| Attribution (why tokens) | **OpenAnchor** | Not in PyTokenCalc scope |
| Pattern detection | **OpenAnchor** | Not in PyTokenCalc scope |
| Trend analysis | **OpenAnchor** | Not in PyTokenCalc scope |
| Optimization recommendations | **OpenAnchor** | Not in PyTokenCalc scope |
| Observability integration | **OpenAnchor** | Not in PyTokenCalc scope |
| Model optimization | User code | Builds on PyTokenCalc's counts |
| Financial analysis | User code | Use token counts with pricing data |
| Usage tracking | User code | Aggregate counts over time |
| Dashboard/UI | Separate project | Not in PyTokenCalc scope |
| Forecasting ML | Separate project | Not in PyTokenCalc scope |

---

## Roadmap: What's Next (v0.8 - v1.0)

### v0.8: Cloud API Integration
- Anthropic: `messages.count_tokens()` API
- Google: Gemini token counting API
- Aggressive caching: 70-80% fewer API calls

### v0.9: Vision/Multimodal
- Image token counting for Claude, GPT-4V, Gemini
- PDF token counting
- Vision accuracy improvements

### v1.0: Production Hardened
- 100% test coverage
- Performance benchmarks
- Comprehensive documentation

### Post-v1.0: Maintenance Mode
- Bug fixes
- Performance improvements
- Add new provider support as needed
- Stability and reliability focus

---

## Conclusion

**PyTokenCalc is a focused, stable, production-grade token counting library for multi-provider LLM development.**

Everything else (financial analysis, optimization, tracking) is someone else's responsibility.

This keeps us sharp, reliable, and valuable.

---

*Last updated: 2026-07-15*
*Maintainer: Georgi Mammen Mullassery*
*Repository: https://github.com/Mullassery/PyTokenCalc*
