"""
PyTokenCalc v0.7: Multi-provider token cost calculator.
Calculates real costs from LLM API usage with provider-specific token models.
"""

from typing import Dict, List, Optional
from collections import defaultdict
from .cost_models import UsageData, CostModelRegistry


class CostCalculatorV6:
    """
    PyTokenCalc v0.6: Multi-provider cost calculator with provider-specific token models.
    Supports 20+ cloud providers and 10+ open-source APIs with accurate cost calculation.
    """

    def __init__(self):
        self.model_registry = CostModelRegistry()
        self.costs_tracked: List[UsageData] = []

    def calculate(self, usage: UsageData) -> float:
        """Calculate cost using provider-specific model"""
        cost = self.model_registry.calculate_cost(usage)
        self.costs_tracked.append(usage)
        return cost

    def calculate_batch(self, usages: List[UsageData]) -> List[float]:
        """Calculate costs for multiple operations"""
        return [self.calculate(usage) for usage in usages]

    def total_cost(self, provider: Optional[str] = None, model: Optional[str] = None) -> float:
        """Get total cost with optional filters"""
        total = 0.0
        for usage in self.costs_tracked:
            if provider and usage.provider != provider:
                continue
            if model and usage.model != model:
                continue
            cost = self.model_registry.calculate_cost(usage)
            total += cost
        return total

    def cost_by_provider(self) -> Dict[str, float]:
        """Breakdown costs by provider"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            breakdown[usage.provider] += cost
        return dict(breakdown)

    def cost_by_model(self) -> Dict[str, float]:
        """Breakdown costs by model"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            breakdown[usage.model] += cost
        return dict(breakdown)

    def cost_by_task_type(self) -> Dict[str, float]:
        """Breakdown costs by task type"""
        breakdown = defaultdict(float)
        for usage in self.costs_tracked:
            task = usage.task_type or "unspecified"
            cost = self.model_registry.calculate_cost(usage)
            breakdown[task] += cost
        return dict(breakdown)

    def get_tracked_operations(self) -> List[UsageData]:
        """Get all tracked operations"""
        return self.costs_tracked.copy()

    def clear(self):
        """Clear all tracked costs"""
        self.costs_tracked.clear()

    def export(self) -> List[Dict]:
        """Export tracked costs as dictionaries"""
        exported = []
        for usage in self.costs_tracked:
            cost = self.model_registry.calculate_cost(usage)
            exported.append({
                "provider": usage.provider,
                "model": usage.model,
                "timestamp": usage.timestamp.isoformat(),
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "input_characters": usage.input_characters,
                "output_characters": usage.output_characters,
                "speed_tier": usage.speed_tier,
                "cost_usd": cost,
                "task_type": usage.task_type,
            })
        return exported
