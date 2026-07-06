"""
Tests for advanced filtering and custom report builder.
"""

import pytest
from datetime import datetime, timedelta
from pycostaudit.advanced_filters import (
    AdvancedFilter,
    Aggregator,
    FilterCondition,
    FilterGroup,
    FilterOperator,
    AggregationFunction,
    TimeBucket,
    PresetFilter
)
from pycostaudit.custom_report_builder import (
    CustomReport,
    ReportType,
    ExportFormat,
    ReportTemplate,
    ReportScheduler,
    ReportSchedule
)


@pytest.fixture
def sample_data():
    """Sample cost data"""
    return [
        {
            "timestamp": datetime.utcnow() - timedelta(days=2),
            "operation_type": "API_CALL",
            "provider": "anthropic",
            "region": "us-east-1",
            "total_cost": 10.0,
            "user_id": "user1"
        },
        {
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "operation_type": "FILE_READ",
            "provider": "anthropic",
            "region": "us-east-1",
            "total_cost": 5.0,
            "user_id": "user1"
        },
        {
            "timestamp": datetime.utcnow(),
            "operation_type": "BROWSER_OPERATION",
            "provider": "bedrock",
            "region": "eu-west-1",
            "total_cost": 25.0,
            "user_id": "user2"
        },
        {
            "timestamp": datetime.utcnow(),
            "operation_type": "API_CALL",
            "provider": "anthropic",
            "region": "us-east-1",
            "total_cost": 15.0,
            "user_id": "user1"
        },
    ]


class TestAdvancedFilter:
    """Test advanced filtering"""

    def test_filter_eq(self, sample_data):
        """Test equality filter"""
        f = AdvancedFilter()
        f.add_condition("operation_type", FilterOperator.EQ, "API_CALL")
        result = f.apply(sample_data)
        assert len(result) == 2
        assert all(item["operation_type"] == "API_CALL" for item in result)

    def test_filter_ne(self, sample_data):
        """Test not equal filter"""
        f = AdvancedFilter()
        f.add_condition("operation_type", FilterOperator.NE, "API_CALL")
        result = f.apply(sample_data)
        assert len(result) == 2
        assert all(item["operation_type"] != "API_CALL" for item in result)

    def test_filter_gt(self, sample_data):
        """Test greater than filter"""
        f = AdvancedFilter()
        f.add_condition("total_cost", FilterOperator.GT, 10.0)
        result = f.apply(sample_data)
        assert len(result) == 2
        assert all(item["total_cost"] > 10.0 for item in result)

    def test_filter_in(self, sample_data):
        """Test IN filter"""
        f = AdvancedFilter()
        f.add_condition("provider", FilterOperator.IN, ["anthropic", "bedrock"])
        result = f.apply(sample_data)
        assert len(result) == 4

    def test_filter_between(self, sample_data):
        """Test BETWEEN filter"""
        f = AdvancedFilter()
        f.add_condition("total_cost", FilterOperator.BETWEEN, [5.0, 15.0])
        result = f.apply(sample_data)
        assert len(result) == 3  # 5, 10, 15

    def test_sort(self, sample_data):
        """Test sorting"""
        f = AdvancedFilter()
        f.sort_by("total_cost", "DESC")
        result = f.apply(sample_data)
        assert result[0]["total_cost"] == 25.0
        assert result[-1]["total_cost"] == 5.0

    def test_limit_offset(self, sample_data):
        """Test limit and offset"""
        f = AdvancedFilter()
        f.limit_results(2, offset=1)
        result = f.apply(sample_data)
        assert len(result) == 2

    def test_combined_filters(self, sample_data):
        """Test multiple filters"""
        f = AdvancedFilter()
        f.add_condition("provider", FilterOperator.EQ, "anthropic")
        f.add_condition("total_cost", FilterOperator.GT, 5.0)
        result = f.apply(sample_data)
        assert len(result) == 2


class TestAggregator:
    """Test data aggregation"""

    def test_group_by_operation_type(self, sample_data):
        """Test grouping by operation type"""
        agg = Aggregator()
        agg.group_by("operation_type")
        agg.add_aggregation("total_cost", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("count", AggregationFunction.COUNT, "operation_type")

        result = agg.aggregate(sample_data)
        assert len(result) == 3  # Three operation types
        assert any(item["operation_type"] == "API_CALL" for item in result)

    def test_group_by_provider(self, sample_data):
        """Test grouping by provider"""
        agg = Aggregator()
        agg.group_by("provider")
        agg.add_aggregation("total_cost", AggregationFunction.SUM, "total_cost")

        result = agg.aggregate(sample_data)
        assert len(result) == 2

        anthropic_total = next(r for r in result if r["provider"] == "anthropic")
        assert anthropic_total["total_cost"] == 30.0  # 10 + 5 + 15

    def test_aggregation_functions(self, sample_data):
        """Test different aggregation functions"""
        agg = Aggregator()
        agg.group_by("provider")
        agg.add_aggregation("total", AggregationFunction.SUM, "total_cost")
        agg.add_aggregation("avg", AggregationFunction.AVG, "total_cost")
        agg.add_aggregation("max", AggregationFunction.MAX, "total_cost")
        agg.add_aggregation("min", AggregationFunction.MIN, "total_cost")

        result = agg.aggregate(sample_data)
        anthropic = next(r for r in result if r["provider"] == "anthropic")

        assert anthropic["total"] == 30.0
        assert anthropic["avg"] == 10.0
        assert anthropic["max"] == 15.0
        assert anthropic["min"] == 5.0

    def test_time_bucketing(self, sample_data):
        """Test time bucketing"""
        agg = Aggregator()
        agg.time_bucket_by(TimeBucket.DAY, "timestamp")
        agg.add_aggregation("daily_cost", AggregationFunction.SUM, "total_cost")

        result = agg.aggregate(sample_data)
        assert len(result) >= 1  # At least 1 day of data
        assert all("daily_cost" in item for item in result)


class TestPresetFilters:
    """Test preset filters"""

    def test_last_n_days(self, sample_data):
        """Test last N days filter"""
        f = PresetFilter.last_n_days(1)
        result = f.apply(sample_data)
        assert len(result) > 0

    def test_high_cost(self, sample_data):
        """Test high cost filter"""
        f = PresetFilter.high_cost(10.0)
        result = f.apply(sample_data)
        assert len(result) == 2  # 25.0 and 15.0
        assert all(item["total_cost"] > 10.0 for item in result)

    def test_operation_types(self, sample_data):
        """Test operation type filter"""
        f = PresetFilter.operation_types("API_CALL", "FILE_READ")
        result = f.apply(sample_data)
        assert len(result) == 3

    def test_providers(self, sample_data):
        """Test provider filter"""
        f = PresetFilter.providers("anthropic")
        result = f.apply(sample_data)
        assert len(result) == 3


class TestCustomReport:
    """Test custom report generation"""

    def test_basic_report(self, sample_data):
        """Test basic report generation"""
        report = CustomReport("Test Report")
        generated = report.generate(sample_data)

        assert generated.metadata.name == "Test Report"
        assert len(generated.raw_data) == 4

    def test_report_with_filter(self, sample_data):
        """Test report with filter"""
        report = CustomReport("Filtered Report")
        report.with_preset_filter(PresetFilter.high_cost, 10.0)

        generated = report.generate(sample_data)
        assert len(generated.raw_data) == 2  # 25.0 and 15.0

    def test_report_with_aggregation(self, sample_data):
        """Test report with aggregation"""
        report = CustomReport("Aggregated Report")
        agg = Aggregator()
        agg.group_by("operation_type")
        agg.add_aggregation("total", AggregationFunction.SUM, "total_cost")
        report.with_aggregation(agg)

        generated = report.generate(sample_data)
        assert len(generated.aggregated_data) == 3

    def test_report_export_json(self, sample_data):
        """Test JSON export"""
        report = CustomReport("JSON Report")
        generated = report.generate(sample_data)

        json_str = generated.export_json()
        assert "JSON Report" in json_str
        assert "metadata" in json_str

    def test_report_export_csv(self, sample_data):
        """Test CSV export"""
        report = CustomReport("CSV Report")
        generated = report.generate(sample_data)

        csv_str = generated.export_csv()
        assert len(csv_str) > 0
        assert "operation_type" in csv_str

    def test_report_export_html(self, sample_data):
        """Test HTML export"""
        report = CustomReport("HTML Report")
        generated = report.generate(sample_data)

        html_str = generated.export_html()
        assert "<!DOCTYPE html>" in html_str
        assert "HTML Report" in html_str

    def test_report_export_markdown(self, sample_data):
        """Test Markdown export"""
        report = CustomReport("Markdown Report")
        generated = report.generate(sample_data)

        md_str = generated.export_markdown()
        assert "# Markdown Report" in md_str

    def test_report_summary(self, sample_data):
        """Test report summary"""
        report = CustomReport("Summary Report")
        generated = report.generate(sample_data)

        summary = generated.get_summary()
        assert summary["record_count"] == 4
        assert summary["total_cost"] == 55.0
        assert summary["average_cost"] == 13.75


class TestReportTemplates:
    """Test report templates"""

    def test_cost_breakdown_by_operation(self, sample_data):
        """Test operation breakdown template"""
        report = ReportTemplate.cost_breakdown_by_operation()
        generated = report.generate(sample_data)

        assert len(generated.aggregated_data) == 3
        assert all("operation_type" in item for item in generated.aggregated_data)

    def test_cost_breakdown_by_provider(self, sample_data):
        """Test provider breakdown template"""
        report = ReportTemplate.cost_breakdown_by_provider()
        generated = report.generate(sample_data)

        assert len(generated.aggregated_data) == 2

    def test_regional_cost_comparison(self, sample_data):
        """Test regional comparison template"""
        report = ReportTemplate.regional_cost_comparison()
        generated = report.generate(sample_data)

        assert len(generated.aggregated_data) > 0

    def test_hourly_pattern(self, sample_data):
        """Test hourly pattern template"""
        report = ReportTemplate.hourly_pattern()
        generated = report.generate(sample_data)

        assert generated.metadata.report_type == ReportType.TREND_ANALYSIS


class TestReportScheduler:
    """Test report scheduling"""

    def test_schedule_report(self, sample_data):
        """Test scheduling a report"""
        report = CustomReport("Scheduled Report")
        scheduler = ReportScheduler()

        report_id = scheduler.schedule_report(
            report,
            ReportSchedule.DAILY,
            ["user@example.com"]
        )

        assert report_id in scheduler.scheduled_reports
        assert scheduler.scheduled_reports[report_id]["schedule"] == ReportSchedule.DAILY

    def test_schedule_weekly(self, sample_data):
        """Test weekly scheduling"""
        report = CustomReport("Weekly Report")
        scheduler = ReportScheduler()

        report_id = scheduler.schedule_report(
            report,
            ReportSchedule.WEEKLY,
            ["user@example.com"]
        )

        config = scheduler.scheduled_reports[report_id]
        assert config["next_run"] > datetime.utcnow()

    def test_mark_report_run(self):
        """Test marking report as run"""
        report = CustomReport("Test Report")
        scheduler = ReportScheduler()

        report_id = scheduler.schedule_report(
            report,
            ReportSchedule.DAILY,
            ["user@example.com"]
        )

        old_next_run = scheduler.scheduled_reports[report_id]["next_run"]
        scheduler.mark_report_run(report_id)
        new_next_run = scheduler.scheduled_reports[report_id]["next_run"]

        assert new_next_run > old_next_run


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
