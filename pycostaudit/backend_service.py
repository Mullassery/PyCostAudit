"""
Backend service for PyCostAudit v0.6+
Integrates cost tracking, alerts, forecasting, and analytics.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from .database import (
    DatabaseManager, AlertConfiguration, TimeSeriesDataPoint,
    ForecastCache, AnomalyRecord, RecommendationRecord
)
from .cost_model import CostTracker, Cost


class BackendService:
    """Main service orchestrating all backend operations"""

    def __init__(self, db_path: str = "~/.pycostaudit/pycostaudit.db"):
        self.db = DatabaseManager(db_path)
        self.cost_tracker = CostTracker()

    def initialize(self):
        """Initialize database and schema"""
        with self.db:
            self.db.init_schema()

    def track_cost(
        self,
        user_id: str,
        call_data: Dict[str, Any],
        response_data: Dict[str, Any]
    ) -> Optional[Cost]:
        """Track a cost and aggregate to time series"""
        cost = self.cost_tracker.track_api_call(call_data, response_data)

        if cost and user_id:
            # Aggregate to daily time series
            self._aggregate_to_time_series(user_id, cost)

            # Check if it triggers any alerts
            self._check_alert_triggers(user_id, cost)

        return cost

    def _aggregate_to_time_series(self, user_id: str, cost: Cost):
        """Add cost to daily time series aggregates"""
        with self.db:
            # Get today's date at midnight
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_str = today.isoformat()

            # Check if today's record exists (compare by prefix to handle different times same day)
            self.db.cursor.execute("""
                SELECT id FROM time_series_data
                WHERE user_id = ? AND period_start LIKE ?
            """, (user_id, today_str[:10] + "%"))
            existing = self.db.cursor.fetchone()

            if existing:
                # Update existing record
                self.db.cursor.execute("""
                    UPDATE time_series_data
                    SET total_cost = total_cost + ?,
                        num_operations = num_operations + 1
                    WHERE id = ?
                """, (cost.total_cost, existing["id"]))
                self.db.conn.commit()
            else:
                # Create new record
                ts = TimeSeriesDataPoint(
                    user_id=user_id,
                    period_start=today,
                    period_type="daily",
                    total_cost=cost.total_cost,
                    num_operations=1,
                    hour_of_day=datetime.utcnow().hour,
                    day_of_week=datetime.utcnow().weekday()
                )
                self.db.insert_time_series(ts)

    def _check_alert_triggers(self, user_id: str, cost: Cost):
        """Check if cost triggers any alerts"""
        with self.db:
            config = self.db.get_alert_config(user_id)
            if not config or not config.enabled:
                return

            # Check daily budget threshold
            if config.daily_budget_usd:
                self._check_daily_budget(user_id, config, cost)

    def _check_daily_budget(
        self,
        user_id: str,
        config: AlertConfiguration,
        cost: Cost
    ):
        """Check if daily cost exceeds budget threshold"""
        with self.db:
            # Get today's total
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_str = today.isoformat()

            self.db.cursor.execute("""
                SELECT total_cost FROM time_series_data
                WHERE user_id = ? AND period_start LIKE ?
            """, (user_id, today_str[:10] + "%"))

            row = self.db.cursor.fetchone()
            today_total = row["total_cost"] if row else cost.total_cost

            # Calculate percentage
            percent_used = (today_total / config.daily_budget_usd) * 100

            # Trigger alert if threshold exceeded
            if percent_used >= (config.alert_at_percent * 100):
                self._create_alert(
                    user_id,
                    config.id,
                    alert_type="budget_threshold",
                    message=f"Daily budget {percent_used:.1f}% used (${today_total:.2f}/${config.daily_budget_usd:.2f})",
                    current_cost=today_total,
                    budget_limit=config.daily_budget_usd,
                    threshold_percent=config.alert_at_percent
                )

    def _create_alert(
        self,
        user_id: str,
        config_id: str,
        alert_type: str,
        message: str,
        current_cost: float,
        budget_limit: float,
        threshold_percent: float
    ):
        """Create and send an alert"""
        with self.db:
            self.db.cursor.execute("""
                INSERT INTO alert_history (
                    id, user_id, alert_config_id, alert_type, message,
                    current_cost, budget_limit, threshold_percent,
                    created_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()), user_id, config_id, alert_type,
                message, current_cost, budget_limit, threshold_percent,
                datetime.utcnow().isoformat(), "pending"
            ))
            self.db.conn.commit()

    def set_budget(
        self,
        user_id: str,
        daily: Optional[float] = None,
        weekly: Optional[float] = None,
        monthly: Optional[float] = None,
        notify_at_percent: float = 0.75,
        slack_webhook: Optional[str] = None,
        email: Optional[str] = None
    ) -> AlertConfiguration:
        """Set budget configuration for user"""
        with self.db:
            config = self.db.get_alert_config(user_id)

            if config:
                # Update existing
                if daily is not None:
                    config.daily_budget_usd = daily
                if weekly is not None:
                    config.weekly_budget_usd = weekly
                if monthly is not None:
                    config.monthly_budget_usd = monthly
                if slack_webhook:
                    config.slack_webhook_url = slack_webhook
                if email:
                    config.email_address = email

                config.alert_at_percent = notify_at_percent
                config.updated_at = datetime.utcnow()

                # Update in DB
                self.db.cursor.execute("""
                    UPDATE alert_configurations
                    SET daily_budget_usd = ?,
                        weekly_budget_usd = ?,
                        monthly_budget_usd = ?,
                        alert_at_percent = ?,
                        slack_webhook_url = ?,
                        email_address = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    config.daily_budget_usd,
                    config.weekly_budget_usd,
                    config.monthly_budget_usd,
                    config.alert_at_percent,
                    config.slack_webhook_url,
                    config.email_address,
                    config.updated_at.isoformat(),
                    config.id
                ))
                self.db.conn.commit()
            else:
                # Create new
                config = AlertConfiguration(
                    user_id=user_id,
                    daily_budget_usd=daily,
                    weekly_budget_usd=weekly,
                    monthly_budget_usd=monthly,
                    alert_at_percent=notify_at_percent,
                    slack_webhook_url=slack_webhook,
                    email_address=email
                )
                self.db.insert_alert_config(config)

            return config

    def get_daily_summary(self, user_id: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily cost summary"""
        if date is None:
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=1)
            if not ts_data:
                return {
                    "date": date.date().isoformat(),
                    "total_cost": 0.0,
                    "num_operations": 0,
                    "by_operation_type": {},
                    "by_file_format": {},
                    "by_model": {},
                    "by_provider": {}
                }

            data = ts_data[0]
            return {
                "date": data.period_start.date().isoformat(),
                "total_cost": data.total_cost,
                "num_operations": data.num_operations,
                "by_operation_type": data.by_operation_type,
                "by_file_format": data.by_file_format,
                "by_model": data.by_model,
                "by_provider": data.by_provider
            }

    def get_trend(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get cost trend over last N days"""
        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=days)

            daily_costs = [d.total_cost for d in reversed(ts_data)]
            dates = [d.period_start.date().isoformat() for d in reversed(ts_data)]

            avg_cost = sum(daily_costs) / len(daily_costs) if daily_costs else 0
            total_period = sum(daily_costs)

            return {
                "period_days": len(ts_data),
                "daily_costs": daily_costs,
                "dates": dates,
                "average_daily": avg_cost,
                "total_period": total_period,
                "trend": self._calculate_trend(daily_costs)
            }

    def _calculate_trend(self, daily_costs: List[float]) -> str:
        """Calculate if trend is up, down, or stable"""
        if len(daily_costs) < 2:
            return "insufficient_data"

        first_half = sum(daily_costs[:len(daily_costs)//2]) / (len(daily_costs)//2 + 1)
        second_half = sum(daily_costs[len(daily_costs)//2:]) / (len(daily_costs) - len(daily_costs)//2)

        percent_change = ((second_half - first_half) / first_half) * 100 if first_half > 0 else 0

        if abs(percent_change) < 5:
            return "stable"
        elif percent_change > 0:
            return f"up_{abs(percent_change):.1f}%"
        else:
            return f"down_{abs(percent_change):.1f}%"
