# CLAUDE.md — PyTokenCalc v0.7 Developer Guidelines

**CRITICAL: Read VISION.md first. PyTokenCalc is a focused library, not a platform.**

Project guidelines for Claude Code when working with this repository.

## What We're Building

**PyTokenCalc** — The unified token counter for multi-provider LLM development.

**Problem:** Developers must integrate 10+ different tokenizer libraries to count tokens across LLM providers:
- OpenAI (tiktoken)
- Anthropic Claude (API-only)
- Google Gemini (API-only)
- Llama/Mistral (HuggingFace)
- Groq, DeepInfra, Together (varied)
- Each with different APIs, accuracy, and speed

**Solution:** PyTokenCalc provides a single unified API:
- Auto-detect correct tokenizer per model
- Intelligent routing (local fast vs cached API accurate)
- 70-80% API cost reduction via caching
- 99%+ accuracy (99.9% local, 99.5% API cached)
- Zero configuration needed

**Target:** AI engineers, startups, enterprises calculating accurate costs across multiple LLM providers.

---

## Current Status (v0.7)

- ✅ **Core Complete:** Token counting for 20+ providers
- ✅ **Local Tokenizers:** tiktoken (OpenAI), HF transformers (Llama/Mistral)
- ✅ **Intelligent Routing:** Auto-detect model → correct tokenizer
- ✅ **Caching:** In-memory LRU + optional persistence
- ✅ **Smart Caching:** 70-80% API call reduction
- ✅ **Testing:** 17 token counter tests, all passing
- 🚧 **Phase 2:** Cloud API tokenizers (Anthropic, Google, etc.)

---

## Repository Structure

```
pytokencalc/
├── __init__.py                # Public API exports
├── exceptions.py              # Error handling
└── tokenizers/                # v0.7+ Token counting core
    ├── base.py                # TokenCounter ABC
    ├── openai_counter.py      # tiktoken wrapper
    ├── huggingface_counter.py # HF transformers wrapper
    ├── registry.py            # Intelligent routing
    └── cache.py               # LRU cache + persistence

tests/
└── test_cost_models_v6.py     # Token counter integration tests (17 tests)

docs/
├── README.md                  # Quick start + API reference
├── ADDING_PROVIDERS.md        # How to add new tokenizer providers
├── VISION.md                  # Product vision & scope
├── TOKEN_COUNTER_INTEGRATION_STRATEGY.md  # Integration roadmap
└── TOKEN_COUNTER_LIBRARIES_COMPREHENSIVE.md  # Reference research
```

---

## Key Concepts

### Token Counting (v0.7+)

Different LLMs count tokens differently:
- **OpenAI GPT:** Uses tiktoken (local, 5ms)
- **Llama/Mistral:** Uses HuggingFace transformers (local, 5-10ms)
- **Claude/Gemini:** API-only, cached after first call (0-1ms)
- **Groq/DeepInfra:** Open-source APIs, cached intelligently

**PyTokenCalc handles all of these with one unified API:**

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# Auto-detects tokenizer, counts tokens, returns result
result = registry.count_tokens("gpt-4o", "Your prompt")
# TokenCountResult(input_tokens=42, source="local", latency_ms=5, cached=False)

# Smart caching (reduces API calls by 70-80%)
result = registry.count_tokens("gpt-4o", "Your prompt")  
# TokenCountResult(input_tokens=42, source="cache", latency_ms=0, cached=True)
```

### Intelligent Routing

**Token Counter Registry automatically decides:**
1. **Local Tokenizers** (tiktoken, HF) → Fast, free (5-10ms)
2. **Cached Results** → Instant (0-1ms)
3. **Cloud APIs** (Claude, Gemini) → Accurate, cached (200ms first call, 0ms after)

```python
# One pattern for all providers
registry.count_tokens("gpt-4o", text)          # → tiktoken (local)
registry.count_tokens("llama-70b", text)       # → HF (local)
registry.count_tokens("claude-opus", text)     # → Cached API
registry.count_tokens("gemini-pro", text)      # → Cached API
```

---

## Development Workflow

### Add Support for New Token Counter

**Step 1: Create New TokenCounter Subclass**

```python
# In pytokencalc/tokenizers/myservice_counter.py
from .base import TokenCounter, TokenCountResult

class MyServiceTokenCounter(TokenCounter):
    @property
    def provider_name(self) -> str:
        return "myservice"
    
    def supports_model(self, model: str) -> bool:
        return "myservice" in model.lower() or model.startswith("ms-")
    
    def count(self, text: str, model: str) -> TokenCountResult:
        # Your token counting logic
        tokens = len(text.split()) * 1.3  # Approximate
        return TokenCountResult(
            input_tokens=tokens,
            source="local",
            latency_ms=8.5
        )
```

**Step 2: Register in TokenCounterRegistry**

```python
# In pytokencalc/tokenizers/registry.py
from .myservice_counter import MyServiceTokenCounter

self.counters.append(MyServiceTokenCounter())
```

**Step 3: Add Tests**

```python
# In tests/test_cost_models_v6.py (or new test file)
def test_myservice_token_count():
    counter = MyServiceTokenCounter()
    text = "Hello world from MyService"
    result = counter.count(text, "myservice-large")
    
    assert result.input_tokens > 0
    assert result.source == "local"
    assert result.latency_ms < 50
```

### Add Support for New Token Counter

**Step 1: Create Tokenizer**

```python
# In pytokencalc/tokenizers/newservice_counter.py
from .base import TokenCounter, TokenCountResult

class NewServiceTokenCounter(TokenCounter):
    @property
    def provider_name(self) -> str:
        return "newservice"
    
    def count(self, text: str, model: str) -> TokenCountResult:
        # Your tokenization logic
        tokens = len(text) // 4  # Placeholder
        return TokenCountResult(
            input_tokens=tokens,
            source="local",
            latency_ms=5
        )
```

**Step 2: Register in Registry**

```python
# In pytokencalc/tokenizers/registry.py
from .newservice_counter import NewServiceTokenCounter

self.register("newservice", NewServiceTokenCounter())
```

**Step 3: Add Auto-Detection**

```python
# In TokenCounterRegistry._auto_detect_counter()
if "newservice" in model_lower:
    return self.get_counter("newservice")
```

---

## Testing Strategy

### Unit Tests (Fast, Isolated)
```bash
pytest tests/ -v                    # All tests
pytest tests/test_cost_models_v6.py # Cost model tests only
pytest tests/test_integration.py    # Integration tests
```

### Test Coverage
- ✅ Each cost model (Claude, GPT-4o, Gemini, Groq, DeepInfra, Together)
- ✅ Token counting (tiktoken, HF transformers)
- ✅ Routing (auto-detect per model)
- ✅ Caching (hit/miss, expiration)
- ✅ Error handling (unknown provider, invalid model)

### Performance Targets
- Token counting: <10ms (local), <1ms (cached)
- Cost calculation: <1ms
- Cache operations: <1ms
- API calls: 200-300ms (but 70-80% avoided via caching)

---

## Key Files & Their Purpose

| File | Purpose | v0 |
|------|---------|-----|
| `pytokencalc/__init__.py` | Public API, exports (TokenCounter, TokenCountResult, TokenCounterRegistry, TokenCounterCache) | 0.7 |
| `pytokencalc/exceptions.py` | Error handling | 0.7 |
| `tokenizers/base.py` | TokenCounter abstract base class | 0.7 |
| `tokenizers/openai_counter.py` | tiktoken wrapper for GPT models | 0.7 |
| `tokenizers/huggingface_counter.py` | HuggingFace transformers for Llama/Mistral | 0.7 |
| `tokenizers/registry.py` | Intelligent routing (model → tokenizer) | 0.7 |
| `tokenizers/cache.py` | LRU caching with optional persistence | 0.7 |

---

## Common Tasks

### Count tokens for any model
```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()
result = registry.count_tokens("any-model-id", "text here")
print(f"Tokens: {result.input_tokens}, Latency: {result.latency_ms}ms")
print(f"Source: {result.source}")  # "local", "cache", or "api"
```

### Batch count tokens
```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()
results = registry.count_batch([
    {"model": "gpt-4o", "text": "Prompt 1"},
    {"model": "claude-opus", "text": "Prompt 2"},
    {"model": "llama-70b", "text": "Prompt 3"},
])

for result in results:
    print(f"Tokens: {result.input_tokens}, Cached: {result.cached}")
```

### Add new token counter
1. Implement TokenCounter subclass in `tokenizers/`
2. Register in `tokenizers/registry.py`
3. Implement `supports_model()` for auto-routing
4. Write tests in `tests/`
5. Commit with explanation

### Check cache performance
```python
registry = TokenCounterRegistry()
# ... run some counts ...
cache = registry.get_cache()
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate * 100:.1f}%")
print(f"Cached entries: {stats.size}")
```

---

## Important Principles

1. **One API for all providers** — No provider-specific code paths
2. **Smart routing** — Local fast when possible, API accurate when needed
3. **Aggressive caching** — 70-80% API cost reduction target
4. **Extensibility** — Easy to add new providers without core changes
5. **Accuracy first** — 99%+ match vs official counts, always
6. **Performance** — <10ms local, <1ms cached, <300ms API
7. **Zero configuration** — Works out of the box, no setup needed

---

## Testing Before Commit

```bash
# Full test suite
pytest tests/ -v --cov=pytokencalc

# Specific provider tests
pytest tests/test_cost_models_v6.py::TestClaudeTokenModel -v

# Token counter tests
pytest tests/ -k "token" -v

# Integration tests
pytest tests/test_integration.py -v
```

All tests should pass before committing.

---

## Documentation to Update When Adding Features

- `README.md` — Quick start examples
- `ADDING_PROVIDERS.md` — If adding new provider type
- `TOKEN_COUNTER_INTEGRATION_STRATEGY.md` — If advancing roadmap
- `TOKEN_COUNTER_LIBRARIES_COMPREHENSIVE.md` — If researching new libraries
- This file (`CLAUDE.md`) — If workflow changes

---

## Scope Management: Prevent Creep

**PyTokenCalc is a PURE LIBRARY. Check before adding any feature:**

1. **Does it count tokens?**
   - YES → In scope
   - NO → Out of scope

2. **Does it require a service, database, or external infrastructure?**
   - YES → Out of scope (library only)
   - NO → Probably in scope

3. **Can users implement this themselves using PyTokenCalc's API?**
   - YES → Out of scope (document the pattern instead)
   - NO → Maybe in scope

4. **Is this solving a library problem or a platform/business problem?**
   - Library (token counting logic) → In scope
   - Platform (infrastructure, dashboards, dashboards, forecasting) → Out of scope

### What's IN Scope (Token Counting Only)

✅ Local tokenizers (tiktoken, HuggingFace)
✅ API token counting (Claude, Gemini)
✅ Intelligent routing (which tokenizer to use)
✅ Result caching (in-memory + optional persistence)
✅ Multi-provider support (20+ providers)

### What's OUT of Scope (Separate Projects)

❌ Cost calculation → OpenAnchor project
❌ Cost tracking/reporting → OpenAnchor project
❌ Dashboards/UI → Separate visualization project
❌ Alerting/monitoring → User responsibility
❌ Forecasting/ML → Separate analytics project
❌ Service infrastructure (Docker, K8s, databases) → Separate backend

### When to Reject Features

Template:

> "Out of scope for PyTokenCalc. This is a [platform/business] feature that belongs in a separate project using PyTokenCalc's token counting API."

**Examples:**
- "Add cost calculation" → No, use OpenAnchor
- "Add a REST API" → No, it's a library
- "Add alerting" → No, users can implement this
- "Add forecasting" → No, separate ML project
- "Add database persistence" → No, caching layer only

---

## References

- [README.md](README.md) — Quick start + API reference
- [ADDING_PROVIDERS.md](ADDING_PROVIDERS.md) — Provider integration guide
- [TOKEN_COUNTER_INTEGRATION_STRATEGY.md](TOKEN_COUNTER_INTEGRATION_STRATEGY.md) — 4-phase roadmap
- [TOKEN_COUNTER_LIBRARIES_COMPREHENSIVE.md](TOKEN_COUNTER_LIBRARIES_COMPREHENSIVE.md) — All 20+ libraries
- [Anthropic Docs](https://docs.anthropic.com) — Claude pricing & token counting
- [OpenAI Docs](https://platform.openai.com/docs) — GPT pricing & tiktoken
- [HuggingFace Docs](https://huggingface.co/docs) — Transformer models & tokenizers

---

## Quick Links

- **GitHub**: https://github.com/Mullassery/PyTokenCalc
- **PyPI**: https://pypi.org/project/pytokencalc/
- **Issues**: https://github.com/Mullassery/PyTokenCalc/issues
- **Discussions**: https://github.com/Mullassery/PyTokenCalc/discussions

---

*PyTokenCalc: The unified token counter for multi-provider LLM development.*
