"""
Enhanced recommendations engine using detailed token classification.
Generates targeted recommendations based on granular token consumption patterns.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .detailed_token_classifier import (
    DetailedTokenClassifier,
    DetailedTokenBreakdown,
    TokenSource,
    TokenComplexity,
    TaskCategory,
    InputSource,
    TimeWindow,
    OutputType,
)
from .recommendations_engine import Recommendation, RecommendationType


@dataclass
class DetailedRecommendation:
    """Enhanced recommendation with detailed cost driver analysis"""
    recommendation: Recommendation
    cost_drivers: List[Dict[str, Any]]
    optimization_opportunities: List[Dict[str, Any]]
    effectiveness_score: float  # 0-1, how much impact this rec will have
    prerequisite_recs: List[str] = None

    def __post_init__(self):
        if self.prerequisite_recs is None:
            self.prerequisite_recs = []


class DetailedRecommendationsAnalyzer:
    """Analyze detailed token patterns to generate targeted recommendations"""

    def __init__(self):
        self.classifier = DetailedTokenClassifier()

    def analyze_token_patterns(
        self,
        breakdowns: List[DetailedTokenBreakdown]
    ) -> Dict[str, Any]:
        """Analyze patterns across multiple token breakdowns"""

        if not breakdowns:
            return {"error": "No token data to analyze"}

        # Classify each operation
        classifications = [
            self.classifier.classify_operation(b)
            for b in breakdowns
        ]

        # Aggregate patterns
        patterns = self._aggregate_patterns(classifications, breakdowns)

        # Identify cost drivers
        drivers = self._identify_top_drivers(classifications)

        # Calculate consumption statistics
        stats = self._calculate_consumption_stats(breakdowns)

        return {
            "total_operations": len(classifications),
            "total_effective_tokens": sum(c["costs"]["total_effective_tokens"] for c in classifications),
            "patterns": patterns,
            "top_cost_drivers": drivers,
            "consumption_statistics": stats,
            "recommendations_available": self._estimate_recommendations_available(drivers, patterns)
        }

    def generate_detailed_recommendations(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        min_impact: float = 0.5
    ) -> List[DetailedRecommendation]:
        """Generate recommendations from detailed token analysis"""

        if not breakdowns:
            return []

        analysis = self.analyze_token_patterns(breakdowns)
        recommendations = []

        # 1. Vision token optimization
        vision_recs = self._recommend_vision_optimization(breakdowns, analysis)
        recommendations.extend(vision_recs)

        # 2. Input source optimization
        source_recs = self._recommend_input_source_optimization(breakdowns, analysis)
        recommendations.extend(source_recs)

        # 3. Context window optimization
        context_recs = self._recommend_context_optimization(breakdowns, analysis)
        recommendations.extend(context_recs)

        # 4. Cache effectiveness
        cache_recs = self._recommend_cache_improvement(breakdowns, analysis)
        recommendations.extend(cache_recs)

        # 5. Task complexity reduction
        complexity_recs = self._recommend_complexity_reduction(breakdowns, analysis)
        recommendations.extend(complexity_recs)

        # 6. Tool call optimization
        tool_recs = self._recommend_tool_optimization(breakdowns, analysis)
        recommendations.extend(tool_recs)

        # 7. Time-of-day optimization
        time_recs = self._recommend_time_optimization(breakdowns, analysis)
        recommendations.extend(time_recs)

        # 8. Batch optimization
        batch_recs = self._recommend_batch_optimization(breakdowns, analysis)
        recommendations.extend(batch_recs)

        # Filter by impact and sort
        recommendations = [
            r for r in recommendations
            if r.effectiveness_score >= min_impact
        ]
        recommendations.sort(key=lambda r: r.recommendation.roi_score, reverse=True)

        return recommendations

    def _aggregate_patterns(
        self,
        classifications: List[Dict[str, Any]],
        breakdowns: List[DetailedTokenBreakdown]
    ) -> Dict[str, Any]:
        """Aggregate consumption patterns across operations"""

        patterns = {
            "input_sources": {},
            "task_categories": {},
            "complexity_levels": {},
            "time_windows": {},
            "cache_effectiveness": [],
            "vision_usage": 0,
            "tool_call_frequency": 0,
            "context_usage_percent": [],
        }

        for breakdown in breakdowns:
            # Track input sources
            source = breakdown.input_source_method.value
            patterns["input_sources"][source] = patterns["input_sources"].get(source, 0) + 1

            # Track task categories
            category = breakdown.task_category.value
            patterns["task_categories"][category] = patterns["task_categories"].get(category, 0) + 1

            # Track complexity
            complexity = breakdown.complexity_level.value
            patterns["complexity_levels"][complexity] = patterns["complexity_levels"].get(complexity, 0) + 1

            # Track time windows
            time_window = breakdown.time_window.value
            patterns["time_windows"][time_window] = patterns["time_windows"].get(time_window, 0) + 1

            # Track cache effectiveness
            patterns["cache_effectiveness"].append(breakdown.cache_effectiveness)

            # Track vision usage
            if breakdown.vision_tokens > 0:
                patterns["vision_usage"] += breakdown.vision_tokens

            # Track tool calls
            patterns["tool_call_frequency"] += breakdown.tool_calls

            # Track context usage
            patterns["context_usage_percent"].append(breakdown.context_window_used_percent)

        return patterns

    def _identify_top_drivers(
        self,
        classifications: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify top cost drivers across operations"""

        all_drivers = []
        driver_impact = {}

        for classification in classifications:
            for driver in classification["cost_drivers"]:
                driver_type = driver.get("driver", "unknown")
                multiplier = driver.get("multiplier", 1.0)

                if driver_type not in driver_impact:
                    driver_impact[driver_type] = {
                        "count": 0,
                        "total_multiplier": 0,
                        "samples": []
                    }

                driver_impact[driver_type]["count"] += 1
                driver_impact[driver_type]["total_multiplier"] += multiplier
                driver_impact[driver_type]["samples"].append(driver)

        # Sort by impact
        ranked = []
        for driver_type, impact in sorted(driver_impact.items(), key=lambda x: x[1]["total_multiplier"], reverse=True):
            ranked.append({
                "driver": driver_type,
                "frequency": impact["count"],
                "average_multiplier": impact["total_multiplier"] / impact["count"],
                "impact_score": impact["total_multiplier"],
            })

        return ranked

    def _calculate_consumption_stats(
        self,
        breakdowns: List[DetailedTokenBreakdown]
    ) -> Dict[str, Any]:
        """Calculate consumption statistics"""

        total_input = sum(b.total_input_tokens for b in breakdowns)
        total_output = sum(b.total_output_tokens for b in breakdowns)
        total_vision = sum(b.vision_tokens for b in breakdowns)
        total_cached_read = sum(b.cache_tokens_read for b in breakdowns)
        total_cached_write = sum(b.cache_tokens_written for b in breakdowns)

        avg_cache_effectiveness = sum(b.cache_effectiveness for b in breakdowns) / len(breakdowns)
        avg_context_usage = sum(b.context_window_used_percent for b in breakdowns) / len(breakdowns)
        avg_temperature = sum(b.temperature for b in breakdowns) / len(breakdowns)

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_vision_tokens": total_vision,
            "total_cached_read": total_cached_read,
            "total_cached_write": total_cached_write,
            "input_output_ratio": total_input / total_output if total_output > 0 else 0,
            "average_cache_effectiveness": avg_cache_effectiveness,
            "average_context_usage_percent": avg_context_usage * 100,
            "average_temperature": avg_temperature,
            "operations_with_vision": sum(1 for b in breakdowns if b.vision_tokens > 0),
            "operations_with_tools": sum(1 for b in breakdowns if b.tool_calls > 0),
            "batched_operations": sum(1 for b in breakdowns if b.is_batched),
        }

    def _estimate_recommendations_available(
        self,
        drivers: List[Dict[str, Any]],
        patterns: Dict[str, Any]
    ) -> List[str]:
        """Estimate what types of recommendations are available"""

        available = []

        # Check for vision optimization opportunity
        if patterns.get("vision_usage", 0) > 5000:
            available.append("vision_optimization")

        # Check for input source opportunity
        expensive_sources = ["url_https_image", "url_https_pdf", "browser_scrape", "mcp_skill"]
        if any(source in patterns["input_sources"] for source in expensive_sources):
            available.append("input_source_optimization")

        # Check for context window opportunity
        if any(usage > 0.7 for usage in patterns.get("context_usage_percent", [])):
            available.append("context_reduction")

        # Check for cache opportunity
        avg_cache_eff = sum(patterns.get("cache_effectiveness", [0])) / max(len(patterns.get("cache_effectiveness", [1])), 1)
        if avg_cache_eff < 0.3:
            available.append("cache_improvement")

        # Check for complexity opportunity
        if patterns["complexity_levels"].get("very_complex", 0) > 0:
            available.append("complexity_reduction")

        # Check for tool optimization
        if patterns.get("tool_call_frequency", 0) > 20:
            available.append("tool_optimization")

        # Check for time optimization
        if patterns["time_windows"].get("peak", 0) > len(patterns["time_windows"]) * 0.3:
            available.append("time_optimization")

        return available

    def _recommend_vision_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend vision token optimization"""

        recs = []
        vision_operations = [b for b in breakdowns if b.vision_tokens > 0]

        if not vision_operations:
            return recs

        total_vision = sum(b.vision_tokens for b in vision_operations)
        if total_vision < 5000:  # Not significant
            return recs

        # Estimate savings from resolution reduction
        current_cost = total_vision * 3.6  # Vision token premium
        savings_percent = 0.40  # 40% savings from resolution reduction
        estimated_savings = current_cost * savings_percent

        rec = Recommendation(
            type=RecommendationType.FILE_FORMAT_OPTIMIZATION,
            title=f"Optimize Image Processing ({total_vision:,} vision tokens)",
            description=f"You're using {total_vision:,} vision tokens across {len(vision_operations)} operations. "
                       f"Reducing image resolution and count could save 30-50%.",
            estimated_savings_usd=estimated_savings,
            estimated_savings_percent=savings_percent * 100,
            implementation_effort_hours=4,
            roi_score=estimated_savings * 12 / 4,
            implementation_steps=[
                "Audit current image resolution requirements",
                "Implement image downsampling",
                "Use JPEG instead of PNG where possible",
                "Batch multiple images into single requests",
                "Test quality impact on results"
            ],
            estimated_implementation_time="1-2 days",
            confidence_score=0.85
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "vision_tokens", "impact": f"{total_vision:,} tokens"}],
            optimization_opportunities=[
                {"opportunity": "Resolution reduction", "potential_savings": estimated_savings * 0.5},
                {"opportunity": "Format optimization", "potential_savings": estimated_savings * 0.3},
                {"opportunity": "Batch processing", "potential_savings": estimated_savings * 0.2}
            ],
            effectiveness_score=0.85
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_input_source_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend input source optimization"""

        recs = []
        input_sources = analysis["patterns"]["input_sources"]

        # Identify expensive sources
        expensive = {
            "browser_scrape": 55.0,
            "mcp_skill": 25.0,
            "github_api": 8.0,
            "url_https_image": 4.2,
            "url_https_pdf": 3.6,
        }

        total_expensive_ops = sum(
            count for source, count in input_sources.items()
            if source in expensive
        )

        if total_expensive_ops == 0:
            return recs

        # Calculate potential savings
        avg_cost_per_op = 50.0  # Rough estimate
        total_expensive_cost = total_expensive_ops * avg_cost_per_op * 0.4  # 40% of cost is from expensive sources
        savings_from_switching = total_expensive_cost * 0.6  # 60% savings by switching to cheaper alternatives

        rec = Recommendation(
            type=RecommendationType.OPERATION_ELIMINATION,
            title=f"Reduce Expensive Input Sources ({total_expensive_ops} operations)",
            description="You're using expensive input sources (browser scraping, MCP skills, URLs). "
                       "Using local files or pasted text instead could reduce costs significantly.",
            estimated_savings_usd=savings_from_switching,
            estimated_savings_percent=40,
            implementation_effort_hours=12,
            roi_score=savings_from_switching * 12 / 12,
            implementation_steps=[
                "Catalog current input sources",
                "Identify which could use local files instead",
                "Implement pre-fetching/caching for local storage",
                "Set up file serving infrastructure if needed",
                "Migrate operations batch by batch"
            ],
            estimated_implementation_time="3-5 days",
            confidence_score=0.75
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[
                {
                    "source": source,
                    "count": input_sources.get(source, 0),
                    "multiplier": expensive.get(source, 1.0)
                }
                for source in expensive if source in input_sources
            ],
            optimization_opportunities=[
                {"source": "browser_scrape", "alternative": "API", "savings": 0.95},
                {"source": "mcp_skill", "alternative": "batch_mcp", "savings": 0.40},
                {"source": "url_https_pdf", "alternative": "local_pdf", "savings": 0.67},
            ],
            effectiveness_score=0.75
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_context_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend context window optimization"""

        recs = []
        context_usage = analysis["patterns"]["context_usage_percent"]

        high_usage_ops = [b for b in breakdowns if b.context_window_used_percent > 0.7]

        if not high_usage_ops:
            return recs

        avg_high_usage = sum(b.context_window_used_percent for b in high_usage_ops) / len(high_usage_ops)
        total_tokens_high_usage = sum(b.total_input_tokens for b in high_usage_ops)

        # Estimate 20-30% reduction possible
        potential_reduction = total_tokens_high_usage * 0.25
        estimated_savings = potential_reduction * 0.003  # Rough cost

        rec = Recommendation(
            type=RecommendationType.OPERATION_ELIMINATION,
            title=f"Reduce Context Window Usage ({avg_high_usage*100:.0f}% average)",
            description=f"You're using {avg_high_usage*100:.0f}% of context window. "
                       f"Removing unnecessary context or splitting requests could save 20-30%.",
            estimated_savings_usd=estimated_savings,
            estimated_savings_percent=25,
            implementation_effort_hours=8,
            roi_score=estimated_savings * 12 / 8,
            implementation_steps=[
                "Audit context inclusion patterns",
                "Remove redundant/historical context",
                "Implement summarization for long inputs",
                "Split complex requests into simpler ones",
                "Test accuracy impact"
            ],
            estimated_implementation_time="2-3 days",
            confidence_score=0.7
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "context_window", "usage_percent": avg_high_usage * 100}],
            optimization_opportunities=[
                {"opportunity": "Remove redundant context", "savings": potential_reduction * 0.5},
                {"opportunity": "Summarize inputs", "savings": potential_reduction * 0.3},
                {"opportunity": "Request splitting", "savings": potential_reduction * 0.2}
            ],
            effectiveness_score=0.7
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_cache_improvement(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend cache effectiveness improvement"""

        recs = []
        cache_effectiveness = analysis["consumption_statistics"]["average_cache_effectiveness"]

        if cache_effectiveness > 0.5:  # Already good
            return recs

        # Calculate potential cache savings (90% discount on reads)
        total_tokens = analysis["consumption_statistics"]["total_input_tokens"]
        potential_cached = total_tokens * 0.5  # Assume 50% could be cached
        current_cached = analysis["consumption_statistics"]["total_cached_read"]
        additional_cacheable = potential_cached - current_cached

        # Cache gives 90% discount
        current_cache_savings = current_cached * 0.9
        potential_total_savings = potential_cached * 0.9
        additional_savings = potential_total_savings - current_cache_savings

        rec = Recommendation(
            type=RecommendationType.CACHE_OPTIMIZATION,
            title=f"Improve Cache Hit Rate ({cache_effectiveness*100:.0f}% current)",
            description="Standardizing prompts and reusing cached context could achieve 50-70% cache hit rates, "
                       "saving 45% on those tokens.",
            estimated_savings_usd=additional_savings * 0.003,  # Rough cost
            estimated_savings_percent=(additional_savings / total_tokens * 100) if total_tokens > 0 else 0,
            implementation_effort_hours=6,
            roi_score=(additional_savings * 0.003 * 12) / 6,
            implementation_steps=[
                "Analyze prompt patterns for reuse opportunities",
                "Standardize system prompts",
                "Implement prompt template library",
                "Enable prompt caching across requests",
                "Monitor cache hit rate improvements"
            ],
            estimated_implementation_time="1-2 days",
            confidence_score=0.8
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "low_cache_hit_rate", "current": cache_effectiveness * 100}],
            optimization_opportunities=[
                {"opportunity": "Standardize prompts", "potential_savings": additional_savings * 0.5},
                {"opportunity": "Reuse context", "potential_savings": additional_savings * 0.3},
                {"opportunity": "Template library", "potential_savings": additional_savings * 0.2}
            ],
            effectiveness_score=0.8
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_complexity_reduction(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend task complexity reduction"""

        recs = []
        complexity_levels = analysis["patterns"]["complexity_levels"]

        complex_ops = [
            b for b in breakdowns
            if b.complexity_level in [TokenComplexity.COMPLEX, TokenComplexity.VERY_COMPLEX]
        ]

        if not complex_ops:
            return recs

        # Complex operations have 1.4-1.6x multiplier
        total_complex_tokens = sum(b.total_input_tokens for b in complex_ops)
        multiplier_overhead = 0.4  # 40% overhead
        estimated_savings = total_complex_tokens * multiplier_overhead * 0.003

        rec = Recommendation(
            type=RecommendationType.BATCH_OPERATIONS,
            title=f"Simplify Complex Operations ({len(complex_ops)} operations)",
            description="Breaking down complex operations into simpler subtasks could reduce processing overhead "
                       "and improve accuracy.",
            estimated_savings_usd=estimated_savings,
            estimated_savings_percent=20,
            implementation_effort_hours=10,
            roi_score=estimated_savings * 12 / 10,
            implementation_steps=[
                "Analyze complex operations",
                "Identify decomposition opportunities",
                "Split into step-by-step workflows",
                "Add intermediate validation",
                "Verify cost improvements"
            ],
            estimated_implementation_time="3-5 days",
            confidence_score=0.65
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "complexity", "complex_ops": len(complex_ops)}],
            optimization_opportunities=[
                {"opportunity": "Task decomposition", "savings": estimated_savings * 0.6},
                {"opportunity": "Step-by-step workflow", "savings": estimated_savings * 0.4}
            ],
            effectiveness_score=0.65
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_tool_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend tool call optimization"""

        recs = []
        tool_frequency = analysis["consumption_statistics"]["operations_with_tools"]

        if tool_frequency < 10:
            return recs

        # Tool calls add ~1.5x multiplier
        avg_tools_per_op = analysis["consumption_statistics"]["total_tool_call_overhead"] if "total_tool_call_overhead" in analysis["consumption_statistics"] else 0
        total_tokens = analysis["consumption_statistics"]["total_input_tokens"]

        # Estimate 20-30% reduction from batching tools
        estimated_savings = total_tokens * 0.25 * 0.003

        rec = Recommendation(
            type=RecommendationType.BATCH_OPERATIONS,
            title=f"Optimize Tool Calls ({tool_frequency} operations use tools)",
            description="Batching tool calls and reducing unnecessary invocations could save 20-30% on overhead.",
            estimated_savings_usd=estimated_savings,
            estimated_savings_percent=20,
            implementation_effort_hours=5,
            roi_score=estimated_savings * 12 / 5,
            implementation_steps=[
                "Profile tool call patterns",
                "Identify redundant calls",
                "Batch compatible tool invocations",
                "Cache tool results where possible",
                "Verify output quality"
            ],
            estimated_implementation_time="1-2 days",
            confidence_score=0.7
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "tool_calls", "frequency": tool_frequency}],
            optimization_opportunities=[
                {"opportunity": "Batch tool calls", "savings": estimated_savings * 0.6},
                {"opportunity": "Result caching", "savings": estimated_savings * 0.4}
            ],
            effectiveness_score=0.7
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_time_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend time-of-day optimization"""

        recs = []
        time_windows = analysis["patterns"]["time_windows"]

        peak_ops = time_windows.get("peak", 0)
        total_ops = sum(time_windows.values())

        if peak_ops < total_ops * 0.2:  # Less than 20% in peak
            return recs

        # Peak hours have 1.3x multiplier, off-peak 0.7x
        # Savings = 1.3x - 0.7x = 0.6x, or 46% reduction
        estimated_savings_percent = 30  # Conservative estimate

        rec = Recommendation(
            type=RecommendationType.OFF_PEAK_SCHEDULING,
            title=f"Schedule During Off-Peak Hours ({peak_ops} peak operations)",
            description=f"{peak_ops} of your operations run during peak hours (5-10 PM). "
                       f"Shifting to off-peak (10 PM - 6 AM) would save ~30%.",
            estimated_savings_usd=0.0,  # Would be calculated with actual costs
            estimated_savings_percent=estimated_savings_percent,
            implementation_effort_hours=3,
            roi_score=999,  # High ROI for low effort
            implementation_steps=[
                "Identify which operations can be scheduled",
                "Implement scheduling logic",
                "Route to off-peak windows automatically",
                "Monitor execution times"
            ],
            estimated_implementation_time="Few hours",
            confidence_score=0.8
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "peak_hours", "peak_ops": peak_ops}],
            optimization_opportunities=[
                {"opportunity": "Off-peak scheduling", "savings_percent": 30}
            ],
            effectiveness_score=0.8
        )
        recs.append(detailed_rec)

        return recs

    def _recommend_batch_optimization(
        self,
        breakdowns: List[DetailedTokenBreakdown],
        analysis: Dict[str, Any]
    ) -> List[DetailedRecommendation]:
        """Recommend batch optimization"""

        recs = []
        batched_ops = analysis["consumption_statistics"]["batched_operations"]
        total_ops = len(breakdowns)

        if batched_ops > total_ops * 0.5:  # Already batching well
            return recs

        # Batching gives 5% discount per additional item
        potential_batch_size = 5  # Average batch of 5
        potential_discount = (potential_batch_size - 1) * 0.05  # 20% discount

        rec = Recommendation(
            type=RecommendationType.BATCH_OPERATIONS,
            title=f"Batch More Operations ({total_ops - batched_ops} sequential operations)",
            description=f"Only {batched_ops}/{total_ops} operations are batched. "
                       f"Grouping more operations could save {potential_discount*100:.0f}%.",
            estimated_savings_usd=0.0,
            estimated_savings_percent=potential_discount * 100,
            implementation_effort_hours=4,
            roi_score=999,
            implementation_steps=[
                "Analyze operation patterns",
                "Identify batch opportunities",
                "Implement grouping logic",
                "Monitor batch effectiveness"
            ],
            estimated_implementation_time="1-2 days",
            confidence_score=0.7
        )

        detailed_rec = DetailedRecommendation(
            recommendation=rec,
            cost_drivers=[{"driver": "sequential_ops", "count": total_ops - batched_ops}],
            optimization_opportunities=[
                {"opportunity": "Default batching", "potential_discount": potential_discount}
            ],
            effectiveness_score=0.7
        )
        recs.append(detailed_rec)

        return recs
