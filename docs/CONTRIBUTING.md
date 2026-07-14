# Contributing to PyTokenCalc

Thank you for your interest in contributing to PyTokenCalc! This guide will help you understand how to contribute effectively.

## What is PyTokenCalc?

PyTokenCalc is a unified token counting library for LLM applications. It provides:
- Multi-provider token counting (OpenAI, Anthropic, Google, Llama, etc.)
- Intelligent tokenizer routing (local fast vs cached API)
- Accurate token measurement across 20+ providers

## Getting Started

### Clone and Setup

```bash
git clone https://github.com/Mullassery/PyTokenCalc.git
cd PyTokenCalc
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=pytokencalc
```

---

## What We Welcome

### Bug Reports
- Issues with token counting accuracy
- Provider integration problems
- Performance regressions
- Documentation errors

### New Features (In Scope)
- New tokenizer implementations
- Provider support
- Performance improvements
- Caching enhancements
- Testing improvements

### Documentation
- Improved examples
- Better API documentation
- Tutorials and guides
- Translation improvements

---

## What We Don't Accept

### Out of Scope
- ❌ Cost calculation features
- ❌ Financial/pricing data
- ❌ Service infrastructure (REST APIs, databases)
- ❌ Dashboard/UI components
- ❌ Billing or usage tracking

**Why?** PyTokenCalc is PURELY a token counting library. These features belong in separate projects.

---

## Adding a New Tokenizer

### Step 1: Create TokenCounter Subclass

```python
# In pytokencalc/tokenizers/myprovider_counter.py
from .base import TokenCounter, TokenCountResult

class MyProviderTokenCounter(TokenCounter):
    @property
    def provider_name(self) -> str:
        return "myprovider"

    def supports_model(self, model: str) -> bool:
        return "myprovider" in model.lower()

    def count(self, text: str, model: str) -> TokenCountResult:
        # Implement your token counting logic
        tokens = len(text.split()) * 1.3  # Example
        return TokenCountResult(
            input_tokens=tokens,
            source="local",
            latency_ms=5
        )
```

### Step 2: Register in Registry

```python
# In pytokencalc/tokenizers/registry.py
from .myprovider_counter import MyProviderTokenCounter

self.counters.append(MyProviderTokenCounter())
```

### Step 3: Add Tests

```python
# In tests/test_token_counter.py
def test_myprovider_token_count():
    counter = MyProviderTokenCounter()
    result = counter.count("test text", "myprovider-model")
    
    assert result.input_tokens > 0
    assert result.source == "local"
    assert result.latency_ms > 0
```

### Step 4: Submit PR

1. Create a feature branch: `git checkout -b feature/add-myprovider`
2. Commit changes with clear messages
3. Submit PR with test results

---

## Development Workflow

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test
pytest tests/test_token_counter.py::TestTokenCounterRegistry::test_caching_behavior -v

# With coverage
pytest tests/ --cov=pytokencalc --cov-report=html
```

### Code Style

We follow PEP 8. No special formatter required, but:
- Use clear variable names
- Add type hints (PEP 484)
- Keep functions focused and small
- Document non-obvious behavior

### Commit Messages

```
format: Brief description

Longer explanation if needed. Reference issues with #123.

Examples:
- "feat: Add Groq tokenizer support"
- "fix: Cache invalidation for model updates"
- "docs: Improve ADDING_PROVIDERS guide"
```

---

## Project Structure

```
pytokencalc/
├── __init__.py           # Public API
├── exceptions.py         # Error types
└── tokenizers/           # Core token counting
    ├── base.py           # TokenCounter ABC
    ├── registry.py       # Intelligent routing
    ├── cache.py          # Caching layer
    ├── openai_counter.py # GPT tokenizer
    └── huggingface_counter.py # Llama/Mistral

tests/
└── test_token_counter.py # All tests (17 tests)

examples/
└── quick_start.py        # Usage examples

docs/
└── CONTRIBUTING.md       # This file
```

---

## Key Concepts

### TokenCounter Interface

Every tokenizer must implement:
- `provider_name` (property) - Unique identifier
- `supports_model(model: str) -> bool` - Check if model is supported
- `count(text: str, model: str) -> TokenCountResult` - Count tokens

### TokenCountResult

```python
@dataclass
class TokenCountResult:
    input_tokens: int      # Number of tokens
    source: str            # "local", "api", or "formula"
    latency_ms: float      # Execution time
    cached: bool = False   # Was result cached?
```

### Registry Routing

The `TokenCounterRegistry` automatically:
1. Checks each registered counter's `supports_model()`
2. Uses the first counter that returns `True`
3. Caches results for subsequent calls

---

## Testing Requirements

All PRs must:
- [ ] Include tests for new functionality
- [ ] Pass existing tests: `pytest tests/`
- [ ] Maintain or improve coverage

**Current state:** 17 tests, all passing ✅

---

## Before Submitting

1. Run tests locally
2. Check for obvious issues
3. Verify scope is within PyTokenCalc's mission
4. Add/update documentation if needed
5. Keep commits atomic and clear

---

## Questions?

- Check existing issues: https://github.com/Mullassery/PyTokenCalc/issues
- Read documentation: README.md, ADDING_PROVIDERS.md
- Open a discussion: https://github.com/Mullassery/PyTokenCalc/discussions

---

## Core Principles

**PyTokenCalc adheres to these principles:**

1. **Single Responsibility:** Count tokens. That's it.
2. **Zero External Dependencies:** Only pydantic required
3. **Accurate:** 99%+ match vs official token counts
4. **Fast:** <10ms for local, <1ms for cached
5. **Extensible:** Easy to add new tokenizers
6. **Pure Library:** No services, APIs, or infrastructure

---

Thank you for contributing to PyTokenCalc! 🙏

---

*Last updated: 2026-07-15*  
*Repository: https://github.com/Mullassery/PyTokenCalc*
