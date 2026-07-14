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

❌ **NOT cost calculation**: Cost calculation belongs in OpenAnchor
❌ **NOT cost tracking**: Tracking costs over time is OpenAnchor's job
❌ **NOT cost optimization**: Choosing cheaper models is OpenAnchor's job
❌ **NOT a service**: No backend, no web API, no database server
❌ **NOT a dashboard/UI**: Pure Python library for programmatic access
❌ **NOT budget enforcement**: No alerting, no notifications, no integrations
❌ **NOT forecasting**: No ML predictions, no anomaly detection

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

❌ **Cost-related features** (all belong in OpenAnchor or user code)
- Cost calculation/pricing
- Provider pricing management
- Cost tracking or aggregation
- Budget enforcement
- Cost reports/exports

❌ **Services & Backends**
- REST API server
- Database server
- Message queue
- Scheduled jobs/cron
- Async workers

❌ **Monitoring & Alerting**
- Real-time dashboards
- Cost alerts
- Notification integrations (Slack, email, SMS)
- Metrics collection
- Distributed tracing

❌ **Advanced Features**
- ML-based token prediction
- Anomaly detection
- Cost optimization recommendations
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
- **No cost calculation, no cost tracking, no cost optimization**
- If the feature doesn't align with the name, it doesn't belong

---

## Related But Separate Projects

These features belong in separate projects that *use* PyTokenCalc:

| Feature | Project | Status |
|---------|---------|--------|
| Cost optimization | [OpenAnchor](https://github.com/Mullassery/openanchor) | Active |
| Cost calculation | OpenAnchor | Active |
| Cost tracking | OpenAnchor | Active |
| Dashboard/UI | Future project | Planned |
| Forecasting ML | Future project | Planned |

---

## Roadmap: What's Next (v0.8 - v1.0)

### v0.8: Cloud API Integration
- Anthropic: `messages.count_tokens()` API
- Google: Gemini token counting API
- Aggressive caching: 70-80% API call reduction

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

Everything else (cost calculation, optimization, tracking) is someone else's responsibility.

This keeps us sharp, reliable, and valuable.

---

*Last updated: 2026-07-15*
*Maintainer: Georgi Mammen Mullassery*
*Repository: https://github.com/Mullassery/PyTokenCalc*
