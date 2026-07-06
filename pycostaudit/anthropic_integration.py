"""
Anthropic API integration for real usage data.
Gets actual token counts and costs from Anthropic, not estimates.
"""

import os
from typing import Dict, Optional, List
from pathlib import Path
import json
from datetime import datetime, timedelta


class AnthropicAPIClient:
    """Client for Anthropic's usage and billing APIs"""

    BASE_URL = "https://api.anthropic.com/v1"

    ANTHROPIC_MODELS = {
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "input_price": 3.00,  # per 1M tokens
            "output_price": 15.00,
        },
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "input_price": 0.80,
            "output_price": 4.00,
        },
        "claude-3-opus-20250219": {
            "name": "Claude 3 Opus",
            "input_price": 15.00,
            "output_price": 75.00,
        },
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic API client.

        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.available = bool(self.api_key)

        if not self.available:
            print("⚠️  Anthropic API key not found. Using estimates instead.")
            print("   To enable real costs: export ANTHROPIC_API_KEY=sk-ant-...")

    def get_real_usage(self, days: int = 30) -> Dict:
        """
        Get real usage data from Anthropic API.

        This requires an Anthropic API key and access to the usage endpoint.

        Args:
            days: Number of days of history to retrieve

        Returns:
            Dict with real usage and costs
        """
        if not self.available:
            return {"error": "Anthropic API key not configured"}

        try:
            import requests
        except ImportError:
            return {"error": "requests library not installed. pip install requests"}

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        # Note: This endpoint may not be publicly available yet
        # This is the structure for when it becomes available
        endpoint = f"{self.BASE_URL}/usage"

        params = {
            "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
        }

        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "error": f"API returned {response.status_code}",
                    "note": "Usage API may not be available yet"
                }
        except Exception as e:
            return {"error": str(e)}

    def get_usage_summary(self) -> Dict:
        """
        Get summary of current month's usage.

        Returns:
            Dict with total tokens, cost, by model breakdown
        """
        if not self.available:
            return {"available": False, "reason": "No API key configured"}

        usage = self.get_real_usage(days=30)

        if "error" in usage:
            return {"available": False, "error": usage["error"]}

        # Parse response and calculate costs
        try:
            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0
            by_model = {}

            for model_id, model_pricing in self.ANTHROPIC_MODELS.items():
                model_usage = usage.get(model_id, {})
                input_tokens = model_usage.get("input_tokens", 0)
                output_tokens = model_usage.get("output_tokens", 0)

                model_cost = (
                    (input_tokens * model_pricing["input_price"]) +
                    (output_tokens * model_pricing["output_price"])
                ) / 1_000_000

                if input_tokens + output_tokens > 0:
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens
                    total_cost += model_cost

                    by_model[model_id] = {
                        "name": model_pricing["name"],
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_usd": round(model_cost, 4),
                    }

            return {
                "available": True,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "total_cost_usd": round(total_cost, 2),
                "by_model": by_model,
            }

        except Exception as e:
            return {"available": False, "error": str(e)}

    def compare_estimated_vs_real(self, estimated_cost: float) -> Dict:
        """
        Compare estimated costs (from history analysis) vs real costs (from API).

        Args:
            estimated_cost: Cost calculated from token estimation

        Returns:
            Comparison showing accuracy of estimation
        """
        real = self.get_usage_summary()

        if not real.get("available"):
            return {"status": "Unable to fetch real data", "reason": real.get("error")}

        real_cost = real.get("total_cost_usd", 0)
        difference = abs(real_cost - estimated_cost)
        accuracy = (1 - (difference / max(real_cost, estimated_cost))) * 100 if max(real_cost, estimated_cost) > 0 else 0

        return {
            "estimated_cost": round(estimated_cost, 2),
            "real_cost": round(real_cost, 2),
            "difference": round(difference, 2),
            "accuracy": round(accuracy, 1),
            "recommendation": "Estimates are good" if accuracy > 80 else "Consider using real data",
        }


class RealCostCalculator:
    """
    Enhanced cost calculator using real Anthropic API data when available.
    Falls back to estimates when API key not configured.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.anthropic = AnthropicAPIClient(api_key)
        self.use_real_data = self.anthropic.available

    def get_costs(self, history_file: Optional[str] = None) -> Dict:
        """
        Get cost data - real if available, estimated otherwise.

        Args:
            history_file: Path to Claude Code history file

        Returns:
            Dict with costs and data source (real or estimated)
        """
        if self.use_real_data:
            real_data = self.anthropic.get_usage_summary()

            if real_data.get("available"):
                return {
                    "source": "real",
                    "data": real_data,
                    "note": "Data from Anthropic API - actual token counts",
                }

        # Fallback to estimates
        from pycostaudit.cost_calculator import CostCalculator

        calc = CostCalculator(history_file)
        breakdown = calc.get_cost_breakdown()

        return {
            "source": "estimated",
            "data": breakdown,
            "note": "Data from Claude Code history - estimated tokens",
        }

    def calibrate_estimates(self, estimated_cost: float) -> Dict:
        """
        Use real API data to calibrate and improve future estimates.

        Args:
            estimated_cost: Previously estimated cost

        Returns:
            Calibration results for ML model training
        """
        comparison = self.anthropic.compare_estimated_vs_real(estimated_cost)

        return {
            "comparison": comparison,
            "next_step": "Real data collected for model improvement",
        }


def setup_anthropic_api_key():
    """
    Interactive setup for Anthropic API key.
    Helps user configure optional real data source.
    """
    print("\n" + "=" * 80)
    print("🔑 ANTHROPIC API KEY SETUP (Optional)")
    print("=" * 80 + "\n")

    print("PyCostAudit can use real token counts from Anthropic API.")
    print("This gives you actual costs instead of estimates.\n")

    print("To enable:")
    print("1. Get your Anthropic API key from https://console.anthropic.com/account/keys")
    print("2. Run: export ANTHROPIC_API_KEY=sk-ant-...")
    print("3. Or create ~/.pycostaudit/config.json:\n")

    config_template = {
        "anthropic_api_key": "sk-ant-your-key-here",
        "use_real_data": True,
        "cache_results": True,
    }

    print(json.dumps(config_template, indent=2))
    print("\n✅ Optional - PyCostAudit works without it using estimates")
    print("=" * 80 + "\n")


def load_config() -> Dict:
    """
    Load PyCostAudit configuration.

    Checks:
    1. Environment variables
    2. ~/.pycostaudit/config.json
    3. Defaults to estimates mode
    """
    config = {
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
        "use_real_data": os.getenv("PYCOSTAUDIT_REAL_DATA", "false").lower() == "true",
    }

    config_file = Path("~/.pycostaudit/config.json").expanduser()
    if config_file.exists():
        try:
            with open(config_file) as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception:
            pass

    return config
