#!/usr/bin/env python3
"""
PyTokenCalc v0.7 Quick Start Example

Shows how to:
1. Count tokens for different models
2. Calculate costs across providers
3. Track operations and get breakdowns
"""

from pytokencalc import CostCalculatorV6, UsageData
from pytokencalc.tokenizers import TokenCounterRegistry


def token_counting_example():
    """Demonstrate token counting across providers"""
    print("\n" + "=" * 60)
    print("TOKEN COUNTING EXAMPLE")
    print("=" * 60)

    registry = TokenCounterRegistry()

    # Count tokens for different models
    text = "Your prompt here: Analyze this data and provide insights."

    models = ["gpt-4o", "llama-70b", "claude-3-5-sonnet"]
    for model in models:
        try:
            result = registry.count_tokens(model, text)
            print(f"{model:20} → {result.input_tokens:4d} tokens (source: {result.source})")
        except Exception as e:
            print(f"{model:20} → Error: {str(e)[:40]}")


def cost_calculation_example():
    """Demonstrate cost calculation across providers"""
    print("\n" + "=" * 60)
    print("COST CALCULATION EXAMPLE")
    print("=" * 60)

    calc = CostCalculatorV6()

    # Example 1: Claude (simple input/output model)
    print("\n1️⃣ Claude 3.5 Sonnet")
    usage = UsageData(
        provider="anthropic",
        model="claude-3-5-sonnet",
        input_tokens=1_000_000,
        output_tokens=500_000,
        task_type="analysis"
    )
    cost = calc.calculate(usage)
    print(f"   1M input + 500K output tokens → ${cost:.4f}")

    # Example 2: GPT-4o (dual token model: full + mini)
    print("\n2️⃣ GPT-4o (with mini tokens)")
    usage = UsageData(
        provider="openai",
        model="gpt-4o",
        input_tokens=1_000_000,
        input_mini_tokens=500_000,  # Mini tokens cheaper
        output_tokens=250_000,
        task_type="coding"
    )
    cost = calc.calculate(usage)
    print(f"   1M full + 500K mini input tokens → ${cost:.4f}")

    # Example 3: Gemini (character-based)
    print("\n3️⃣ Gemini 2 Flash (character-based billing)")
    usage = UsageData(
        provider="google",
        model="gemini-2-flash",
        input_characters=1_000_000_000,  # 1B characters
        output_characters=500_000_000,
        task_type="summarization"
    )
    cost = calc.calculate(usage)
    print(f"   1B input + 500M output characters → ${cost:.4f}")

    # Example 4: Groq (speed-tiered)
    print("\n4️⃣ Groq Llama 70B (speed-tiered)")
    usage = UsageData(
        provider="groq",
        model="llama-70b",
        input_tokens=1_000_000,
        output_tokens=500_000,
        speed_tier="standard",
        task_type="reasoning"
    )
    cost = calc.calculate(usage)
    print(f"   Standard tier: ${cost:.4f}")

    usage.speed_tier = "fastest"
    cost = calc.calculate(usage)
    print(f"   Fastest tier:  ${cost:.4f}")

    # Example 5: Cost breakdown
    print("\n5️⃣ Cost Breakdown")
    print(f"   By provider: {calc.cost_by_provider()}")
    print(f"   By model:    {calc.cost_by_model()}")
    print(f"   By task:     {calc.cost_by_task_type()}")
    print(f"   Total:       ${calc.total_cost():.4f}")


def batch_operations_example():
    """Demonstrate batch operations"""
    print("\n" + "=" * 60)
    print("BATCH OPERATIONS EXAMPLE")
    print("=" * 60)

    calc = CostCalculatorV6()

    operations = [
        UsageData(
            provider="anthropic",
            model="claude-3-5-sonnet",
            input_tokens=100_000,
            output_tokens=50_000,
            task_type="analysis"
        ),
        UsageData(
            provider="openai",
            model="gpt-4o",
            input_tokens=100_000,
            output_tokens=50_000,
            task_type="coding"
        ),
        UsageData(
            provider="google",
            model="gemini-2-flash",
            input_characters=100_000_000,
            output_characters=50_000_000,
            task_type="summarization"
        ),
    ]

    costs = calc.calculate_batch(operations)
    total = sum(costs)

    print(f"\nBatch of 3 operations:")
    for i, (op, cost) in enumerate(zip(operations, costs), 1):
        print(f"  {i}. {op.provider:12} {op.model:20} → ${cost:.4f}")

    print(f"\nTotal cost: ${total:.4f}")


def export_example():
    """Demonstrate export functionality"""
    print("\n" + "=" * 60)
    print("EXPORT EXAMPLE")
    print("=" * 60)

    calc = CostCalculatorV6()

    # Track some operations
    calc.calculate(UsageData(
        provider="anthropic",
        model="claude-3-5-sonnet",
        input_tokens=500_000,
        output_tokens=250_000,
        task_type="analysis"
    ))

    calc.calculate(UsageData(
        provider="openai",
        model="gpt-4o",
        input_tokens=500_000,
        output_tokens=250_000,
        task_type="coding"
    ))

    # Export all operations
    exported = calc.export()
    print(f"\nExported {len(exported)} operations:")
    for op in exported:
        print(f"  {op['provider']:12} {op['model']:20} → ${op['cost_usd']:.4f}")


if __name__ == "__main__":
    print("\n🚀 PyTokenCalc v0.7 Quick Start Guide")

    token_counting_example()
    cost_calculation_example()
    batch_operations_example()
    export_example()

    print("\n" + "=" * 60)
    print("✅ Examples complete!")
    print("=" * 60)
