"""
Custom report builder with flexible report generation, scheduling, and export formats.
Enables users to create tailored cost analysis reports without code.
"""

import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .advanced_filters import AdvancedFilter, Aggregator, AggregationFunction, TimeBucket, PresetFilter


class ExportFormat(Enum):
    """Report export formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    EXCEL = "excel"


class ReportSchedule(Enum):
    """Report scheduling frequency"""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class ReportType(Enum):
    """Types of reports"""
    COST_BREAKDOWN = "cost_breakdown"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE = "comparative"
    ANOMALY = "anomaly"
    OPTIMIZATION = "optimization"
    BUDGET_STATUS = "budget_status"
    CUSTOM = "custom"


@dataclass
class ReportSection:
    """Section of a report"""
    title: str
    description: str
    data: Dict[str, Any] = field(default_factory=dict)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)


@dataclass
class ReportMetadata:
    """Report metadata"""
    report_id: str
    name: str
    description: str
    report_type: ReportType
    created_at: datetime
    generated_at: datetime
    created_by: str
    organization: str = "default"
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


class CustomReport:
    """Custom report builder"""

    def __init__(
        self,
        name: str,
        report_type: ReportType = ReportType.CUSTOM,
        description: str = ""
    ):
        self.name = name
        self.report_type = report_type
        self.description = description
        self.filters: Optional[AdvancedFilter] = None
        self.aggregator: Optional[Aggregator] = None
        self.sections: List[ReportSection] = []
        self.metadata_fields: List[str] = []
        self.export_formats: List[ExportFormat] = [ExportFormat.JSON, ExportFormat.CSV]
        self.created_at = datetime.utcnow()

    def with_filter(self, adv_filter: AdvancedFilter) -> "CustomReport":
        """Add filter to report"""
        self.filters = adv_filter
        return self

    def with_preset_filter(self, preset: Callable[..., AdvancedFilter], *args, **kwargs) -> "CustomReport":
        """Add preset filter"""
        self.filters = preset(*args, **kwargs)
        return self

    def with_aggregation(self, aggregator: Aggregator) -> "CustomReport":
        """Add aggregation to report"""
        self.aggregator = aggregator
        return self

    def add_section(self, section: ReportSection) -> "CustomReport":
        """Add report section"""
        self.sections.append(section)
        return self

    def with_export_formats(self, *formats: ExportFormat) -> "CustomReport":
        """Set export formats"""
        self.export_formats = list(formats)
        return self

    def with_metadata(self, *fields: str) -> "CustomReport":
        """Add metadata fields to include"""
        self.metadata_fields.extend(fields)
        return self

    def generate(self, data: List[Dict[str, Any]]) -> "GeneratedReport":
        """Generate report from data"""
        # Apply filters
        filtered_data = data
        if self.filters:
            filtered_data = self.filters.apply(data)

        # Apply aggregations
        aggregated_data = filtered_data
        if self.aggregator:
            aggregated_data = self.aggregator.aggregate(filtered_data)

        # Create metadata
        metadata = ReportMetadata(
            report_id=f"report_{datetime.utcnow().timestamp()}",
            name=self.name,
            description=self.description,
            report_type=self.report_type,
            created_at=self.created_at,
            generated_at=datetime.utcnow(),
            created_by="system"
        )

        return GeneratedReport(
            metadata=metadata,
            raw_data=filtered_data,
            aggregated_data=aggregated_data,
            sections=self.sections,
            export_formats=self.export_formats
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize report definition"""
        return {
            "name": self.name,
            "description": self.description,
            "report_type": self.report_type.value,
            "filters": self.filters.to_dict() if self.filters else None,
            "sections_count": len(self.sections),
            "export_formats": [fmt.value for fmt in self.export_formats],
            "metadata_fields": self.metadata_fields,
            "created_at": self.created_at.isoformat()
        }


class GeneratedReport:
    """Generated report instance"""

    def __init__(
        self,
        metadata: ReportMetadata,
        raw_data: List[Dict[str, Any]],
        aggregated_data: List[Dict[str, Any]],
        sections: List[ReportSection],
        export_formats: List[ExportFormat]
    ):
        self.metadata = metadata
        self.raw_data = raw_data
        self.aggregated_data = aggregated_data
        self.sections = sections
        self.export_formats = export_formats

    def get_summary(self) -> Dict[str, Any]:
        """Get report summary"""
        total_cost = sum(item.get("total_cost", 0) for item in self.raw_data)
        avg_cost = total_cost / len(self.raw_data) if self.raw_data else 0

        return {
            "report_id": self.metadata.report_id,
            "name": self.metadata.name,
            "generated_at": self.metadata.generated_at.isoformat(),
            "record_count": len(self.raw_data),
            "total_cost": total_cost,
            "average_cost": avg_cost,
            "min_cost": min((item.get("total_cost", 0) for item in self.raw_data), default=0),
            "max_cost": max((item.get("total_cost", 0) for item in self.raw_data), default=0),
            "sections_count": len(self.sections)
        }

    def export_json(self) -> str:
        """Export as JSON"""
        output = {
            "metadata": {
                "report_id": self.metadata.report_id,
                "name": self.metadata.name,
                "description": self.metadata.description,
                "report_type": self.metadata.report_type.value,
                "generated_at": self.metadata.generated_at.isoformat(),
                "created_by": self.metadata.created_by
            },
            "summary": self.get_summary(),
            "data": self.aggregated_data if self.aggregated_data else self.raw_data,
            "sections": [
                {
                    "title": s.title,
                    "description": s.description,
                    "data": s.data,
                    "insights": s.insights
                }
                for s in self.sections
            ]
        }
        return json.dumps(output, indent=2, default=str)

    def export_csv(self) -> str:
        """Export as CSV"""
        if not self.aggregated_data and not self.raw_data:
            return ""

        data = self.aggregated_data if self.aggregated_data else self.raw_data
        if not data:
            return ""

        output = []
        writer = None
        fieldnames = set()

        # Collect all fieldnames
        for row in data:
            fieldnames.update(row.keys())

        fieldnames = sorted(list(fieldnames))

        # Write header
        output.append(",".join(fieldnames))

        # Write rows
        for row in data:
            values = [str(row.get(field, "")) for field in fieldnames]
            output.append(",".join(values))

        return "\n".join(output)

    def export_html(self) -> str:
        """Export as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.metadata.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f0f0f0; }}
        .summary {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .insight {{ background-color: #e8f4f8; padding: 10px; margin: 10px 0; border-left: 4px solid #0099cc; }}
        .section {{ margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>{self.metadata.name}</h1>
    <p>{self.metadata.description}</p>

    <div class="summary">
        <h2>Summary</h2>
        <p>Generated: {self.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Total Records: {len(self.raw_data)}</p>
        <p>Total Cost: ${sum(item.get("total_cost", 0) for item in self.raw_data):.2f}</p>
    </div>
"""

        # Add sections
        for section in self.sections:
            html += f"""
    <div class="section">
        <h2>{section.title}</h2>
        <p>{section.description}</p>
"""
            if section.insights:
                html += "<div class='insights'>"
                for insight in section.insights:
                    html += f"<div class='insight'>{insight}</div>"
                html += "</div>"

            html += "    </div>"

        # Add data table
        data = self.aggregated_data if self.aggregated_data else self.raw_data
        if data:
            fieldnames = sorted(list(set().union(*(d.keys() for d in data))))
            html += """
    <div class="section">
        <h2>Detailed Data</h2>
        <table>
            <tr>
"""
            for field in fieldnames:
                html += f"                <th>{field}</th>\n"

            html += "            </tr>\n"

            for row in data:
                html += "            <tr>\n"
                for field in fieldnames:
                    html += f"                <td>{row.get(field, '')}</td>\n"
                html += "            </tr>\n"

            html += """        </table>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def export_markdown(self) -> str:
        """Export as Markdown"""
        md = f"""# {self.metadata.name}

{self.metadata.description}

## Summary

- Generated: {self.metadata.generated_at.strftime("%Y-%m-%d %H:%M:%S")}
- Total Records: {len(self.raw_data)}
- Total Cost: ${sum(item.get("total_cost", 0) for item in self.raw_data):.2f}

"""

        # Add sections
        for section in self.sections:
            md += f"""## {section.title}

{section.description}

"""
            if section.insights:
                md += "### Key Insights\n\n"
                for insight in section.insights:
                    md += f"- {insight}\n"
                md += "\n"

        # Add data table
        data = self.aggregated_data if self.aggregated_data else self.raw_data
        if data and len(data) <= 100:  # Only show table for smaller datasets
            fieldnames = sorted(list(set().union(*(d.keys() for d in data))))
            md += "## Data\n\n"
            md += "| " + " | ".join(fieldnames) + " |\n"
            md += "| " + " | ".join(["-"] * len(fieldnames)) + " |\n"

            for row in data:
                values = [str(row.get(field, "")) for field in fieldnames]
                md += "| " + " | ".join(values) + " |\n"

        return md

    def export(self, format: ExportFormat) -> str:
        """Export report in specified format"""
        if format == ExportFormat.JSON:
            return self.export_json()
        elif format == ExportFormat.CSV:
            return self.export_csv()
        elif format == ExportFormat.HTML:
            return self.export_html()
        elif format == ExportFormat.MARKDOWN:
            return self.export_markdown()
        else:
            raise ValueError(f"Unsupported export format: {format}")


class ReportTemplate:
    """Pre-built report templates"""

    @staticmethod
    def cost_breakdown_by_operation() -> CustomReport:
        """Cost breakdown by operation type"""
        report = CustomReport(
            "Cost Breakdown by Operation Type",
            ReportType.COST_BREAKDOWN,
            "Shows cost distribution across different operation types"
        )

        agg = Aggregator()
        agg.group_by("operation_type")
        agg.add_aggregation("total_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("operation_count", AggregationFunction.COUNT, "operation_type")
        agg.add_aggregation("avg_cost_per_op", AggregationFunction.AVG, "total_cost")

        report.with_aggregation(agg)

        section = ReportSection(
            title="Operation Type Breakdown",
            description="Cost and operation count by type"
        )
        report.add_section(section)

        return report

    @staticmethod
    def cost_breakdown_by_provider() -> CustomReport:
        """Cost breakdown by provider"""
        report = CustomReport(
            "Cost Breakdown by Provider",
            ReportType.COST_BREAKDOWN,
            "Shows cost distribution across cloud providers"
        )

        agg = Aggregator()
        agg.group_by("provider")
        agg.add_aggregation("total_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("operation_count", AggregationFunction.COUNT, "provider")

        report.with_aggregation(agg)
        return report

    @staticmethod
    def daily_trend(days: int = 30) -> CustomReport:
        """Daily cost trend report"""
        report = CustomReport(
            f"Daily Cost Trend ({days} days)",
            ReportType.TREND_ANALYSIS,
            f"Cost trends over the last {days} days"
        )

        report.with_preset_filter(PresetFilter.last_n_days, days)

        agg = Aggregator()
        agg.time_bucket_by(TimeBucket.DAY, "timestamp")
        agg.group_by("date")
        agg.add_aggregation("daily_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("operation_count", AggregationFunction.COUNT, "timestamp")

        report.with_aggregation(agg)
        return report

    @staticmethod
    def anomaly_report() -> CustomReport:
        """Anomaly detection report"""
        report = CustomReport(
            "Cost Anomalies",
            ReportType.ANOMALY,
            "Unusual cost spikes and patterns detected"
        )

        report.with_preset_filter(PresetFilter.anomalies_only)

        agg = Aggregator()
        agg.group_by("operation_type", "provider")
        agg.add_aggregation("anomaly_count", AggregationFunction.COUNT, "timestamp")
        agg.add_aggregation("avg_anomaly_cost", AggregationFunction.AVG, "total_cost")

        report.with_aggregation(agg)
        return report

    @staticmethod
    def regional_cost_comparison() -> CustomReport:
        """Regional cost comparison"""
        report = CustomReport(
            "Regional Cost Comparison",
            ReportType.COMPARATIVE,
            "Cost differences across regions"
        )

        agg = Aggregator()
        agg.group_by("region", "provider")
        agg.add_aggregation("total_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("avg_regional_multiplier", AggregationFunction.AVG, "regional_multiplier")

        report.with_aggregation(agg)
        return report

    @staticmethod
    def hourly_pattern() -> CustomReport:
        """Hourly cost pattern analysis"""
        report = CustomReport(
            "Hourly Cost Patterns",
            ReportType.TREND_ANALYSIS,
            "Identifies peak and off-peak hours"
        )

        agg = Aggregator()
        agg.group_by("hour")
        agg.add_aggregation("hourly_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("operation_count", AggregationFunction.COUNT, "timestamp")

        report.with_aggregation(agg)
        return report

    @staticmethod
    def top_operations(limit: int = 10) -> CustomReport:
        """Top most expensive operations"""
        report = CustomReport(
            f"Top {limit} Most Expensive Operations",
            ReportType.CUSTOM,
            "Identifies the costliest operations"
        )

        # Will be sorted in post-processing
        return report


class ReportScheduler:
    """Schedule and manage report generation"""

    def __init__(self):
        self.scheduled_reports: Dict[str, Dict[str, Any]] = {}

    def schedule_report(
        self,
        report_def: CustomReport,
        schedule: ReportSchedule,
        recipients: List[str],
        export_format: ExportFormat = ExportFormat.HTML
    ) -> str:
        """Schedule report for delivery"""
        report_id = f"scheduled_{datetime.utcnow().timestamp()}"

        self.scheduled_reports[report_id] = {
            "report_def": report_def,
            "schedule": schedule,
            "recipients": recipients,
            "export_format": export_format,
            "created_at": datetime.utcnow(),
            "last_run": None,
            "next_run": self._calculate_next_run(schedule)
        }

        return report_id

    def _calculate_next_run(self, schedule: ReportSchedule) -> datetime:
        """Calculate next run time"""
        now = datetime.utcnow()

        if schedule == ReportSchedule.DAILY:
            return now + timedelta(days=1)
        elif schedule == ReportSchedule.WEEKLY:
            return now + timedelta(weeks=1)
        elif schedule == ReportSchedule.BIWEEKLY:
            return now + timedelta(weeks=2)
        elif schedule == ReportSchedule.MONTHLY:
            return now + timedelta(days=30)
        elif schedule == ReportSchedule.QUARTERLY:
            return now + timedelta(days=90)
        else:
            return now

    def get_pending_reports(self) -> List[tuple]:
        """Get reports that need to run"""
        now = datetime.utcnow()
        pending = []

        for report_id, config in self.scheduled_reports.items():
            if config["next_run"] <= now:
                pending.append((report_id, config))

        return pending

    def mark_report_run(self, report_id: str):
        """Mark report as run"""
        if report_id in self.scheduled_reports:
            self.scheduled_reports[report_id]["last_run"] = datetime.utcnow()
            self.scheduled_reports[report_id]["next_run"] = self._calculate_next_run(
                self.scheduled_reports[report_id]["schedule"]
            )
