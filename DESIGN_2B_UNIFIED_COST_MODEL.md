# Design: Unified Multi-Provider Cost Model (Phase 2B)

**Status**: Design (Ready for implementation)  
**Timeline**: Week 1-2  
**Owner**: Backend Developer  

---

## Overview

Abstraction layer that unifies cost calculation across OpenAI, AWS Bedrock, and Google Gemini. Each provider has different pricing models, but we expose a single interface.

---

## Architecture

```
Application Code
      ↓
CostTracker API (unified interface)
      ↓
    ↙  ↓  ↘
OpenAI  Bedrock  Gemini
Plugin  Plugin   Plugin
      ↓    ↓      ↓
   Provider-specific cost logic
```

---

## Core Interfaces

### 1. Provider Registry

```python
class ProviderRegistry:
    """Registry of all supported providers"""
    
    @staticmethod
    def detect_provider(call_data) -> Provider:
        """Detect which provider from SDK call signature"""
        # If openai.ChatCompletion.create() → OpenAIProvider
        # If bedrock.invoke_model() → BedrockProvider
        # If genai.GenerativeModel → GeminiProvider
        pass
    
    @staticmethod
    def get_provider(name: str) -> Provider:
        """Get provider by name: 'openai', 'bedrock', 'gemini'"""
        pass
    
    @staticmethod
    def list_providers() -> List[str]:
        """List all registered providers"""
        pass
```

### 2. Provider Interface (Abstract)

```python
from abc import ABC, abstractmethod

class Provider(ABC):
    """Base class for all LLM providers"""
    
    name: str  # 'openai', 'bedrock', 'gemini'
    
    @abstractmethod
    def detect_call(self, call_data) -> bool:
        """Check if this call is for this provider"""
        pass
    
    @abstractmethod
    def calculate_cost(self, call_data) -> Cost:
        """Calculate cost for a single call"""
        pass
    
    @abstractmethod
    def validate_pricing(self) -> bool:
        """Validate pricing table is loaded correctly"""
        pass

class Cost:
    """Cost calculation result"""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float  # dollars
    output_cost: float  # dollars
    total_cost: float  # dollars
    details: dict  # {vision_premium: 0.2, batch_discount: 0.1, etc}
```

### 3. Cost Tracker (Main API)

```python
class CostTracker:
    """Unified cost tracking across all providers"""
    
    def __init__(self):
        self.registry = ProviderRegistry()
        self.costs = []
    
    def track_api_call(self, call_data, response_data):
        """Track a single API call (called by interceptor/middleware)"""
        provider = self.registry.detect_provider(call_data)
        cost = provider.calculate_cost(call_data, response_data)
        self.costs.append(cost)
        return cost
    
    def get_costs(self, filters=None) -> List[Cost]:
        """Get costs with optional filters"""
        # filters: {provider: 'openai', model: 'gpt-4', start_time: ..., end_time: ...}
        pass
    
    def get_total_cost(self, filters=None) -> float:
        """Total cost across all tracked calls"""
        pass
    
    def cost_by_provider(self) -> dict:
        """Breakdown: {openai: 100.50, bedrock: 50.25, gemini: 10.10}"""
        pass
    
    def cost_by_model(self) -> dict:
        """Breakdown by model"""
        pass
```

---

## Provider Implementations

### Provider 1: OpenAI

```python
class OpenAIProvider(Provider):
    name = 'openai'
    
    # Pricing loaded from PRICING_DATA.md
    PRICING = {
        'gpt-4': {'input': 0.03, 'output': 0.06},  # $/1K tokens
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-5': {'input': 0.05, 'output': 0.10},
        # ... more models
    }
    
    def detect_call(self, call_data) -> bool:
        # Check if openai.ChatCompletion.create() or similar
        return hasattr(call_data, 'model') and 'gpt' in call_data.model
    
    def calculate_cost(self, call_data, response_data) -> Cost:
        model = call_data.model
        input_tokens = response_data.usage.prompt_tokens
        output_tokens = response_data.usage.completion_tokens
        
        input_cost = (input_tokens / 1000) * self.PRICING[model]['input']
        output_cost = (output_tokens / 1000) * self.PRICING[model]['output']
        
        # Handle vision premium if applicable
        if 'vision' in call_data or call_data.model == 'gpt-4-vision':
            # Add vision premium (typically 25% markup)
            input_cost *= 1.25
        
        return Cost(
            provider='openai',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            details={'vision_premium': 0.25 if 'vision' in call_data else 0}
        )
```

### Provider 2: AWS Bedrock

```python
class BedrockProvider(Provider):
    name = 'bedrock'
    
    PRICING = {
        'anthropic.claude-3-opus': {'input': 0.015, 'output': 0.075},  # $/1K tokens
        'anthropic.claude-3-sonnet': {'input': 0.003, 'output': 0.015},
        'anthropic.claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        'meta.llama2-70b': {'input': 0.0008, 'output': 0.001},
        'mistral.mistral-large': {'input': 0.008, 'output': 0.024},
    }
    
    def detect_call(self, call_data) -> bool:
        # Check if bedrock.invoke_model() call
        return hasattr(call_data, 'modelId') and 'anthropic' in call_data.modelId
    
    def calculate_cost(self, call_data, response_data) -> Cost:
        model = call_data.modelId
        input_tokens = response_data['usage']['input_tokens']
        output_tokens = response_data['usage']['output_tokens']
        
        input_cost = (input_tokens / 1000) * self.PRICING[model]['input']
        output_cost = (output_tokens / 1000) * self.PRICING[model]['output']
        
        # Check for provisioned throughput discount
        provisioned_discount = 0
        if 'provisioned_throughput_arn' in call_data:
            provisioned_discount = 0.1  # 10% discount for provisioned
        
        total_cost = (input_cost + output_cost) * (1 - provisioned_discount)
        
        return Cost(
            provider='bedrock',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            details={'provisioned_discount': provisioned_discount}
        )
```

### Provider 3: Google Gemini

```python
class GeminiProvider(Provider):
    name = 'gemini'
    
    PRICING = {
        'gemini-pro': {'input': 0.000125, 'output': 0.000375},  # $/1K tokens
        'gemini-pro-vision': {'input': 0.000125, 'output': 0.000375},
    }
    
    def detect_call(self, call_data) -> bool:
        # Check if genai.GenerativeModel().generate_content()
        return hasattr(call_data, 'model') and 'gemini' in call_data.model
    
    def calculate_cost(self, call_data, response_data) -> Cost:
        model = call_data.model or 'gemini-pro'
        input_tokens = response_data.usage_metadata.prompt_token_count
        output_tokens = response_data.usage_metadata.candidates_token_count
        
        input_cost = (input_tokens / 1000) * self.PRICING[model]['input']
        output_cost = (output_tokens / 1000) * self.PRICING[model]['output']
        
        return Cost(
            provider='gemini',
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            details={}
        )
```

---

## Integration Points

### 1. Python SDK Integration (Decorator/Wrapper)

```python
# Option A: Decorator approach
@track_cost(tracker)
def my_function():
    response = openai.ChatCompletion.create(...)
    return response

# Option B: Context manager
with cost_tracker.track():
    response = openai.ChatCompletion.create(...)

# Option C: Manual tracking
cost_tracker.track_api_call(call_data, response_data)
```

### 2. Middleware Approach (Proxy Layer)

```python
# Route all provider calls through middleware
class CostTrackingMiddleware:
    def __init__(self, tracker):
        self.tracker = tracker
    
    def before_request(self, call_data):
        # Extract call data
        pass
    
    def after_request(self, response_data):
        # Track cost
        cost = self.tracker.track_api_call(...)
        return response_data
```

---

## Data Storage

### Cost Record Schema

```python
class CostRecord:
    id: str
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    metadata: dict  # {user_id, project_id, tags, etc}
    details: dict  # Provider-specific details
```

### Storage Options

1. **SQLite** (local, simple): `pycostaudit_costs.db`
2. **PostgreSQL** (scalable): `costs` table with indexes on (timestamp, provider, model)
3. **JSON file** (very simple): `costs.jsonl` (newline-delimited JSON)

**Recommended for MVP**: SQLite with automatic rotation (daily backup)

---

## Testing Strategy

### Unit Tests

```python
def test_openai_cost_calculation():
    provider = OpenAIProvider()
    call_data = MockOpenAICall(model='gpt-4', tokens=1000)
    response = MockOpenAIResponse(prompt_tokens=100, completion_tokens=50)
    cost = provider.calculate_cost(call_data, response)
    assert cost.total_cost == expected_value

def test_bedrock_with_provisioned_discount():
    provider = BedrockProvider()
    call_data = MockBedrockCall(provisioned_throughput_arn='...')
    cost = provider.calculate_cost(call_data, response)
    assert cost.details['provisioned_discount'] == 0.1

def test_provider_detection():
    registry = ProviderRegistry()
    assert registry.detect_provider(openai_call).name == 'openai'
    assert registry.detect_provider(bedrock_call).name == 'bedrock'
```

### Integration Tests

```python
def test_multi_provider_tracking():
    tracker = CostTracker()
    
    # Track OpenAI call
    tracker.track_api_call(openai_call, openai_response)
    
    # Track Bedrock call
    tracker.track_api_call(bedrock_call, bedrock_response)
    
    # Verify breakdown
    breakdown = tracker.cost_by_provider()
    assert 'openai' in breakdown
    assert 'bedrock' in breakdown
```

---

## Implementation Phases

### Phase 1 (Days 1-3): Core Architecture
- [ ] Create base `Provider` class and `CostTracker`
- [ ] Implement `ProviderRegistry`
- [ ] Create `Cost` data class
- [ ] Set up storage (SQLite)

### Phase 2 (Days 3-5): Provider Implementations
- [ ] Implement `OpenAIProvider` (with pricing from PRICING_DATA.md)
- [ ] Implement `BedrockProvider`
- [ ] Implement `GeminiProvider`
- [ ] Load pricing tables from external file

### Phase 3 (Days 5-7): Integration & Testing
- [ ] Create decorator/context manager for easy integration
- [ ] Write comprehensive unit & integration tests
- [ ] Validate against real SDK calls (mock test data)
- [ ] Performance testing (ensure tracking adds <5ms latency)

---

## Success Criteria

- ✓ All three providers (OpenAI, Bedrock, Gemini) tracked
- ✓ Pricing loaded from PRICING_DATA.md file (updateable)
- ✓ <5ms overhead per tracked call
- ✓ 95%+ accuracy (within 0.01 cents per call)
- ✓ All tests passing

---

## Next Steps

1. Fill in `PRICING_DATA.md` with current rates
2. Proceed with Phase 1 implementation (core architecture)
3. Implement each provider plugin
4. Validate with real API calls
