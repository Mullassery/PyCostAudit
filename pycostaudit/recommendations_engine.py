"""
Intelligent cost optimization recommendations.
Analyzes spending patterns and suggests targeted optimization strategies.
"""

import statistics
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .database import DatabaseManager, RecommendationRecord
from .pricing_manager import PricingManager, Provider, Region


class RecommendationType(Enum):
    """Types of cost optimization recommendations"""
    BATCH_OPERATIONS = "batch_operations"
    OFF_PEAK_SCHEDULING = "off_peak_scheduling"
    MODEL_DOWNGRADE = "model_downgrade"
    FILE_FORMAT_OPTIMIZATION = "file_format_optimization"
    MCP_EFFICIENCY = "mcp_efficiency"
    CACHE_OPTIMIZATION = "cache_optimization"
    PLAN_CHANGE = "plan_change"
    OPERATION_ELIMINATION = "operation_elimination"


@dataclass
class Recommendation:
    """Single optimization recommendation"""
    type: RecommendationType
    title: str
    description: str
    estimated_savings_usd: float
    estimated_savings_percent: float
    implementation_effort_hours: float
    roi_score: float
    implementation_steps: List[str]
    estimated_implementation_time: str
    confidence_score: float  # 0-1, how sure we are


class RecommendationsEngine:
    """Generate optimization recommendations from cost data"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.pricing_manager = PricingManager()

    def generate_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        min_savings: float = 1.0,
        provider: Provider = Provider.ANTHROPIC_API,
        region: Optional[Region] = None,
        model: str = "claude-3-5-sonnet"
    ) -> List[Recommendation]:
        """Generate all applicable recommendations for a user"""
        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=90)

            if len(ts_data) < 7:
                return []

            recommendations = []

            # Analyze patterns
            daily_costs = [d.total_cost for d in reversed(ts_data)]
            mean_cost = statistics.mean(daily_costs)

            # Get regional pricing multiplier
            regional_multiplier = self._get_regional_multiplier(provider, region)

            # 1. Batching recommendations
            batching_recs = self._analyze_batching_opportunities(
                ts_data, daily_costs, mean_cost, user_id, regional_multiplier
            )
            recommendations.extend(batching_recs)

            # 2. Off-peak scheduling
            offpeak_recs = self._analyze_offpeak_opportunities(
                ts_data, mean_cost, user_id, regional_multiplier
            )
            recommendations.extend(offpeak_recs)

            # 3. Model optimization (compare models in same region)
            model_recs = self._analyze_model_optimization(
                ts_data, mean_cost, user_id, provider, region, model, regional_multiplier
            )
            recommendations.extend(model_recs)

            # 4. File format optimization
            format_recs = self._analyze_file_format_opportunities(
                ts_data, mean_cost, user_id, regional_multiplier
            )
            recommendations.extend(format_recs)

            # 5. MCP efficiency
            mcp_recs = self._analyze_mcp_efficiency(
                ts_data, mean_cost, user_id, regional_multiplier
            )
            recommendations.extend(mcp_recs)

            # 6. Cache optimization
            cache_recs = self._analyze_cache_opportunities(
                ts_data, mean_cost, user_id, regional_multiplier
            )
            recommendations.extend(cache_recs)

            # 7. Region/Provider optimization
            region_recs = self._analyze_region_optimization(
                user_id, mean_cost, provider, region, model
            )
            recommendations.extend(region_recs)

            # Filter and sort
            recommendations = [r for r in recommendations if r.estimated_savings_usd >= min_savings]
            recommendations.sort(key=lambda r: r.roi_score, reverse=True)

            # Persist top recommendations
            self._save_recommendations(user_id, recommendations[:limit])

            return recommendations[:limit]

    def _get_regional_multiplier(self, provider: Provider, region: Optional[Region]) -> float:
        """Get price multiplier for region"""
        regional_multipliers = {
            (Provider.ANTHROPIC_API, None): 1.0,
            (Provider.AWS_BEDROCK, Region.US_EAST_1): 1.0,
            (Provider.AWS_BEDROCK, Region.EU_WEST_1): 1.10,
            (Provider.AWS_BEDROCK, Region.AP_SOUTHEAST_1): 1.15,
            (Provider.GCP_MODEL_GARDEN, None): 1.0,
            (Provider.AZURE_FOUNDRY, Region.EAST_US): 1.0,
            (Provider.AZURE_FOUNDRY, Region.WEST_EU): 1.12,
            (Provider.AZURE_FOUNDRY, Region.SOUTHEAST_ASIA): 1.20,
        }
        return regional_multipliers.get((provider, region), 1.0)

    def _analyze_region_optimization(
        self,
        user_id: str,
        mean_cost: float,
        current_provider: Provider,
        current_region: Optional[Region],
        model: str
    ) -> List[Recommendation]:
        """Analyze region/provider switching opportunities"""
        recommendations = []

        # Find cheapest provider for same workload
        tokens_per_day = mean_cost / 0.05  # Rough estimate
        cheapest_provider, cheapest_cost = self.pricing_manager.get_cheapest_provider(
            model,
            int(tokens_per_day),
            int(tokens_per_day * 0.3)
        )

        # Compare with current
        current_pricing = self.pricing_manager.get_pricing(current_provider, current_region)
        if model in current_pricing:
            current_monthly_cost = mean_cost * 30
            cheapest_monthly = cheapest_cost * 30 * 30  # Rough projection

            if cheapest_monthly < current_monthly_cost * 0.95:  # At least 5% savings
                savings = current_monthly_cost - cheapest_monthly

                rec = Recommendation(
                    type=RecommendationType.PLAN_CHANGE,
                    title=f"Switch to {cheapest_provider} for {savings/current_monthly_cost*100:.0f}% savings",
                    description=f"Moving from {current_provider.value} to {cheapest_provider} "
                               f"would save approximately ${savings:.2f}/month.",
                    estimated_savings_usd=savings,
                    estimated_savings_percent=(savings / current_monthly_cost) * 100,
                    implementation_effort_hours=24,  # Higher effort for migration
                    roi_score=savings * 12 / 24,
                    implementation_steps=[
                        "Audit current usage patterns",
                        "Test workloads on new provider",
                        "Set up authentication/credentials",
                        "Gradually migrate traffic",
                        "Monitor for performance differences",
                        "Decommission old setup"
                    ],
                    estimated_implementation_time="1-2 weeks",
                    confidence_score=0.6  # Lower due to migration complexity
                )
                recommendations.append(rec)

        return recommendations

    def _analyze_batching_opportunities(
        self,
        ts_data: List,
        daily_costs: List[float],
        mean_cost: float,
        user_id: str,
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze batching optimization opportunities"""
        recommendations = []

        # Check if there are multiple small operations that could be batched
        # Heuristic: If we see consistent daily operations, suggest batching
        num_operations_per_day = sum(d.num_operations for d in ts_data) / len(ts_data)

        if num_operations_per_day > 100:  # More than 100 ops/day
            # Estimate 30% savings from batching
            daily_savings = mean_cost * 0.30
            monthly_savings = daily_savings * 30

            rec = Recommendation(
                type=RecommendationType.BATCH_OPERATIONS,
                title="Batch Similar Operations",
                description=f"You're running {num_operations_per_day:.0f} operations daily. "
                           "Grouping similar tasks can reduce overhead by 20-40%.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=30,
                implementation_effort_hours=8,
                roi_score=monthly_savings * 12 / 8,
                implementation_steps=[
                    "Analyze your operation patterns",
                    "Group similar operations (e.g., all file reads)",
                    "Batch them into single requests",
                    "Monitor for cost reduction"
                ],
                estimated_implementation_time="1-2 days",
                confidence_score=0.7
            )
            recommendations.append(rec)

        return recommendations

    def _analyze_offpeak_opportunities(
        self,
        ts_data: List,
        mean_cost: float,
        user_id: str,
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze off-peak scheduling opportunities"""
        recommendations = []

        # Check for consistent daily costs (indicates potential off-peak savings)
        # Off-peak rates are 30% lower (0.7x multiplier)
        # Account for regional multiplier
        potential_savings = (mean_cost * regional_multiplier) * 0.30

        if potential_savings > 1.0:  # At least $1/day savings
            monthly_savings = potential_savings * 30

            rec = Recommendation(
                type=RecommendationType.OFF_PEAK_SCHEDULING,
                title="Shift Operations to Off-Peak Hours",
                description="Run expensive operations during off-peak hours (10 PM - 6 AM) "
                           "to get 30% discount on costs.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=30,
                implementation_effort_hours=4,
                roi_score=monthly_savings * 12 / 4,
                implementation_steps=[
                    "Identify which operations can be scheduled",
                    "Set up automated scheduling (cron/scheduler)",
                    "Route off-peak operations to night hours",
                    "Monitor for rate limit compliance"
                ],
                estimated_implementation_time="Few hours",
                confidence_score=0.85
            )
            recommendations.append(rec)

        return recommendations

    def _analyze_model_optimization(
        self,
        ts_data: List,
        mean_cost: float,
        user_id: str,
        provider: Provider = Provider.ANTHROPIC_API,
        region: Optional[Region] = None,
        current_model: str = "claude-3-5-sonnet",
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze model choice optimization"""
        recommendations = []

        # Get pricing for different models in the same region/provider
        pricing = self.pricing_manager.get_pricing(provider, region)

        # Compare current model with Haiku
        if current_model in pricing and "claude-3-5-haiku" in pricing:
            current_input_rate = pricing[current_model]["input"]
            haiku_input_rate = pricing["claude-3-5-haiku"]["input"]

            # Haiku is typically 80%+ cheaper
            savings_percent = (current_input_rate - haiku_input_rate) / current_input_rate * 100

            # Estimate 30% of tasks could use cheaper model
            potential_savings = (mean_cost * regional_multiplier) * (savings_percent / 100) * 0.30

            if potential_savings > 1.0:
                monthly_savings = potential_savings * 30

            rec = Recommendation(
                type=RecommendationType.MODEL_DOWNGRADE,
                title="Use Haiku for Simple Tasks",
                description="Haiku is 85% cheaper than Sonnet for simple tasks. "
                           "Implement smart model selection based on task complexity.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=25,
                implementation_effort_hours=12,
                roi_score=monthly_savings * 12 / 12,
                implementation_steps=[
                    "Categorize your tasks by complexity",
                    "Route simple tasks to Haiku, complex to Sonnet",
                    "Implement fallback logic",
                    "Test accuracy on simple tasks",
                    "Monitor quality metrics"
                ],
                estimated_implementation_time="2-3 days",
                confidence_score=0.8
            )
            recommendations.append(rec)

        return recommendations

    def _analyze_file_format_opportunities(
        self,
        ts_data: List,
        mean_cost: float,
        user_id: str,
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze file format optimization"""
        recommendations = []

        # If heavy PDF usage is detected (via file format data)
        # PDFs via URL cost 3.6x more than disk
        # Estimate 20% of file operations might be PDFs
        # Account for regional multiplier
        estimated_pdf_cost = (mean_cost * regional_multiplier) * 0.20
        potential_savings = estimated_pdf_cost * 0.72  # Move to disk = 72% savings

        if potential_savings > 1.0:
            monthly_savings = potential_savings * 30

            rec = Recommendation(
                type=RecommendationType.FILE_FORMAT_OPTIMIZATION,
                title="Move PDFs from URLs to Disk Storage",
                description="PDF files fetched from URLs cost 3.6x more than disk storage. "
                           "Store PDFs locally and pass file paths instead.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=20,
                implementation_effort_hours=6,
                roi_score=monthly_savings * 12 / 6,
                implementation_steps=[
                    "Audit current PDF sources (URL vs disk)",
                    "Set up local storage for PDFs",
                    "Update your code to use file paths",
                    "Test with sample PDFs",
                    "Deploy and monitor"
                ],
                estimated_implementation_time="1 day",
                confidence_score=0.75
            )
            recommendations.append(rec)

        return recommendations

    def _analyze_mcp_efficiency(
        self,
        ts_data: List,
        mean_cost: float,
        user_id: str,
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze MCP integration efficiency"""
        recommendations = []

        # MCPs can have 10-100x overhead
        # Estimate 15% of spend is MCP-related
        # Account for regional multiplier
        estimated_mcp_cost = (mean_cost * regional_multiplier) * 0.15
        potential_savings = estimated_mcp_cost * 0.30  # 30% optimization

        if potential_savings > 1.0:
            monthly_savings = potential_savings * 30

            rec = Recommendation(
                type=RecommendationType.MCP_EFFICIENCY,
                title="Optimize MCP Usage Patterns",
                description="Some MCP calls have significant overhead. "
                           "Batch MCP calls and minimize repeated integrations.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=15,
                implementation_effort_hours=8,
                roi_score=monthly_savings * 12 / 8,
                implementation_steps=[
                    "Identify most-used MCPs",
                    "Profile MCP call patterns",
                    "Batch related MCP calls",
                    "Cache MCP results where applicable",
                    "Monitor for improvements"
                ],
                estimated_implementation_time="1-2 days",
                confidence_score=0.7
            )
            recommendations.append(rec)

        return recommendations

    def _analyze_cache_opportunities(
        self,
        ts_data: List,
        mean_cost: float,
        user_id: str,
        regional_multiplier: float = 1.0
    ) -> List[Recommendation]:
        """Analyze prompt caching opportunities"""
        recommendations = []

        # Prompt caching gives 90% discount on cached tokens
        # Estimate 25% of usage could benefit from caching
        # Account for regional multiplier
        potential_savings = (mean_cost * regional_multiplier) * 0.25 * 0.90

        if potential_savings > 1.0:
            monthly_savings = potential_savings * 30

            rec = Recommendation(
                type=RecommendationType.CACHE_OPTIMIZATION,
                title="Enable Prompt Caching",
                description="Reuse system prompts and context with prompt caching "
                           "to get 90% discount on cached token consumption.",
                estimated_savings_usd=monthly_savings,
                estimated_savings_percent=22,
                implementation_effort_hours=10,
                roi_score=monthly_savings * 12 / 10,
                implementation_steps=[
                    "Identify reusable prompts and context",
                    "Implement cache_control parameters",
                    "Test cache behavior",
                    "Monitor cache hit rates",
                    "Adjust caching strategy as needed"
                ],
                estimated_implementation_time="2-3 days",
                confidence_score=0.8
            )
            recommendations.append(rec)

        return recommendations

    def _save_recommendations(self, user_id: str, recommendations: List[Recommendation]):
        """Save recommendations to database"""
        with self.db:
            for rec in recommendations:
                try:
                    self.db.cursor.execute("""
                        INSERT INTO recommendations (
                            id, user_id, recommendation_type, title, description,
                            estimated_savings_usd, estimated_savings_percent,
                            implementation_effort_hours, roi_score, implementation_steps,
                            estimated_implementation_time, implemented,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rec.__dict__.get('id', ''),  # Will be generated by DB
                        user_id,
                        rec.type.value,
                        rec.title,
                        rec.description,
                        rec.estimated_savings_usd,
                        rec.estimated_savings_percent,
                        rec.implementation_effort_hours,
                        rec.roi_score,
                        str(rec.implementation_steps),
                        rec.estimated_implementation_time,
                        0,
                        datetime.utcnow().isoformat(),
                        datetime.utcnow().isoformat()
                    ))
                    self.db.conn.commit()
                except Exception as e:
                    print(f"Error saving recommendation: {e}")

    def get_top_recommendations(
        self,
        user_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top recommendations ranked by ROI"""
        with self.db:
            self.db.cursor.execute("""
                SELECT * FROM recommendations
                WHERE user_id = ? AND implemented = 0
                ORDER BY roi_score DESC
                LIMIT ?
            """, (user_id, limit))

            recommendations = []
            for row in self.db.cursor.fetchall():
                recommendations.append({
                    "id": row["id"],
                    "type": row["recommendation_type"],
                    "title": row["title"],
                    "description": row["description"],
                    "estimated_savings": row["estimated_savings_usd"],
                    "roi_score": row["roi_score"],
                    "effort_hours": row["implementation_effort_hours"],
                    "implementation_time": row["estimated_implementation_time"]
                })

            return recommendations

    def mark_recommendation_implemented(self, recommendation_id: str, actual_savings: Optional[float] = None) -> bool:
        """Mark a recommendation as implemented"""
        try:
            with self.db:
                self.db.cursor.execute("""
                    UPDATE recommendations
                    SET implemented = 1, implemented_at = ?, actual_savings_usd = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), actual_savings, recommendation_id))
                self.db.conn.commit()
                return True
        except Exception as e:
            print(f"Error updating recommendation: {e}")
            return False
