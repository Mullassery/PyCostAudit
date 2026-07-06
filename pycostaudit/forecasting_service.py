"""
Advanced cost forecasting with plan-aware calculations.
Projects 30/60/90-day costs, what-if scenarios, and confidence intervals.
"""

import statistics
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from .database import DatabaseManager, TimeSeriesDataPoint, ForecastCache


class BillingPlan(Enum):
    """Claude subscription plans"""
    API = "api"  # Pay-as-you-go
    PRO = "pro"  # $20/month
    MAX = "max"  # $100+ /month (variable tiers)


@dataclass
class PlanConfig:
    """Plan billing configuration"""
    name: str
    monthly_cost: float
    monthly_usage_limit: Optional[float]  # None = unlimited
    tokens_per_minute: int
    is_subscription: bool


# Plan configurations (based on public information)
PLAN_CONFIGS = {
    BillingPlan.API: PlanConfig(
        name="API",
        monthly_cost=0.0,  # Pay-per-token
        monthly_usage_limit=None,  # Unlimited
        tokens_per_minute=90000,
        is_subscription=False
    ),
    BillingPlan.PRO: PlanConfig(
        name="Claude Pro",
        monthly_cost=20.0,
        monthly_usage_limit=None,  # Included usage, no hard cap
        tokens_per_minute=90000,
        is_subscription=True
    ),
    BillingPlan.MAX: PlanConfig(
        name="Claude Max",
        monthly_cost=100.0,  # Base tier
        monthly_usage_limit=None,  # Higher included usage
        tokens_per_minute=900000,  # 10x higher rate limit
        is_subscription=True
    )
}


class ForecastingService:
    """Advanced cost forecasting with scenario analysis"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.min_history_days = 7

    def forecast_period(
        self,
        user_id: str,
        days: int = 30,
        plan: BillingPlan = BillingPlan.API,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """Forecast costs for a specific period"""
        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=90)

            if len(ts_data) < self.min_history_days:
                return self._insufficient_data_forecast(days, plan)

            # Calculate forecast metrics
            daily_costs = [d.total_cost for d in reversed(ts_data)]
            mean_daily = statistics.mean(daily_costs)
            stdev = statistics.stdev(daily_costs) if len(daily_costs) > 1 else 0

            # Project for the period
            projected_total = mean_daily * days
            projected_daily = mean_daily

            # Calculate confidence interval
            margin_of_error = self._calculate_margin_of_error(stdev, days, confidence)
            ci_low = max(0, projected_total - margin_of_error)
            ci_high = projected_total + margin_of_error

            # Apply plan-specific logic
            plan_config = PLAN_CONFIGS[plan]
            plan_adjusted_total = self._apply_plan_logic(projected_total, plan, days)

            # Trend analysis
            if len(daily_costs) >= 7:
                first_week = statistics.mean(daily_costs[:7])
                last_week = statistics.mean(daily_costs[-7:])
                trend_percent = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
            else:
                trend_percent = 0

            forecast = {
                "period_days": days,
                "plan": plan.value,
                "plan_name": plan_config.name,
                "plan_monthly_cost": plan_config.monthly_cost,
                "projected_daily_cost": projected_daily,
                "projected_total_cost": plan_adjusted_total,
                "confidence_interval": {
                    "low": ci_low,
                    "high": ci_high,
                    "confidence_level": confidence
                },
                "trend": {
                    "direction": "up" if trend_percent > 5 else "down" if trend_percent < -5 else "stable",
                    "percent_change": trend_percent
                },
                "statistics": {
                    "historical_days": len(daily_costs),
                    "historical_mean": mean_daily,
                    "historical_stdev": stdev,
                    "historical_min": min(daily_costs),
                    "historical_max": max(daily_costs)
                },
                "warnings": self._generate_warnings(plan_adjusted_total, plan, days)
            }

            return forecast

    def compare_plans(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Compare costs across different plans"""
        comparisons = []

        for plan in [BillingPlan.API, BillingPlan.PRO, BillingPlan.MAX]:
            forecast = self.forecast_period(user_id, days, plan)
            plan_config = PLAN_CONFIGS[plan]

            comparison = {
                "plan": plan.value,
                "plan_name": plan_config.name,
                "monthly_subscription": plan_config.monthly_cost if plan_config.is_subscription else 0,
                "projected_usage_cost": forecast["projected_total_cost"] - (plan_config.monthly_cost if plan_config.is_subscription else 0),
                "total_cost": forecast["projected_total_cost"],
                "tokens_per_minute": plan_config.tokens_per_minute,
                "is_best_for_usage": False
            }
            comparisons.append(comparison)

        # Find best plan (lowest total cost)
        best_plan = min(comparisons, key=lambda x: x["total_cost"])
        for comp in comparisons:
            if comp["plan"] == best_plan["plan"]:
                comp["is_best_for_usage"] = True

        return {
            "period_days": days,
            "comparisons": comparisons,
            "best_plan": best_plan["plan"],
            "best_plan_name": best_plan["plan_name"],
            "monthly_savings": max(0, comparisons[0]["total_cost"] - best_plan["total_cost"]),
            "annual_savings": max(0, (comparisons[0]["total_cost"] - best_plan["total_cost"]) * 12)
        }

    def what_if_optimization(
        self,
        user_id: str,
        days: int = 30,
        plan: BillingPlan = BillingPlan.API
    ) -> Dict[str, Any]:
        """Model cost savings from optimization strategies"""
        base_forecast = self.forecast_period(user_id, days, plan)
        base_cost = base_forecast["projected_total_cost"]

        scenarios = []

        # Scenario 1: Batch operations (20% reduction)
        batch_scenario = {
            "name": "Batch Operations",
            "description": "Group similar operations to reduce overhead",
            "savings_percent": 20,
            "projected_cost": base_cost * 0.8,
            "estimated_savings": base_cost * 0.2,
            "implementation_effort": "Medium (1-2 days)",
            "effort_score": 3
        }
        scenarios.append(batch_scenario)

        # Scenario 2: Off-peak scheduling (30% reduction)
        offpeak_scenario = {
            "name": "Off-Peak Scheduling",
            "description": "Run expensive operations during off-peak hours",
            "savings_percent": 30,
            "projected_cost": base_cost * 0.7,
            "estimated_savings": base_cost * 0.3,
            "implementation_effort": "Low (few hours)",
            "effort_score": 1
        }
        scenarios.append(offpeak_scenario)

        # Scenario 3: Model optimization (25% reduction)
        model_scenario = {
            "name": "Model Optimization",
            "description": "Use Haiku for simple tasks, Sonnet for complex",
            "savings_percent": 25,
            "projected_cost": base_cost * 0.75,
            "estimated_savings": base_cost * 0.25,
            "implementation_effort": "Medium (2-3 days)",
            "effort_score": 2
        }
        scenarios.append(model_scenario)

        # Scenario 4: Combined (55% reduction)
        combined_scenario = {
            "name": "Combined Optimizations",
            "description": "Apply all three optimization strategies",
            "savings_percent": 55,
            "projected_cost": base_cost * 0.45,
            "estimated_savings": base_cost * 0.55,
            "implementation_effort": "High (1-2 weeks)",
            "effort_score": 5
        }
        scenarios.append(combined_scenario)

        # Calculate ROI
        for scenario in scenarios:
            scenario["roi"] = (scenario["estimated_savings"] * 12) / (scenario["effort_score"] * 40)  # ROI per hour

        # Sort by ROI
        scenarios.sort(key=lambda x: x["roi"], reverse=True)

        return {
            "base_cost": base_cost,
            "period_days": days,
            "plan": plan.value,
            "scenarios": scenarios,
            "best_roi_scenario": scenarios[0] if scenarios else None,
            "potential_annual_savings": sum(s["estimated_savings"] for s in scenarios[:2]) * 12
        }

    def _apply_plan_logic(self, projected_cost: float, plan: BillingPlan, days: int) -> float:
        """Apply plan-specific billing logic"""
        config = PLAN_CONFIGS[plan]

        if plan == BillingPlan.API:
            # Pay-as-you-go, no adjustment needed
            return projected_cost
        elif plan == BillingPlan.PRO or plan == BillingPlan.MAX:
            # Subscription-based: minimum monthly cost
            monthly_periods = days / 30
            min_cost = config.monthly_cost * monthly_periods
            return max(min_cost, projected_cost)
        else:
            return projected_cost

    def _calculate_margin_of_error(
        self,
        stdev: float,
        days: int,
        confidence: float
    ) -> float:
        """Calculate confidence interval margin of error"""
        # Z-score for 95% confidence = 1.96
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence, 1.96)

        # Standard error increases with forecast horizon
        # More days = more uncertainty
        forecast_uncertainty = (days / 30) ** 0.5

        return z * stdev * forecast_uncertainty

    def _generate_warnings(
        self,
        projected_cost: float,
        plan: BillingPlan,
        days: int
    ) -> List[str]:
        """Generate warnings about forecast"""
        warnings = []

        config = PLAN_CONFIGS[plan]

        # Warning 1: Subscription inefficiency
        if plan != BillingPlan.API:
            monthly_cost = config.monthly_cost
            monthly_projected = (projected_cost / days) * 30

            if monthly_projected < monthly_cost * 0.3:
                warnings.append(
                    f"Projected usage suggests {plan.value.upper()} may not justify {monthly_cost:.0f}/month subscription"
                )

        # Warning 2: Approaching limits
        if plan == BillingPlan.MAX and projected_cost > 300:
            warnings.append("High spending: Consider if optimizations could reduce costs")

        # Warning 3: Volatility
        # (Would need stdev from caller to implement)

        return warnings

    def _insufficient_data_forecast(self, days: int, plan: BillingPlan) -> Dict[str, Any]:
        """Return placeholder forecast when insufficient data"""
        config = PLAN_CONFIGS[plan]
        monthly_cost = config.monthly_cost

        return {
            "period_days": days,
            "plan": plan.value,
            "plan_name": config.name,
            "plan_monthly_cost": monthly_cost,
            "projected_daily_cost": monthly_cost / 30 if plan != BillingPlan.API else 0,
            "projected_total_cost": (monthly_cost / 30) * days if plan != BillingPlan.API else 0,
            "confidence_interval": {
                "low": 0,
                "high": 0,
                "confidence_level": 0.0
            },
            "trend": {
                "direction": "insufficient_data",
                "percent_change": 0
            },
            "statistics": {
                "historical_days": 0,
                "historical_mean": 0,
                "historical_stdev": 0,
                "historical_min": 0,
                "historical_max": 0
            },
            "warnings": [
                "Insufficient historical data. Collect more data for accurate forecast.",
                f"Showing minimum {plan.value} subscription cost if applicable."
            ]
        }

    def get_breakeven_analysis(
        self,
        user_id: str,
        from_plan: BillingPlan = BillingPlan.API,
        to_plan: BillingPlan = BillingPlan.PRO
    ) -> Dict[str, Any]:
        """Calculate when a plan change makes financial sense"""
        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=90)

            if len(ts_data) < self.min_history_days:
                return {"error": "Insufficient data for breakeven analysis"}

            daily_costs = [d.total_cost for d in reversed(ts_data)]
            mean_daily = statistics.mean(daily_costs)

            from_config = PLAN_CONFIGS[from_plan]
            to_config = PLAN_CONFIGS[to_plan]

            # Daily cost difference
            from_daily = from_config.monthly_cost / 30 if from_config.is_subscription else mean_daily
            to_daily = to_config.monthly_cost / 30 if to_config.is_subscription else mean_daily

            # Calculate breakeven
            if to_daily < from_daily:
                monthly_savings = (from_daily - to_daily) * 30
                breakeven_months = 0
                recommendation = "Switch immediately - saves money"
            elif to_daily > from_daily:
                monthly_additional_cost = (to_daily - from_daily) * 30
                breakeven_months = 0  # Never breaks even if more expensive
                recommendation = "Not recommended - costs more"
            else:
                monthly_savings = 0
                breakeven_months = 0
                recommendation = "No financial difference"

            return {
                "from_plan": from_plan.value,
                "to_plan": to_plan.value,
                "current_monthly_cost": from_daily * 30,
                "new_monthly_cost": to_daily * 30,
                "monthly_savings": max(0, monthly_savings),
                "breakeven_months": breakeven_months,
                "annual_savings": max(0, monthly_savings * 12),
                "recommendation": recommendation,
                "projected_daily_usage": mean_daily
            }
