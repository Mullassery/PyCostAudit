"""
Tests for advanced forecasting service.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from pycostaudit.database import DatabaseManager, TimeSeriesDataPoint
from pycostaudit.forecasting_service import ForecastingService, BillingPlan


@pytest.fixture
def temp_db():
    """Create temporary database"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path


@pytest.fixture
def forecasting_service(temp_db):
    """Create forecasting service with temp database"""
    db = DatabaseManager(temp_db)
    db.connect()
    db.init_schema()

    service = ForecastingService(db)
    yield service
    db.disconnect()


def insert_sample_data(db, user_id, days=30, daily_cost=50.0):
    """Insert sample time series data"""
    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days-1-i)
        date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Add some variance
        cost = daily_cost + (i % 3) * 5

        ts = TimeSeriesDataPoint(
            user_id=user_id,
            period_start=date,
            total_cost=cost,
            num_operations=10
        )
        db.insert_time_series(ts)


def test_forecast_30_days_api(forecasting_service):
    """Test 30-day forecast on API plan"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    forecast = forecasting_service.forecast_period(
        user_id=user_id,
        days=30,
        plan=BillingPlan.API
    )

    assert forecast["period_days"] == 30
    assert forecast["plan"] == "api"
    assert forecast["projected_daily_cost"] > 0
    assert forecast["projected_total_cost"] > 0
    assert "confidence_interval" in forecast
    assert "trend" in forecast


def test_forecast_60_days_pro(forecasting_service):
    """Test 60-day forecast on Pro plan"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    forecast = forecasting_service.forecast_period(
        user_id=user_id,
        days=60,
        plan=BillingPlan.PRO
    )

    assert forecast["period_days"] == 60
    assert forecast["plan"] == "pro"
    assert forecast["plan_monthly_cost"] == 20.0
    # Pro plan minimum: $20/month * 2 months = $40
    assert forecast["projected_total_cost"] >= 40.0


def test_forecast_90_days_max(forecasting_service):
    """Test 90-day forecast on Max plan"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=150.0)

    forecast = forecasting_service.forecast_period(
        user_id=user_id,
        days=90,
        plan=BillingPlan.MAX
    )

    assert forecast["period_days"] == 90
    assert forecast["plan"] == "max"
    assert forecast["plan_monthly_cost"] == 100.0
    # Max plan minimum: $100/month * 3 months = $300
    assert forecast["projected_total_cost"] >= 300.0


def test_compare_plans(forecasting_service):
    """Test plan comparison"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    comparison = forecasting_service.compare_plans(user_id=user_id, days=30)

    assert "comparisons" in comparison
    assert len(comparison["comparisons"]) == 3  # API, Pro, Max
    assert "best_plan" in comparison
    assert "best_plan_name" in comparison
    assert comparison["monthly_savings"] >= 0


def test_what_if_optimization(forecasting_service):
    """Test optimization scenario analysis"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    scenarios = forecasting_service.what_if_optimization(
        user_id=user_id,
        days=30,
        plan=BillingPlan.API
    )

    assert "scenarios" in scenarios
    assert len(scenarios["scenarios"]) > 0
    assert "base_cost" in scenarios
    assert all("roi" in s for s in scenarios["scenarios"])


def test_breakeven_analysis(forecasting_service):
    """Test plan change breakeven analysis"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    analysis = forecasting_service.get_breakeven_analysis(
        user_id=user_id,
        from_plan=BillingPlan.API,
        to_plan=BillingPlan.PRO
    )

    assert "from_plan" in analysis
    assert "to_plan" in analysis
    assert "monthly_savings" in analysis
    assert "annual_savings" in analysis
    assert "recommendation" in analysis


def test_insufficient_data_forecast(forecasting_service):
    """Test forecast with insufficient data"""
    user_id = "user123"

    with forecasting_service.db:
        # Insert only 3 days (need 7 minimum)
        insert_sample_data(forecasting_service.db, user_id, days=3, daily_cost=50.0)

    forecast = forecasting_service.forecast_period(
        user_id=user_id,
        days=30,
        plan=BillingPlan.API
    )

    assert "warnings" in forecast
    assert any("Insufficient" in w for w in forecast["warnings"])


def test_confidence_intervals(forecasting_service):
    """Test confidence interval calculation"""
    user_id = "user123"

    with forecasting_service.db:
        insert_sample_data(forecasting_service.db, user_id, days=30, daily_cost=50.0)

    forecast = forecasting_service.forecast_period(
        user_id=user_id,
        days=30,
        plan=BillingPlan.API,
        confidence=0.95
    )

    ci = forecast["confidence_interval"]
    assert ci["low"] <= forecast["projected_total_cost"] <= ci["high"]
    assert ci["confidence_level"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
