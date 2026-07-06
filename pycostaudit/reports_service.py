"""
Automated cost reports with HTML emails and scheduled delivery.
Supports daily, weekly, and custom report generation.
"""

import os
import json
import smtplib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import asdict

from .database import DatabaseManager
from .backend_service import BackendService


class ReportsService:
    """Service for generating and sending cost reports"""

    def __init__(self, db: DatabaseManager, backend: BackendService):
        self.db = db
        self.backend = backend

    def generate_daily_report(self, user_id: str, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate daily cost report"""
        if date is None:
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get daily summary
        daily = self.backend.get_daily_summary(user_id, date)

        # Get trend data
        trend = self.backend.get_trend(user_id, days=7)

        # Get configuration
        with self.db:
            config = self.db.get_alert_config(user_id)

        report = {
            "type": "daily",
            "date": date.date().isoformat(),
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "daily": daily,
            "trend": trend,
            "budget": {
                "daily_limit": config.daily_budget_usd if config else None,
                "daily_spent": daily["total_cost"],
                "percent_used": (daily["total_cost"] / config.daily_budget_usd * 100) if config and config.daily_budget_usd else 0
            },
            "recommendations": self._generate_recommendations(daily, trend)
        }

        return report

    def generate_weekly_report(self, user_id: str, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate weekly cost report"""
        if end_date is None:
            end_date = datetime.utcnow()

        start_date = end_date - timedelta(days=7)

        # Get weekly summary
        with self.db:
            ts_data = self.db.get_time_series(user_id, "daily", limit=7)

        weekly_total = sum(d.total_cost for d in ts_data)
        weekly_operations = sum(d.num_operations for d in ts_data)

        # Aggregate by dimension
        by_operation_type = {}
        by_file_format = {}
        by_model = {}
        by_provider = {}

        for ts in ts_data:
            for op_type, cost in ts.by_operation_type.items():
                by_operation_type[op_type] = by_operation_type.get(op_type, 0) + cost

            for fmt, cost in ts.by_file_format.items():
                by_file_format[fmt] = by_file_format.get(fmt, 0) + cost

            for model, cost in ts.by_model.items():
                by_model[model] = by_model.get(model, 0) + cost

            for provider, cost in ts.by_provider.items():
                by_provider[provider] = by_provider.get(provider, 0) + cost

        # Get configuration
        with self.db:
            config = self.db.get_alert_config(user_id)

        # Calculate trends
        daily_costs = [d.total_cost for d in reversed(ts_data)]
        first_half_avg = sum(daily_costs[:3]) / 3 if len(daily_costs) >= 3 else 0
        second_half_avg = sum(daily_costs[-3:]) / 3 if len(daily_costs) >= 3 else 0
        trend_percent = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0

        report = {
            "type": "weekly",
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "weekly": {
                "total_cost": weekly_total,
                "num_operations": weekly_operations,
                "average_daily": weekly_total / 7,
                "by_operation_type": by_operation_type,
                "by_file_format": by_file_format,
                "by_model": by_model,
                "by_provider": by_provider,
                "daily_costs": daily_costs
            },
            "budget": {
                "weekly_limit": config.weekly_budget_usd if config else None,
                "weekly_spent": weekly_total,
                "percent_used": (weekly_total / config.weekly_budget_usd * 100) if config and config.weekly_budget_usd else 0
            },
            "trend": {
                "direction": "up" if trend_percent > 5 else "down" if trend_percent < -5 else "stable",
                "percent": trend_percent
            },
            "recommendations": self._generate_recommendations(
                {"total_cost": weekly_total, "by_operation_type": by_operation_type},
                {"daily_costs": daily_costs, "average_daily": weekly_total / 7}
            )
        }

        return report

    def _generate_recommendations(self, daily: Dict, trend: Dict) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations"""
        recommendations = []

        # Check for expensive operation types
        if "by_operation_type" in daily:
            for op_type, cost in daily["by_operation_type"].items():
                if cost > 50:  # Expensive operation
                    recommendations.append({
                        "type": "high_cost_operation",
                        "operation": op_type,
                        "cost": cost,
                        "suggestion": f"Consider batching or optimizing {op_type} operations"
                    })

        # Check for expensive file formats
        if "by_file_format" in daily:
            if daily["by_file_format"].get("pdf_url", 0) > 20:
                recommendations.append({
                    "type": "file_format_optimization",
                    "current": "pdf_url",
                    "alternative": "pdf_local",
                    "estimated_savings": daily["by_file_format"].get("pdf_url", 0) * 0.72,
                    "suggestion": "Move PDFs to disk storage (3.6x cheaper than URL)"
                })

        # Check for upward trend
        if "average_daily" in trend and len(trend.get("daily_costs", [])) >= 3:
            if trend["daily_costs"][-1] > trend["average_daily"] * 1.5:
                recommendations.append({
                    "type": "spending_spike",
                    "current_daily": trend["daily_costs"][-1],
                    "average_daily": trend["average_daily"],
                    "suggestion": "Spending is 50% above average - investigate recent changes"
                })

        return recommendations

    def render_html_report(self, report: Dict[str, Any]) -> str:
        """Render report as HTML email"""
        if report["type"] == "daily":
            return self._render_daily_html(report)
        elif report["type"] == "weekly":
            return self._render_weekly_html(report)
        else:
            return "<p>Unknown report type</p>"

    def _render_daily_html(self, report: Dict[str, Any]) -> str:
        """Render daily report as HTML"""
        daily = report["daily"]
        budget = report["budget"]
        trend = report["trend"]

        # Build breakdown table
        breakdown_rows = ""
        for op_type, cost in sorted(daily["by_operation_type"].items(), key=lambda x: x[1], reverse=True)[:5]:
            breakdown_rows += f"""
            <tr>
                <td>{op_type.replace('_', ' ').title()}</td>
                <td style="text-align: right;">${cost:.2f}</td>
            </tr>
            """

        # Recommendations
        recommendations_html = ""
        for rec in report.get("recommendations", []):
            recommendations_html += f"""
            <div style="background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0;">
                <strong>💡 {rec.get('suggestion', 'Optimization Opportunity')}</strong>
                <p style="margin: 5px 0 0 0; font-size: 12px;">{rec}</p>
            </div>
            """

        # Color for budget percentage
        percent = budget["percent_used"]
        if percent >= 90:
            color = "#d32f2f"
        elif percent >= 75:
            color = "#ff9800"
        else:
            color = "#36a64f"

        html = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px;">
                    <!-- Header -->
                    <div style="border-bottom: 3px solid #1976d2; padding-bottom: 15px; margin-bottom: 20px;">
                        <h1 style="margin: 0 0 5px 0; color: #1976d2;">PyCostAudit Daily Report</h1>
                        <p style="margin: 0; color: #666; font-size: 14px;">{report['date']}</p>
                    </div>

                    <!-- Budget Summary -->
                    <div style="background-color: #f9f9f9; border-left: 4px solid {color}; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                        <h2 style="margin: 0 0 10px 0; font-size: 18px;">Daily Budget</h2>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                            <div>
                                <p style="margin: 0; font-size: 12px; color: #666;">Spent Today</p>
                                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold; color: {color};">${budget['daily_spent']:.2f}</p>
                            </div>
                            <div>
                                <p style="margin: 0; font-size: 12px; color: #666;">Budget Limit</p>
                                <p style="margin: 5px 0 0 0; font-size: 24px; font-weight: bold;">${budget['daily_limit'] or 'Unlimited'}</p>
                            </div>
                        </div>
                        <div style="margin-top: 10px;">
                            <div style="height: 8px; background-color: #e0e0e0; border-radius: 4px; overflow: hidden;">
                                <div style="height: 100%; width: {min(percent, 100)}%; background-color: {color}; transition: width 0.3s;"></div>
                            </div>
                            <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">{percent:.1f}% of budget used</p>
                        </div>
                    </div>

                    <!-- Cost Breakdown -->
                    <div style="margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">Cost Breakdown</h3>
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <thead>
                                <tr style="background-color: #f0f0f0;">
                                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Operation Type</th>
                                    <th style="text-align: right; padding: 8px; border-bottom: 1px solid #ddd;">Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                {breakdown_rows}
                            </tbody>
                        </table>
                    </div>

                    <!-- 7-Day Trend -->
                    <div style="margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">7-Day Trend</h3>
                        <p style="margin: 10px 0; font-size: 14px;">Average daily cost: ${trend.get('average_daily', 0):.2f}</p>
                        <p style="margin: 0; font-size: 14px; color: {'#d32f2f' if 'up' in trend.get('trend', '') else '#36a64f' if 'down' in trend.get('trend', '') else '#666'};">
                            Trend: {trend.get('trend', 'stable').upper()}
                        </p>
                    </div>

                    <!-- Recommendations -->
                    {f'<div style="margin-bottom: 20px;"><h3 style="margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">Recommendations</h3>{recommendations_html}</div>' if recommendations_html else ''}

                    <!-- Footer -->
                    <div style="border-top: 1px solid #ddd; padding-top: 15px; margin-top: 20px; font-size: 12px; color: #999;">
                        <p style="margin: 0;">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        <p style="margin: 5px 0 0 0;">
                            <a href="https://github.com/Mullassery/PyCostAudit" style="color: #1976d2; text-decoration: none;">PyCostAudit</a> - Track your Claude costs efficiently
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return html

    def _render_weekly_html(self, report: Dict[str, Any]) -> str:
        """Render weekly report as HTML"""
        weekly = report["weekly"]
        budget = report["budget"]
        trend = report["trend"]

        # Build breakdown table
        breakdown_rows = ""
        for op_type, cost in sorted(weekly["by_operation_type"].items(), key=lambda x: x[1], reverse=True)[:5]:
            breakdown_rows += f"""
            <tr>
                <td>{op_type.replace('_', ' ').title()}</td>
                <td style="text-align: right;">${cost:.2f}</td>
            </tr>
            """

        # Daily costs bar
        daily_costs_html = ""
        max_cost = max(weekly["daily_costs"]) if weekly["daily_costs"] else 1
        for i, cost in enumerate(weekly["daily_costs"]):
            date_str = (datetime.utcnow() - timedelta(days=6-i)).strftime("%a")
            pct = (cost / max_cost * 100) if max_cost > 0 else 0
            daily_costs_html += f"""
            <div style="text-align: center; font-size: 12px;">
                <div style="height: 40px; background-color: #1976d2; border-radius: 4px; margin-bottom: 5px; opacity: {0.5 + pct/200};"></div>
                <p style="margin: 0;">{date_str}</p>
                <p style="margin: 0; font-weight: bold;">${cost:.2f}</p>
            </div>
            """

        # Recommendations
        recommendations_html = ""
        for rec in report.get("recommendations", []):
            recommendations_html += f"""
            <div style="background-color: #fff3cd; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0;">
                <strong>💡 {rec.get('suggestion', 'Optimization Opportunity')}</strong>
            </div>
            """

        # Color for budget percentage
        percent = budget["percent_used"]
        if percent >= 90:
            color = "#d32f2f"
        elif percent >= 75:
            color = "#ff9800"
        else:
            color = "#36a64f"

        html = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px;">
                    <!-- Header -->
                    <div style="border-bottom: 3px solid #1976d2; padding-bottom: 15px; margin-bottom: 20px;">
                        <h1 style="margin: 0 0 5px 0; color: #1976d2;">PyCostAudit Weekly Report</h1>
                        <p style="margin: 0; color: #666; font-size: 14px;">{report['start_date']} to {report['end_date']}</p>
                    </div>

                    <!-- Weekly Summary -->
                    <div style="background-color: #f9f9f9; border-left: 4px solid {color}; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                        <h2 style="margin: 0 0 10px 0; font-size: 18px;">Weekly Total</h2>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                            <div>
                                <p style="margin: 0; font-size: 12px; color: #666;">Total Spent</p>
                                <p style="margin: 5px 0 0 0; font-size: 22px; font-weight: bold; color: {color};">${weekly['total_cost']:.2f}</p>
                            </div>
                            <div>
                                <p style="margin: 0; font-size: 12px; color: #666;">Daily Average</p>
                                <p style="margin: 5px 0 0 0; font-size: 22px; font-weight: bold;">${weekly['average_daily']:.2f}</p>
                            </div>
                            <div>
                                <p style="margin: 0; font-size: 12px; color: #666;">Operations</p>
                                <p style="margin: 5px 0 0 0; font-size: 22px; font-weight: bold;">{weekly['num_operations']}</p>
                            </div>
                        </div>
                    </div>

                    <!-- Daily Chart -->
                    <div style="margin-bottom: 20px;">
                        <h3 style="margin: 0 0 15px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">Daily Trend</h3>
                        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px;">
                            {daily_costs_html}
                        </div>
                        <p style="margin: 10px 0 0 0; font-size: 12px; color: {'#d32f2f' if 'up' in trend.get('trend', '') else '#36a64f' if 'down' in trend.get('trend', '') else '#666'};">
                            Week trend: {trend.get('direction', 'stable').upper()} {abs(trend.get('percent', 0)):.1f}%
                        </p>
                    </div>

                    <!-- Cost Breakdown -->
                    <div style="margin-bottom: 20px;">
                        <h3 style="margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">Top Operations</h3>
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <thead>
                                <tr style="background-color: #f0f0f0;">
                                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Type</th>
                                    <th style="text-align: right; padding: 8px; border-bottom: 1px solid #ddd;">Cost</th>
                                </tr>
                            </thead>
                            <tbody>
                                {breakdown_rows}
                            </tbody>
                        </table>
                    </div>

                    <!-- Recommendations -->
                    {f'<div style="margin-bottom: 20px;"><h3 style="margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #1976d2; padding-bottom: 5px;">Recommendations</h3>{recommendations_html}</div>' if recommendations_html else ''}

                    <!-- Footer -->
                    <div style="border-top: 1px solid #ddd; padding-top: 15px; margin-top: 20px; font-size: 12px; color: #999;">
                        <p style="margin: 0;">Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
                        <p style="margin: 5px 0 0 0;">
                            <a href="https://github.com/Mullassery/PyCostAudit" style="color: #1976d2; text-decoration: none;">PyCostAudit</a> - Track your Claude costs efficiently
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """

        return html

    def send_report_email(
        self,
        email_address: str,
        report: Dict[str, Any],
        subject: Optional[str] = None
    ) -> bool:
        """Send report via email"""
        try:
            # Get SMTP configuration
            smtp_host = os.getenv("PYCOSTAUDIT_SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("PYCOSTAUDIT_SMTP_PORT", "587"))
            smtp_user = os.getenv("PYCOSTAUDIT_SMTP_USER")
            smtp_password = os.getenv("PYCOSTAUDIT_SMTP_PASSWORD")
            from_email = os.getenv("PYCOSTAUDIT_FROM_EMAIL", smtp_user)

            if not smtp_user or not smtp_password:
                print("SMTP credentials not configured")
                return False

            # Create email
            if subject is None:
                if report["type"] == "daily":
                    subject = f"PyCostAudit Daily Report - {report['date']}"
                else:
                    subject = f"PyCostAudit Weekly Report - {report['start_date']} to {report['end_date']}"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = email_address

            # HTML content
            html = self.render_html_report(report)
            msg.attach(MIMEText(html, "html"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, email_address, msg.as_string())

            return True

        except Exception as e:
            print(f"Error sending report email: {e}")
            return False

    def schedule_daily_reports(self, schedule_time: str = "09:00"):
        """Schedule daily reports (requires APScheduler or similar)

        Args:
            schedule_time: Time in HH:MM format (UTC)

        Implementation would use APScheduler:
        from apscheduler.schedulers.background import BackgroundScheduler

        scheduler = BackgroundScheduler()
        scheduler.add_job(self.send_daily_reports, 'cron', hour=9, minute=0)
        scheduler.start()
        """
        pass

    def schedule_weekly_reports(self, day: str = "monday", time: str = "09:00"):
        """Schedule weekly reports

        Args:
            day: Day of week (monday-sunday)
            time: Time in HH:MM format (UTC)
        """
        pass
