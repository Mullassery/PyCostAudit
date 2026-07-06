"""
Advanced filtering system for cost data with composable filters and aggregations.
Enables complex queries without SQL knowledge.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class FilterOperator(Enum):
    """Filter comparison operators"""
    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    CONTAINS = "contains"  # String contains
    NOT_CONTAINS = "not_contains"  # String does not contain
    BETWEEN = "between"  # Between two values
    REGEX = "regex"  # Regex match


class AggregationFunction(Enum):
    """Aggregation functions for report generation"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    STDDEV = "stddev"
    PERCENTILE_50 = "p50"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"


class TimeBucket(Enum):
    """Time bucketing for time-series aggregation"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class FilterCondition:
    """Single filter condition"""
    field: str
    operator: FilterOperator
    value: Any
    description: str = ""

    def evaluate(self, obj: Dict[str, Any]) -> bool:
        """Evaluate condition against object"""
        if self.field in obj:
            field = obj.get(self.field)
            if self.operator == FilterOperator.EQ:
                return field == self.value
            elif self.operator == FilterOperator.NE:
                return field != self.value
            elif self.operator == FilterOperator.GT:
                return field > self.value
            elif self.operator == FilterOperator.GTE:
                return field >= self.value
            elif self.operator == FilterOperator.LT:
                return field < self.value
            elif self.operator == FilterOperator.LTE:
                return field <= self.value
            elif self.operator == FilterOperator.IN:
                return field in self.value
            elif self.operator == FilterOperator.NOT_IN:
                return field not in self.value
            elif self.operator == FilterOperator.CONTAINS:
                return str(self.value).lower() in str(field).lower()
            elif self.operator == FilterOperator.NOT_CONTAINS:
                return str(self.value).lower() not in str(field).lower()
            elif self.operator == FilterOperator.BETWEEN:
                return self.value[0] <= field <= self.value[1]
            elif self.operator == FilterOperator.REGEX:
                import re
                return bool(re.search(self.value, str(field)))
        return False


@dataclass
class FilterGroup:
    """Group of conditions with AND/OR logic"""
    conditions: List[FilterCondition]
    logic: str = "AND"  # "AND" or "OR"

    def evaluate(self, obj: Dict[str, Any]) -> bool:
        """Evaluate all conditions"""
        if not self.conditions:
            return True

        results = [cond.evaluate(obj) for cond in self.conditions]

        if self.logic.upper() == "AND":
            return all(results)
        else:  # OR
            return any(results)


class AdvancedFilter:
    """Advanced composable filter system"""

    def __init__(self):
        self.filter_groups: List[FilterGroup] = []
        self.exclude_groups: List[FilterGroup] = []
        self.sort_field: Optional[str] = None
        self.sort_order: str = "ASC"
        self.limit: Optional[int] = None
        self.offset: int = 0

    def add_filter_group(self, group: FilterGroup) -> "AdvancedFilter":
        """Add filter group (AND applied between groups)"""
        self.filter_groups.append(group)
        return self

    def add_exclude_group(self, group: FilterGroup) -> "AdvancedFilter":
        """Add exclusion filter group"""
        self.exclude_groups.append(group)
        return self

    def add_condition(self, field: str, operator: FilterOperator, value: Any) -> "AdvancedFilter":
        """Add single condition to current group"""
        if not self.filter_groups:
            self.filter_groups.append(FilterGroup(conditions=[]))

        self.filter_groups[-1].conditions.append(
            FilterCondition(field, operator, value)
        )
        return self

    def sort_by(self, field: str, order: str = "ASC") -> "AdvancedFilter":
        """Set sort field and order"""
        self.sort_field = field
        self.sort_order = order.upper()
        return self

    def limit_results(self, limit: int, offset: int = 0) -> "AdvancedFilter":
        """Limit and offset results"""
        self.limit = limit
        self.offset = offset
        return self

    def apply(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply all filters to data"""
        # Apply include filters (AND between groups)
        result = data
        for group in self.filter_groups:
            result = [item for item in result if group.evaluate(item)]

        # Apply exclude filters
        for group in self.exclude_groups:
            result = [item for item in result if not group.evaluate(item)]

        # Sort
        if self.sort_field:
            reverse = self.sort_order == "DESC"
            result.sort(
                key=lambda x: x.get(self.sort_field, ""),
                reverse=reverse
            )

        # Limit and offset
        if self.offset:
            result = result[self.offset:]
        if self.limit:
            result = result[:self.limit]

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Serialize filter to dict"""
        return {
            "filter_groups": [
                {
                    "conditions": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value
                        }
                        for c in group.conditions
                    ],
                    "logic": group.logic
                }
                for group in self.filter_groups
            ],
            "exclude_groups": [
                {
                    "conditions": [
                        {
                            "field": c.field,
                            "operator": c.operator.value,
                            "value": c.value
                        }
                        for c in group.conditions
                    ],
                    "logic": group.logic
                }
                for group in self.exclude_groups
            ],
            "sort_field": self.sort_field,
            "sort_order": self.sort_order,
            "limit": self.limit,
            "offset": self.offset
        }


class Aggregator:
    """Data aggregation engine"""

    def __init__(self):
        self.group_by_fields: List[str] = []
        self.aggregations: Dict[str, tuple] = {}  # field -> (function, source_field)
        self.time_bucket: Optional[TimeBucket] = None
        self.time_field: str = "timestamp"

    def group_by(self, *fields: str) -> "Aggregator":
        """Group by fields"""
        self.group_by_fields.extend(fields)
        return self

    def add_aggregation(
        self,
        output_field: str,
        function: AggregationFunction,
        source_field: str
    ) -> "Aggregator":
        """Add aggregation"""
        self.aggregations[output_field] = (function, source_field)
        return self

    def time_bucket_by(self, bucket: TimeBucket, time_field: str = "timestamp") -> "Aggregator":
        """Set time bucketing"""
        self.time_bucket = bucket
        self.time_field = time_field
        return self

    def aggregate(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply aggregations"""
        if not data:
            return []

        # If time bucketing, create time buckets
        if self.time_bucket:
            data = self._apply_time_bucketing(data)

        # Group data
        groups: Dict[tuple, List[Dict[str, Any]]] = {}

        for item in data:
            key_parts = []
            for field in self.group_by_fields:
                key_parts.append(item.get(field))

            key = tuple(key_parts)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        # Aggregate each group
        result = []
        for key, group_items in groups.items():
            row = {}

            # Add group by fields
            for i, field in enumerate(self.group_by_fields):
                row[field] = key[i]

            # Apply aggregations
            for output_field, (function, source_field) in self.aggregations.items():
                values = [item.get(source_field, 0) for item in group_items if source_field in item]

                if not values:
                    row[output_field] = 0
                elif function == AggregationFunction.SUM:
                    row[output_field] = sum(values)
                elif function == AggregationFunction.AVG:
                    row[output_field] = sum(values) / len(values)
                elif function == AggregationFunction.MIN:
                    row[output_field] = min(values)
                elif function == AggregationFunction.MAX:
                    row[output_field] = max(values)
                elif function == AggregationFunction.COUNT:
                    row[output_field] = len(values)
                elif function == AggregationFunction.STDDEV:
                    import statistics
                    row[output_field] = statistics.stdev(values) if len(values) > 1 else 0
                elif function == AggregationFunction.PERCENTILE_50:
                    row[output_field] = sorted(values)[len(values) // 2]
                elif function == AggregationFunction.PERCENTILE_95:
                    idx = int(len(values) * 0.95)
                    row[output_field] = sorted(values)[idx]
                elif function == AggregationFunction.PERCENTILE_99:
                    idx = int(len(values) * 0.99)
                    row[output_field] = sorted(values)[idx]

            result.append(row)

        return result

    def _apply_time_bucketing(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply time bucketing to data"""
        if not self.time_bucket:
            return data

        bucketed = {}

        for item in data:
            timestamp = item.get(self.time_field)
            if not isinstance(timestamp, datetime):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    continue

            bucket_key = self._get_bucket_key(timestamp)
            if bucket_key not in bucketed:
                bucketed[bucket_key] = item.copy()
            else:
                # Merge numeric fields
                for key, value in item.items():
                    if isinstance(value, (int, float)) and key in bucketed[bucket_key]:
                        bucketed[bucket_key][key] += value

        return list(bucketed.values())

    def _get_bucket_key(self, dt: datetime) -> str:
        """Get bucket key for datetime"""
        if self.time_bucket == TimeBucket.MINUTE:
            return dt.strftime("%Y-%m-%d %H:%M")
        elif self.time_bucket == TimeBucket.HOUR:
            return dt.strftime("%Y-%m-%d %H:00")
        elif self.time_bucket == TimeBucket.DAY:
            return dt.strftime("%Y-%m-%d")
        elif self.time_bucket == TimeBucket.WEEK:
            week_start = dt - timedelta(days=dt.weekday())
            return week_start.strftime("%Y-W%V")
        elif self.time_bucket == TimeBucket.MONTH:
            return dt.strftime("%Y-%m")
        elif self.time_bucket == TimeBucket.QUARTER:
            quarter = (dt.month - 1) // 3 + 1
            return f"{dt.year}-Q{quarter}"
        elif self.time_bucket == TimeBucket.YEAR:
            return dt.strftime("%Y")
        else:
            return dt.strftime("%Y-%m-%d")


class PresetFilter:
    """Pre-built common filters"""

    @staticmethod
    def last_n_days(n: int) -> AdvancedFilter:
        """Filter for last N days"""
        cutoff = datetime.utcnow() - timedelta(days=n)
        f = AdvancedFilter()
        return f.add_condition(
            "timestamp",
            FilterOperator.GTE,
            cutoff
        )

    @staticmethod
    def date_range(start: datetime, end: datetime) -> AdvancedFilter:
        """Filter for date range"""
        f = AdvancedFilter()
        return f.add_condition(
            "timestamp",
            FilterOperator.BETWEEN,
            [start, end]
        )

    @staticmethod
    def high_cost(threshold: float) -> AdvancedFilter:
        """Filter for costs above threshold"""
        f = AdvancedFilter()
        return f.add_condition(
            "total_cost",
            FilterOperator.GT,
            threshold
        )

    @staticmethod
    def operation_types(*types: str) -> AdvancedFilter:
        """Filter by operation types"""
        f = AdvancedFilter()
        return f.add_condition(
            "operation_type",
            FilterOperator.IN,
            list(types)
        )

    @staticmethod
    def providers(*providers: str) -> AdvancedFilter:
        """Filter by providers"""
        f = AdvancedFilter()
        return f.add_condition(
            "provider",
            FilterOperator.IN,
            list(providers)
        )

    @staticmethod
    def regions(*regions: str) -> AdvancedFilter:
        """Filter by regions"""
        f = AdvancedFilter()
        return f.add_condition(
            "region",
            FilterOperator.IN,
            list(regions)
        )

    @staticmethod
    def users(*user_ids: str) -> AdvancedFilter:
        """Filter by users"""
        f = AdvancedFilter()
        return f.add_condition(
            "user_id",
            FilterOperator.IN,
            list(user_ids)
        )

    @staticmethod
    def anomalies_only() -> AdvancedFilter:
        """Filter for anomalies only"""
        f = AdvancedFilter()
        return f.add_condition(
            "is_anomaly",
            FilterOperator.EQ,
            True
        )

    @staticmethod
    def peak_hours_only() -> AdvancedFilter:
        """Filter for peak hours only (5 PM - 10 PM)"""
        f = AdvancedFilter()
        return f.add_condition(
            "hour",
            FilterOperator.IN,
            [17, 18, 19, 20, 21]
        )
