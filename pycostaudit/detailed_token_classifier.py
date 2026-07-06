"""
Ultra-detailed token consumption classification.
Provides granular tracking across 50+ dimensions for precise cost attribution.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class TokenSource(Enum):
    """Where tokens come from"""
    USER_INPUT = "user_input"
    SYSTEM_PROMPT = "system_prompt"
    CONTEXT_WINDOW = "context_window"
    TOOL_OUTPUT = "tool_output"
    PREVIOUS_RESPONSE = "previous_response"
    CACHED_CONTENT = "cached_content"
    FILE_CONTENT = "file_content"
    API_RESPONSE = "api_response"
    IMAGE_DATA = "image_data"
    VIDEO_DATA = "video_data"


class TokenComplexity(Enum):
    """Complexity level of operation"""
    TRIVIAL = "trivial"  # < 100 tokens
    SIMPLE = "simple"  # 100-500 tokens
    MODERATE = "moderate"  # 500-2000 tokens
    COMPLEX = "complex"  # 2000-10000 tokens
    VERY_COMPLEX = "very_complex"  # > 10000 tokens


class TaskCategory(Enum):
    """High-level task categories"""
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TEXT_GENERATION = "text_generation"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    REASONING = "reasoning"
    CREATIVE = "creative"
    IMAGE_ANALYSIS = "image_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    TESTING = "testing"


class FileType(Enum):
    """Detailed file type classification"""
    # Text
    TEXT_PLAIN = "text_plain"
    TEXT_MARKDOWN = "text_markdown"
    TEXT_JSON = "text_json"
    TEXT_XML = "text_xml"
    TEXT_YAML = "text_yaml"
    TEXT_CSV = "text_csv"
    TEXT_LOG = "text_log"

    # Code
    CODE_PYTHON = "code_python"
    CODE_JAVASCRIPT = "code_javascript"
    CODE_TYPESCRIPT = "code_typescript"
    CODE_RUST = "code_rust"
    CODE_GO = "code_go"
    CODE_JAVA = "code_java"
    CODE_SQL = "code_sql"
    CODE_OTHER = "code_other"

    # Documents
    PDF_DOCUMENT = "pdf_document"
    HTML_DOCUMENT = "html_document"
    WORD_DOCUMENT = "word_document"
    MARKDOWN_DOCUMENT = "markdown_document"

    # Images
    IMAGE_PNG = "image_png"
    IMAGE_JPG = "image_jpg"
    IMAGE_GIF = "image_gif"
    IMAGE_SVG = "image_svg"

    # Data
    DATA_PARQUET = "data_parquet"
    DATA_ARROW = "data_arrow"
    DATA_PROTOBUF = "data_protobuf"


class InputSource(Enum):
    """How input was provided"""
    PASTED_TEXT = "pasted_text"  # 1.0x
    LOCAL_FILE = "local_file"  # 1.0x
    LOCAL_FILE_PDF = "local_file_pdf"  # 1.2x
    LOCAL_FILE_IMAGE = "local_file_image"  # 1.0x (but higher token count)
    URL_HTTP = "url_http"  # 2.5x baseline
    URL_HTTPS_PDF = "url_https_pdf"  # 3.6x
    URL_HTTPS_IMAGE = "url_https_image"  # 4.2x
    URL_HTTPS_HTML = "url_https_html"  # 2.8x
    API_ENDPOINT = "api_endpoint"  # 1.5x
    DATABASE_QUERY = "database_query"  # 2.0x
    MCP_SKILL = "mcp_skill"  # 10-100x
    GITHUB_API = "github_api"  # 4-12x
    BROWSER_SCRAPE = "browser_scrape"  # 55x


class OutputType(Enum):
    """Type of output generated"""
    TEXT_RESPONSE = "text_response"
    CODE_GENERATION = "code_generation"
    FUNCTION_CALL = "function_call"
    TOOL_USE = "tool_use"
    STREAMING = "streaming"  # 1.2x overhead
    JSON_STRUCTURED = "json_structured"  # 1.1x
    IMAGE_GENERATION = "image_generation"  # N/A (separate pricing)
    FILE_GENERATION = "file_generation"


class TimeWindow(Enum):
    """Time-of-day pricing multiplier"""
    OFF_PEAK = "off_peak"  # 10 PM - 6 AM: 0.7x
    STANDARD = "standard"  # 6 AM - 5 PM: 1.0x
    PEAK = "peak"  # 5 PM - 10 PM: 1.3x
    WEEKEND = "weekend"  # Saturday/Sunday: 0.85x


@dataclass
class DetailedTokenBreakdown:
    """Ultra-detailed token consumption breakdown"""
    timestamp: datetime
    operation_id: str
    user_id: str
    session_id: Optional[str]

    # Core metrics
    total_input_tokens: int
    total_output_tokens: int

    # Input breakdown by source
    input_by_source: Dict[str, int] = field(default_factory=dict)  # Maps TokenSource -> count

    # Input breakdown by file type
    input_by_file_type: Dict[str, int] = field(default_factory=dict)  # Maps FileType -> count

    # Input delivery method
    input_source_method: InputSource = InputSource.PASTED_TEXT
    input_source_cost_multiplier: float = 1.0

    # Complexity classification
    complexity_level: TokenComplexity = TokenComplexity.SIMPLE

    # Task category
    task_category: TaskCategory = TaskCategory.CODE_GENERATION

    # Caching info
    cache_tokens_written: int = 0  # Cost 1.25x
    cache_tokens_read: int = 0  # Cost 0.1x (90% discount)
    cache_effectiveness: float = 0.0  # 0-1, percentage of tokens from cache

    # Vision/image processing
    vision_tokens: int = 0  # Cost 3.6x
    image_count: int = 0
    image_resolution: str = ""  # "1024x1024", "4096x4096", etc.
    image_processing_type: str = ""  # "analysis", "extraction", "description"

    # Tool/function usage
    tool_calls: int = 0
    tool_use_token_overhead: float = 0.0  # Additional tokens for tool calls
    tools_called: List[str] = field(default_factory=list)

    # Output characteristics
    output_type: OutputType = OutputType.TEXT_RESPONSE
    output_streaming: bool = False  # True = 1.2x overhead
    output_structured: bool = False  # JSON/XML = 1.1x
    output_code_percentage: float = 0.0  # Percent of output that's code

    # Provider and region
    provider: str = "anthropic"
    region: str = "us-east-1"
    model: str = "claude-3-5-sonnet"

    # Temporal info
    time_window: TimeWindow = TimeWindow.STANDARD
    time_multiplier: float = 1.0

    # Context window usage
    context_window_size: int = 200000  # Tokens available
    context_window_used_percent: float = 0.0  # Percentage of context used

    # Quality/accuracy indicators
    temperature: float = 0.7
    max_tokens_requested: int = 0
    actual_tokens_generated: int = 0
    stop_reason: str = ""  # "end_turn", "stop_sequence", "max_tokens"

    # Batch/concurrency info
    batch_size: int = 1  # If part of batch, size of batch
    concurrent_operations: int = 1
    is_batched: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class DetailedTokenClassifier:
    """Ultra-detailed token classification and cost calculation"""

    # Input source cost multipliers
    INPUT_SOURCE_MULTIPLIERS = {
        InputSource.PASTED_TEXT: 1.0,
        InputSource.LOCAL_FILE: 1.0,
        InputSource.LOCAL_FILE_PDF: 1.2,
        InputSource.LOCAL_FILE_IMAGE: 1.0,
        InputSource.URL_HTTP: 2.5,
        InputSource.URL_HTTPS_PDF: 3.6,
        InputSource.URL_HTTPS_IMAGE: 4.2,
        InputSource.URL_HTTPS_HTML: 2.8,
        InputSource.API_ENDPOINT: 1.5,
        InputSource.DATABASE_QUERY: 2.0,
        InputSource.MCP_SKILL: 25.0,  # Average 10-100x
        InputSource.GITHUB_API: 8.0,  # Average 4-12x
        InputSource.BROWSER_SCRAPE: 55.0,
    }

    # Task complexity cost factors
    COMPLEXITY_FACTORS = {
        TokenComplexity.TRIVIAL: (1.0, "Minimal processing needed"),
        TokenComplexity.SIMPLE: (1.1, "Straightforward task"),
        TokenComplexity.MODERATE: (1.2, "Medium complexity processing"),
        TokenComplexity.COMPLEX: (1.4, "Complex reasoning required"),
        TokenComplexity.VERY_COMPLEX: (1.6, "Extensive analysis/generation"),
    }

    # Task category efficiency
    TASK_EFFICIENCY = {
        TaskCategory.DATA_ANALYSIS: 1.0,
        TaskCategory.CODE_GENERATION: 1.3,
        TaskCategory.CODE_REVIEW: 0.9,
        TaskCategory.TEXT_GENERATION: 1.1,
        TaskCategory.TRANSLATION: 1.2,
        TaskCategory.SUMMARIZATION: 0.8,
        TaskCategory.EXTRACTION: 0.7,
        TaskCategory.CLASSIFICATION: 0.6,
        TaskCategory.REASONING: 1.5,
        TaskCategory.CREATIVE: 1.4,
        TaskCategory.IMAGE_ANALYSIS: 2.0,
        TaskCategory.DOCUMENT_PROCESSING: 1.3,
        TaskCategory.RESEARCH: 1.4,
        TaskCategory.DEBUGGING: 1.2,
        TaskCategory.TESTING: 1.1,
    }

    def classify_operation(
        self,
        breakdown: DetailedTokenBreakdown
    ) -> Dict[str, Any]:
        """Comprehensive cost analysis with fine-grained breakdown"""

        # Calculate cost components
        costs = self._calculate_costs(breakdown)

        # Identify all cost drivers
        drivers = self._identify_cost_drivers(breakdown)

        # Calculate effective multiplier
        effective_multiplier = self._calculate_effective_multiplier(breakdown)

        # Generate optimization opportunities
        opportunities = self._generate_optimization_opportunities(breakdown, costs)

        # Regional and provider analysis
        regional_analysis = self._analyze_regional_provider_costs(breakdown)

        return {
            "operation_id": breakdown.operation_id,
            "timestamp": breakdown.timestamp.isoformat(),
            "total_input_tokens": breakdown.total_input_tokens,
            "total_output_tokens": breakdown.total_output_tokens,
            "effective_token_multiplier": effective_multiplier,
            "costs": costs,
            "cost_drivers": drivers,
            "optimization_opportunities": opportunities,
            "regional_provider_analysis": regional_analysis,
            "caching_efficiency": {
                "cache_effectiveness_percent": breakdown.cache_effectiveness * 100,
                "potential_savings_percent": self._calculate_cache_savings_potential(breakdown),
                "cache_write_tokens": breakdown.cache_tokens_written,
                "cache_read_tokens": breakdown.cache_tokens_read,
            },
            "context_usage": {
                "window_size": breakdown.context_window_size,
                "used_percent": breakdown.context_window_used_percent,
                "recommendation": self._get_context_recommendation(breakdown)
            },
            "task_analysis": {
                "category": breakdown.task_category.value,
                "complexity": breakdown.complexity_level.value,
                "efficiency_factor": self.TASK_EFFICIENCY.get(breakdown.task_category, 1.0),
            },
            "recommendations": self._generate_recommendations(breakdown, costs)
        }

    def _calculate_costs(self, breakdown: DetailedTokenBreakdown) -> Dict[str, float]:
        """Calculate costs across all dimensions"""

        # Base input cost
        input_cost = breakdown.total_input_tokens * 1.0

        # Apply input source multiplier
        input_cost *= self.INPUT_SOURCE_MULTIPLIERS.get(
            breakdown.input_source_method, 1.0
        )

        # Apply complexity factor
        complexity_factor, _ = self.COMPLEXITY_FACTORS.get(
            breakdown.complexity_level, (1.0, "")
        )
        input_cost *= complexity_factor

        # Apply task efficiency
        task_efficiency = self.TASK_EFFICIENCY.get(breakdown.task_category, 1.0)
        input_cost *= task_efficiency

        # Cache adjustments
        cache_write_cost = breakdown.cache_tokens_written * 1.25  # 25% premium
        cache_read_discount = breakdown.cache_tokens_read * -0.9  # 90% discount

        # Vision token cost
        vision_cost = breakdown.vision_tokens * 3.6

        # Output cost (usually simpler than input)
        output_cost = breakdown.total_output_tokens * 0.5  # Simplified assumption

        # Streaming overhead
        if breakdown.output_streaming:
            output_cost *= 1.2

        # Structured output overhead
        if breakdown.output_structured:
            output_cost *= 1.1

        # Tool use overhead
        tool_overhead = (breakdown.tool_calls * 100) * 1.5

        # Time-of-day multiplier
        total_input_cost = input_cost * breakdown.time_multiplier
        total_output_cost = output_cost * breakdown.time_multiplier

        # Batch discount
        batch_discount = 1.0
        if breakdown.is_batched and breakdown.batch_size > 1:
            batch_discount = 1.0 - (0.05 * (breakdown.batch_size - 1))  # 5% per item

        total = (total_input_cost + total_output_cost + cache_write_cost +
                 cache_read_discount + vision_cost + tool_overhead) * batch_discount

        return {
            "input_base": breakdown.total_input_tokens,
            "input_after_source_multiplier": input_cost,
            "input_after_complexity": input_cost * complexity_factor,
            "input_after_task_efficiency": input_cost * complexity_factor * task_efficiency,
            "cache_write_cost": cache_write_cost,
            "cache_read_savings": cache_read_discount,
            "vision_cost": vision_cost,
            "output_cost": total_output_cost,
            "tool_overhead": tool_overhead,
            "time_multiplier_applied": breakdown.time_multiplier,
            "batch_discount_applied": batch_discount,
            "total_effective_tokens": total,
        }

    def _identify_cost_drivers(
        self,
        breakdown: DetailedTokenBreakdown
    ) -> List[Dict[str, Any]]:
        """Identify primary cost drivers"""

        drivers = []

        # Input source
        source_multiplier = self.INPUT_SOURCE_MULTIPLIERS.get(
            breakdown.input_source_method, 1.0
        )
        if source_multiplier > 2.0:
            drivers.append({
                "driver": "input_source",
                "type": breakdown.input_source_method.value,
                "multiplier": source_multiplier,
                "impact": "HIGH",
                "recommendation": f"Use {InputSource.PASTED_TEXT.value} (1.0x) instead"
            })

        # Vision tokens
        if breakdown.vision_tokens > 0:
            drivers.append({
                "driver": "vision_processing",
                "tokens": breakdown.vision_tokens,
                "multiplier": 3.6,
                "impact": "HIGH",
                "recommendation": "Pre-process images to reduce resolution or count"
            })

        # Complexity
        complexity_factor, description = self.COMPLEXITY_FACTORS.get(
            breakdown.complexity_level, (1.0, "")
        )
        if complexity_factor > 1.3:
            drivers.append({
                "driver": "task_complexity",
                "level": breakdown.complexity_level.value,
                "multiplier": complexity_factor,
                "impact": "MEDIUM",
                "recommendation": "Break into simpler subtasks"
            })

        # Context window usage
        if breakdown.context_window_used_percent > 0.8:
            drivers.append({
                "driver": "context_window_usage",
                "percent_used": breakdown.context_window_used_percent * 100,
                "impact": "MEDIUM",
                "recommendation": "Reduce context or split across multiple calls"
            })

        # Tool calls overhead
        if breakdown.tool_calls > 5:
            drivers.append({
                "driver": "tool_call_overhead",
                "tool_calls": breakdown.tool_calls,
                "multiplier": 1.5,
                "impact": "MEDIUM",
                "recommendation": "Batch tool calls or reduce number of tools used"
            })

        # Time-of-day multiplier
        if breakdown.time_multiplier > 1.1:
            drivers.append({
                "driver": "peak_hours",
                "time_window": breakdown.time_window.value,
                "multiplier": breakdown.time_multiplier,
                "impact": "LOW",
                "recommendation": "Schedule non-urgent tasks during off-peak hours (10 PM - 6 AM)"
            })

        # Cache effectiveness
        if breakdown.cache_effectiveness < 0.1 and breakdown.cache_tokens_written > 1000:
            drivers.append({
                "driver": "low_cache_hit_rate",
                "effectiveness": breakdown.cache_effectiveness * 100,
                "impact": "MEDIUM",
                "recommendation": "Improve prompt reuse to increase cache hits"
            })

        return drivers

    def _calculate_effective_multiplier(self, breakdown: DetailedTokenBreakdown) -> float:
        """Calculate overall effective cost multiplier"""

        multiplier = 1.0

        # Input source
        multiplier *= self.INPUT_SOURCE_MULTIPLIERS.get(
            breakdown.input_source_method, 1.0
        )

        # Complexity
        complexity_factor, _ = self.COMPLEXITY_FACTORS.get(
            breakdown.complexity_level, (1.0, "")
        )
        multiplier *= complexity_factor

        # Task efficiency
        multiplier *= self.TASK_EFFICIENCY.get(breakdown.task_category, 1.0)

        # Time multiplier
        multiplier *= breakdown.time_multiplier

        # Cache benefit (reduces effective tokens)
        if breakdown.cache_tokens_read > 0:
            total_input = breakdown.total_input_tokens
            cached_savings = breakdown.cache_tokens_read * 0.9  # 90% discount
            multiplier *= 1.0 - (cached_savings / total_input) if total_input > 0 else 1.0

        return multiplier

    def _generate_optimization_opportunities(
        self,
        breakdown: DetailedTokenBreakdown,
        costs: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate specific optimization opportunities ranked by ROI"""

        opportunities = []

        # Vision optimization
        if breakdown.vision_tokens > 5000:
            opportunities.append({
                "opportunity": "Reduce image resolution",
                "current_tokens": breakdown.vision_tokens,
                "potential_savings": breakdown.vision_tokens * 0.4,
                "effort": "LOW",
                "roi_score": 8.0,
                "steps": [
                    "Resize images to 1024x1024 or lower",
                    "Use JPEG compression instead of PNG",
                    "Process one image at a time vs batch"
                ]
            })

        # Context window optimization
        if breakdown.context_window_used_percent > 0.7:
            savings = breakdown.total_input_tokens * 0.3
            opportunities.append({
                "opportunity": "Reduce context window usage",
                "current_usage": breakdown.context_window_used_percent * 100,
                "potential_savings": savings,
                "effort": "MEDIUM",
                "roi_score": 6.0,
                "steps": [
                    "Remove unnecessary context",
                    "Use summarization for long documents",
                    "Split into multiple focused calls"
                ]
            })

        # Cache optimization
        if breakdown.cache_effectiveness < 0.2:
            potential_cache_savings = breakdown.total_input_tokens * 0.7
            opportunities.append({
                "opportunity": "Increase cache hit rate",
                "current_effectiveness": breakdown.cache_effectiveness * 100,
                "potential_savings": potential_cache_savings,
                "effort": "MEDIUM",
                "roi_score": 7.0,
                "steps": [
                    "Standardize prompt templates",
                    "Reuse system prompts",
                    "Batch similar requests"
                ]
            })

        # Complexity reduction
        if breakdown.complexity_level in [TokenComplexity.VERY_COMPLEX, TokenComplexity.COMPLEX]:
            complexity_factor, _ = self.COMPLEXITY_FACTORS.get(breakdown.complexity_level, (1.0, ""))
            savings = breakdown.total_input_tokens * (complexity_factor - 1.0)
            opportunities.append({
                "opportunity": "Reduce task complexity",
                "current_level": breakdown.complexity_level.value,
                "potential_savings": savings,
                "effort": "HIGH",
                "roi_score": 5.0,
                "steps": [
                    "Break into smaller tasks",
                    "Provide clearer instructions",
                    "Use examples for guidance"
                ]
            })

        # Sort by ROI
        opportunities.sort(key=lambda x: x["roi_score"], reverse=True)
        return opportunities

    def _analyze_regional_provider_costs(
        self,
        breakdown: DetailedTokenBreakdown
    ) -> Dict[str, Any]:
        """Analyze regional and provider cost differences"""

        # This would compare costs across different providers/regions
        # For now, show the current selection
        return {
            "current_provider": breakdown.provider,
            "current_region": breakdown.region,
            "provider_multiplier": 1.0,  # Would vary by provider
            "region_multiplier": self._get_region_multiplier(breakdown.region),
            "alternative_regions": self._get_cheaper_alternatives(breakdown.region)
        }

    def _get_region_multiplier(self, region: str) -> float:
        """Get cost multiplier for region"""
        multipliers = {
            "us-east-1": 1.0,
            "us-west-2": 1.0,
            "eu-west-1": 1.10,
            "ap-southeast-1": 1.15,
        }
        return multipliers.get(region, 1.0)

    def _get_cheaper_alternatives(self, region: str) -> List[str]:
        """Get list of cheaper regions"""
        if region in ["eu-west-1", "ap-southeast-1"]:
            return ["us-east-1", "us-west-2"]
        return []

    def _calculate_cache_savings_potential(self, breakdown: DetailedTokenBreakdown) -> float:
        """Calculate potential savings from improved caching"""
        # With perfect caching of 50% of tokens
        perfect_cache_rate = 0.5
        current_rate = breakdown.cache_effectiveness
        potential_improvement = (perfect_cache_rate - current_rate) * 100
        return max(0, potential_improvement)

    def _get_context_recommendation(self, breakdown: DetailedTokenBreakdown) -> str:
        """Get context window usage recommendation"""
        if breakdown.context_window_used_percent > 0.9:
            return "Critical: Split across multiple calls"
        elif breakdown.context_window_used_percent > 0.7:
            return "Warning: Consider reducing context"
        else:
            return "OK: Room for additional context"

    def _generate_recommendations(
        self,
        breakdown: DetailedTokenBreakdown,
        costs: Dict[str, float]
    ) -> List[str]:
        """Generate prioritized recommendations"""

        recommendations = []

        # High impact recommendations
        if breakdown.input_source_method in [
            InputSource.BROWSER_SCRAPE,
            InputSource.MCP_SKILL,
            InputSource.GITHUB_API
        ]:
            recommendations.append(
                f"Primary cost driver: {breakdown.input_source_method.value} "
                f"({self.INPUT_SOURCE_MULTIPLIERS.get(breakdown.input_source_method)}x). "
                f"Consider alternatives."
            )

        if breakdown.context_window_used_percent > 0.8:
            recommendations.append(
                f"Context usage critical ({breakdown.context_window_used_percent*100:.0f}%). "
                f"Split request or summarize input."
            )

        if breakdown.cache_effectiveness < 0.1 and breakdown.total_input_tokens > 5000:
            recommendations.append(
                "Low cache effectiveness. Standardize prompts to increase cache hits (90% discount)."
            )

        if breakdown.time_multiplier > 1.2:
            recommendations.append(
                f"Peak hour premium ({breakdown.time_multiplier}x). "
                f"Schedule for {TimeWindow.OFF_PEAK.value} (10 PM - 6 AM) for 30% savings."
            )

        return recommendations
