# CLAUDE.md — PyTokenCalc v0.7

Project guidelines for Claude Code when working with this repository.

## What We're Building

**PyTokenCalc** — The unified token counter & cost calculator for multi-provider LLM development.

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

**Target:** AI engineers, startups, enterprises tracking LLM costs across multiple providers.

---

## Current Status (v0.7)

- ✅ **Core Complete:** Token counting + cost calculation
- ✅ **Local Tokenizers:** tiktoken (OpenAI), HF transformers (Llama/Mistral)
- ✅ **Intelligent Routing:** Auto-detect model → correct tokenizer
- ✅ **Caching:** In-memory LRU + persistent JSON
- ✅ **Provider Models:** Claude, GPT-4o, Gemini, Groq, DeepInfra, Together
- ✅ **Testing:** 15+ token counter tests, cost model tests
- 🚧 **Phase 2:** Cloud API tokenizers (Anthropic, Google, etc.)

---

## Repository Structure

```
pytokencalc/
├── tokenizers/                 # v0.7+ Token counting
│   ├── base.py                # TokenCounter ABC
│   ├── openai_counter.py      # tiktoken wrapper
│   ├── huggingface_counter.py # HF transformers wrapper
│   ├── registry.py            # Intelligent routing
│   └── cache.py               # LRU cache + persistence
├── cost_models.py             # v0.6+ Provider-specific cost models
├── cost_calculator.py         # v0.5+ Core cost calculation
├── cost_model.py              # Cost data structures
├── pricing_manager.py         # Multi-provider pricing
├── database.py                # SQLite storage
├── persistence.py             # State management
├── _budget_enforcement.py     # Hard cost limits
└── exceptions.py              # Error handling

tests/
├── test_cost_models_v6.py     # Provider-specific cost model tests
├── test_cost_model.py         # Legacy cost model tests
├── test_integration.py        # End-to-end integration
└── test_database_schema.py    # Database tests

docs/
├── README.md                  # Quick start + API reference
├── ADDING_PROVIDERS.md        # How to add new providers
├── TOKEN_COUNTER_INTEGRATION_STRATEGY.md  # 4-phase roadmap
└── TOKEN_COUNTER_LIBRARIES_COMPREHENSIVE.md  # All 20+ libraries analyzed
```

---

## Key Concepts

### Token Counting (v0.7+)

Different LLMs count tokens differently:
- **Claude:** Simple input/output token rates
- **GPT-4o:** Dual token model (full + mini tokens)
- **Gemini:** Character-based (not traditional tokens)
- **Groq:** Speed-tiered pricing affects effective token cost
- **Open-source:** Quantization level affects token count

**PyTokenCalc handles all of these transparently.**

```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()

# Auto-detects tokenizer, counts tokens, returns result
result = registry.count_tokens("gpt-4o", "Your prompt")
# TokenCountResult(input_tokens=42, source="local", latency_ms=5, cached=False)

# Smart caching (99% hit rate on repeated prompts)
result = registry.count_tokens("gpt-4o", "Your prompt")  
# TokenCountResult(input_tokens=42, source="cache", latency_ms=0, cached=True)
```

### Cost Calculation (v0.6+)

Each provider has unique token → cost mapping:
- **Claude:** Tokens × rate (simple)
- **GPT-4o:** Full tokens × rate1 + mini tokens × rate2 (complex)
- **Gemini:** Characters × rate (completely different)

```python
from pytokencalc import UsageData, CostCalculatorV6

calc = CostCalculatorV6()

usage = UsageData(
    provider="anthropic",
    model="claude-3-5-sonnet",
    input_tokens=1_000_000,
    output_tokens=500_000
)

cost = calc.calculate(usage)  # $10.50
```

### Intelligent Routing

**Token Counter Registry decides:**
1. Is this a local tokenizer? (tiktoken, HF) → Use it (5-10ms)
2. Is it cached? → Return cached result (0-1ms)
3. Is this a cloud API? (Claude, Gemini) → Call API (200ms) + cache

```python
# User calls same function for all providers
registry.count_tokens("gpt-4o", text)          # → tiktoken (local)
registry.count_tokens("llama-70b", text)       # → HF (local)
registry.count_tokens("claude-opus", text)     # → Cached API
registry.count_tokens("gemini-pro", text)      # → Cached API
```

---

## Development Workflow

### Add Support for New LLM Provider

**Step 1: Create Provider-Specific Cost Model**

```python
# In pytokencalc/cost_models.py
class MyProviderTokenModel(CostModel):
    PRICING = {
        "my-model-large": {"input": 0.01, "output": 0.02},
    }
    
    @property
    def provider_name(self) -> str:
        return "myprovider"
    
    def calculate(self, usage: UsageData) -> float:
        pricing = self.PRICING[usage.model]
        return (
            (usage.input_tokens * pricing["input"]) +
            (usage.output_tokens * pricing["output"])
        ) / 1_000_000
    
    def validate(self, usage: UsageData) -> bool:
        return usage.provider == "myprovider"
```

**Step 2: Register in CostModelRegistry**

```python
# In pytokencalc/cost_models.py CostModelRegistry.__init__()
self.models = {
    "myprovider": MyProviderTokenModel(),
    # ... other providers
}
```

**Step 3: Add Tests**

```python
# In tests/test_cost_models_v6.py
def test_myprovider_cost():
    model = MyProviderTokenModel()
    usage = UsageData(
        provider="myprovider",
        model="my-model-large",
        input_tokens=1_000_000,
        output_tokens=500_000
    )
    cost = model.calculate(usage)
    assert abs(cost - 0.015) < 0.001
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
| `pytokencalc/__init__.py` | Public API, exports | 0.7 |
| `tokenizers/base.py` | TokenCounter ABC | 0.7 |
| `tokenizers/openai_counter.py` | tiktoken wrapper | 0.7 |
| `tokenizers/huggingface_counter.py` | HF transformers | 0.7 |
| `tokenizers/registry.py` | Intelligent routing | 0.7 |
| `tokenizers/cache.py` | LRU cache | 0.7 |
| `cost_models.py` | Provider-specific models | 0.6 |
| `cost_calculator.py` | Core cost calculation | 0.5 |
| `cost_model.py` | Cost data structures | 0.5 |
| `pricing_manager.py` | Multi-provider pricing | 0.5 |
| `_budget_enforcement.py` | Hard cost limits | 0.5 |

---

## Common Tasks

### Count tokens for any model
```python
from pytokencalc.tokenizers import TokenCounterRegistry

registry = TokenCounterRegistry()
result = registry.count_tokens("any-model-id", "text here")
print(f"Tokens: {result.input_tokens}, Latency: {result.latency_ms}ms")
```

### Calculate cost across providers
```python
from pytokencalc import CostCalculatorV6, UsageData

calc = CostCalculatorV6()
for operation in operations:
    usage = UsageData(
        provider=operation["provider"],
        model=operation["model"],
        input_tokens=operation["input_tokens"],
        output_tokens=operation["output_tokens"]
    )
    cost = calc.calculate(usage)
    print(f"Cost: ${cost:.4f}")

# Get breakdowns
print(calc.cost_by_provider())
print(calc.cost_by_model())
```

### Add new token counter
1. Implement TokenCounter subclass
2. Register in TokenCounterRegistry
3. Add to auto_detect_counter() for auto-routing
4. Write tests
5. Commit with explanation

### Update provider pricing
1. Edit provider's PRICING dict in cost_models.py
2. Update timestamp/notes
3. Run tests to verify accuracy
4. Commit with pricing source

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
