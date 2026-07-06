"""
Token consumption classification and tracking.
Properly categorizes tokens by type, usage pattern, and cost driver.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    """Classification of token consumption"""
    INPUT_STANDARD = "input_standard"  # Regular input tokens
    INPUT_CACHED_WRITE = "input_cached_write"  # Tokens written to cache (25% premium)
    INPUT_CACHED_READ = "input_cached_read"  # Cached tokens retrieved (90% discount)
    OUTPUT_STANDARD = "output_standard"  # Regular output tokens
    VISION_TOKENS = "vision_tokens"  # Vision/image processing (3.6x base rate)
    TOOL_USE_TOKENS = "tool_use_tokens"  # Tool calling overhead


class OperationType(Enum):
    """High-level operation classification"""
    API_CALL = "api_call"  # Direct API calls
    FILE_READ = "file_read"  # File operations (CSV, PDF, etc.)
    BROWSER_OPERATION = "browser_operation"  # Browser scraping (55x more expensive)
    MCP_INVOCATION = "mcp_invocation"  # MCP skill calls (10-100x overhead)
    GITHUB_OPERATION = "github_operation"  # GitHub operations (4-12x base)
    DATABASE_QUERY = "database_query"  # Data warehouse queries (100-1000x+)
    IMAGE_PROCESSING = "image_processing"  # Vision/image tasks
    CODE_EXECUTION = "code_execution"  # Code execution tool
    MARKDOWN_OPERATION = "markdown_operation"  # Documentation updates (3x base)


@dataclass
class TokenConsumption:
    """Single token consumption event"""
    timestamp: datetime
    operation_type: OperationType
    token_type: TokenType
    count: int
    model: str
    region: str
    provider: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    cost_usd: float = 0.0
    is_cached: bool = False
    cache_hit_rate: float = 0.0  # For cached reads
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TokenClassifier:
    """Classify and track token consumption patterns"""

    # Token multipliers by operation type
    OPERATION_MULTIPLIERS = {
        OperationType.API_CALL: 1.0,
        OperationType.FILE_READ: 1.2,  # Varies by file format
        OperationType.BROWSER_OPERATION: 55.0,  # Extremely expensive
        OperationType.MCP_INVOCATION: 25.0,  # Average 10-100x range
        OperationType.GITHUB_OPERATION: 8.0,  # 4-12x average 8x
        OperationType.DATABASE_QUERY: 500.0,  # Average 100-1000x+
        OperationType.IMAGE_PROCESSING: 3.6,  # Vision token premium
        OperationType.CODE_EXECUTION: 2.0,  # Slight overhead
        OperationType.MARKDOWN_OPERATION: 3.0
    }

    # File format multipliers (when reading files)
    FILE_FORMAT_MULTIPLIERS = {
        "csv_pasted": 1.0,
        "json_pasted": 1.0,
        "text_pasted": 1.0,
        "pdf_local": 1.2,  # Slightly more tokens
        "pdf_url": 3.6,  # 3.6x more expensive
        "image_local": 1.0,
        "image_url": 4.2,  # Image URLs are expensive
        "html_pasted": 1.5,
        "html_url": 2.8
    }

    def __init__(self):
        self.consumption_history: List[TokenConsumption] = []

    def classify_consumption(
        self,
        operation_type: OperationType,
        token_count: int,
        model: str,
        region: str = "us-east-1",
        provider: str = "anthropic",
        is_cached: bool = False,
        cache_hit_rate: float = 0.0,
        file_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify token consumption and calculate cost multipliers"""

        # Get base multiplier for operation type
        base_multiplier = self.OPERATION_MULTIPLIERS.get(operation_type, 1.0)

        # Apply file format multiplier if applicable
        if file_format and operation_type == OperationType.FILE_READ:
            file_multiplier = self.FILE_FORMAT_MULTIPLIERS.get(file_format, 1.0)
            base_multiplier *= file_multiplier

        # Classify token types
        token_breakdown = self._classify_token_types(
            token_count, is_cached, cache_hit_rate, operation_type
        )

        # Calculate effective cost multiplier
        effective_multiplier = self._calculate_effective_multiplier(
            token_breakdown, is_cached, cache_hit_rate
        )

        return {
            "operation_type": operation_type.value,
            "base_multiplier": base_multiplier,
            "token_breakdown": token_breakdown,
            "effective_multiplier": effective_multiplier,
            "total_effective_tokens": token_count * effective_multiplier,
            "is_cached": is_cached,
            "cache_hit_rate": cache_hit_rate if is_cached else 0,
            "cost_drivers": self._identify_cost_drivers(operation_type, file_format, is_cached)
        }

    def _classify_token_types(
        self,
        total_tokens: int,
        is_cached: bool,
        cache_hit_rate: float,
        operation_type: OperationType
    ) -> Dict[str, int]:
        """Break down tokens by type"""

        breakdown = {
            TokenType.INPUT_STANDARD.value: 0,
            TokenType.INPUT_CACHED_WRITE.value: 0,
            TokenType.INPUT_CACHED_READ.value: 0,
            TokenType.OUTPUT_STANDARD.value: 0,
            TokenType.VISION_TOKENS.value: 0,
            TokenType.TOOL_USE_TOKENS.value: 0
        }

        if operation_type == OperationType.IMAGE_PROCESSING:
            breakdown[TokenType.VISION_TOKENS.value] = total_tokens
        elif is_cached:
            # Cached operations: split between write and read
            write_portion = total_tokens * (1 - cache_hit_rate)
            read_portion = total_tokens * cache_hit_rate

            breakdown[TokenType.INPUT_CACHED_WRITE.value] = int(write_portion)
            breakdown[TokenType.INPUT_CACHED_READ.value] = int(read_portion)
        else:
            # Estimate input vs output (typically 70% input, 30% output)
            breakdown[TokenType.INPUT_STANDARD.value] = int(total_tokens * 0.7)
            breakdown[TokenType.OUTPUT_STANDARD.value] = int(total_tokens * 0.3)

        if operation_type == OperationType.CODE_EXECUTION:
            breakdown[TokenType.TOOL_USE_TOKENS.value] = int(total_tokens * 0.1)

        return breakdown

    def _calculate_effective_multiplier(
        self,
        token_breakdown: Dict[str, int],
        is_cached: bool,
        cache_hit_rate: float
    ) -> float:
        """Calculate effective cost multiplier accounting for cache"""

        total_tokens = sum(token_breakdown.values())
        if total_tokens == 0:
            return 1.0

        # Base multiplier = 1.0
        effective_cost = 0.0

        # Standard tokens cost 1.0x
        standard_cost = token_breakdown.get(TokenType.INPUT_STANDARD.value, 0) * 1.0
        output_cost = token_breakdown.get(TokenType.OUTPUT_STANDARD.value, 0) * 1.0

        # Cached writes cost 1.25x (25% premium)
        cached_write_cost = token_breakdown.get(TokenType.INPUT_CACHED_WRITE.value, 0) * 1.25

        # Cached reads cost 0.1x (90% discount)
        cached_read_cost = token_breakdown.get(TokenType.INPUT_CACHED_READ.value, 0) * 0.1

        # Vision tokens cost 3.6x
        vision_cost = token_breakdown.get(TokenType.VISION_TOKENS.value, 0) * 3.6

        # Tool use adds 20% overhead
        tool_cost = token_breakdown.get(TokenType.TOOL_USE_TOKENS.value, 0) * 1.2

        effective_cost = (
            standard_cost + output_cost + cached_write_cost +
            cached_read_cost + vision_cost + tool_cost
        )

        return effective_cost / total_tokens if total_tokens > 0 else 1.0

    def _identify_cost_drivers(
        self,
        operation_type: OperationType,
        file_format: Optional[str],
        is_cached: bool
    ) -> List[Dict[str, Any]]:
        """Identify what's driving costs for this operation"""

        drivers = []

        # Operation type cost driver
        multiplier = self.OPERATION_MULTIPLIERS.get(operation_type, 1.0)
        if multiplier > 2.0:
            drivers.append({
                "driver": "operation_type",
                "reason": operation_type.value,
                "cost_multiplier": multiplier,
                "optimization": self._get_optimization_for_operation(operation_type)
            })

        # File format cost driver
        if file_format and operation_type == OperationType.FILE_READ:
            file_mult = self.FILE_FORMAT_MULTIPLIERS.get(file_format, 1.0)
            if file_mult > 1.5:
                drivers.append({
                    "driver": "file_format",
                    "reason": f"Using {file_format}",
                    "cost_multiplier": file_mult,
                    "optimization": f"Consider switching to cheaper format (csv/text ~1.0x vs {file_format} {file_mult}x)"
                })

        # Cache opportunity
        if not is_cached and operation_type in [
            OperationType.API_CALL,
            OperationType.MARKDOWN_OPERATION,
            OperationType.CODE_EXECUTION
        ]:
            drivers.append({
                "driver": "caching_opportunity",
                "reason": "Operation could benefit from prompt caching",
                "cost_multiplier": 0.1,  # Potential reduction to 10% with caching
                "optimization": "Enable prompt caching for 90% token savings"
            })

        return drivers

    def _get_optimization_for_operation(self, operation_type: OperationType) -> str:
        """Get optimization recommendation for operation type"""

        optimizations = {
            OperationType.BROWSER_OPERATION: "Batch browser operations or switch to API when possible",
            OperationType.MCP_INVOCATION: "Batch MCP calls or cache results",
            OperationType.DATABASE_QUERY: "Filter data at source before querying",
            OperationType.GITHUB_OPERATION: "Batch GitHub operations",
            OperationType.FILE_READ: "Use local storage instead of URLs"
        }

        return optimizations.get(operation_type, "Optimize operation specifics")

    def track_consumption(
        self,
        operation_type: OperationType,
        token_count: int,
        model: str,
        user_id: str,
        **kwargs
    ) -> TokenConsumption:
        """Track token consumption for future analysis"""

        consumption = TokenConsumption(
            timestamp=datetime.utcnow(),
            operation_type=operation_type,
            token_type=TokenType.INPUT_STANDARD,
            count=token_count,
            model=model,
            user_id=user_id,
            region=kwargs.get("region", "us-east-1"),
            provider=kwargs.get("provider", "anthropic"),
            session_id=kwargs.get("session_id"),
            metadata=kwargs.get("metadata", {})
        )

        self.consumption_history.append(consumption)
        return consumption

    def get_consumption_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Summarize token consumption by operation type"""

        cutoff = datetime.utcnow() - timedelta(days=days)
        relevant = [c for c in self.consumption_history
                   if c.user_id == user_id and c.timestamp >= cutoff]

        if not relevant:
            return {"error": "No consumption data"}

        # Group by operation type
        by_operation = {}
        total_tokens = 0

        for consumption in relevant:
            op_type = consumption.operation_type.value
            if op_type not in by_operation:
                by_operation[op_type] = {
                    "tokens": 0,
                    "count": 0,
                    "cost_multiplier": self.OPERATION_MULTIPLIERS.get(consumption.operation_type, 1.0)
                }

            by_operation[op_type]["tokens"] += consumption.count
            by_operation[op_type]["count"] += 1
            total_tokens += consumption.count

        # Calculate percentages
        for op_type in by_operation:
            by_operation[op_type]["percent_of_total"] = (
                by_operation[op_type]["tokens"] / total_tokens * 100
                if total_tokens > 0 else 0
            )

        return {
            "period_days": days,
            "total_tokens": total_tokens,
            "by_operation_type": by_operation,
            "operations_count": len(relevant)
        }


from datetime import timedelta
