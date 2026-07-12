"""
Custom budget alerts service with Slack/Email integration.
Handles alert policies, delivery, and suppression.
"""

import os
import json
import hashlib
import smtplib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

from .database import DatabaseManager, AlertConfiguration, AlertHistory


class AlertsService:
    """Service for managing budget alerts and notifications"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.alert_cache = {}  # Track recent alerts to prevent spam

    def evaluate_budget(
        self,
        user_id: str,
        current_cost: float,
        period: str = "daily"
    ) -> List[AlertHistory]:
        """Evaluate if current cost triggers any alerts"""
        alerts_sent = []

        with self.db:
            config = self.db.get_alert_config(user_id)
            if not config or not config.enabled:
                return alerts_sent

            # Get appropriate budget
            budget = self._get_budget_for_period(config, period)
            if not budget:
                return alerts_sent

            # Calculate threshold
            percent_used = (current_cost / budget) * 100
            alert_threshold_percent = config.alert_at_percent * 100

            # Check if alert should be triggered
            if percent_used >= alert_threshold_percent:
                alert = self._create_and_send_alert(
                    user_id=user_id,
                    config=config,
                    alert_type="budget_threshold",
                    current_cost=current_cost,
                    budget_limit=budget,
                    threshold_percent=config.alert_at_percent,
                    percent_used=percent_used,
                    period=period
                )

                if alert:
                    alerts_sent.append(alert)

            # Check critical threshold
            if percent_used >= (config.critical_at_percent * 100):
                alert = self._create_and_send_alert(
                    user_id=user_id,
                    config=config,
                    alert_type="budget_exceeded",
                    current_cost=current_cost,
                    budget_limit=budget,
                    threshold_percent=config.critical_at_percent,
                    percent_used=percent_used,
                    period=period,
                    severity="critical"
                )

                if alert:
                    alerts_sent.append(alert)

        return alerts_sent

    def _get_budget_for_period(self, config: AlertConfiguration, period: str) -> Optional[float]:
        """Get budget amount for period"""
        if period == "daily":
            return config.daily_budget_usd
        elif period == "weekly":
            return config.weekly_budget_usd
        elif period == "monthly":
            return config.monthly_budget_usd
        return None

    def _create_and_send_alert(
        self,
        user_id: str,
        config: AlertConfiguration,
        alert_type: str,
        current_cost: float,
        budget_limit: float,
        threshold_percent: float,
        percent_used: float,
        period: str,
        severity: str = "high"
    ) -> Optional[AlertHistory]:
        """Create alert and send via configured channels"""

        # Check if alert should be suppressed
        if self._is_suppressed(user_id, alert_type):
            return None

        # Create alert record
        alert = AlertHistory(
            user_id=user_id,
            alert_config_id=config.id,
            alert_type=alert_type,
            severity=severity,
            message=self._format_alert_message(
                alert_type, current_cost, budget_limit, percent_used, period
            ),
            current_cost=current_cost,
            budget_limit=budget_limit,
            threshold_percent=threshold_percent,
            status="pending"
        )

        # Send to channels
        with self.db:
            # Send to Slack
            if config.slack_webhook_url:
                sent_to_slack = self.send_slack_alert(config.slack_webhook_url, alert)
                alert.sent_to_slack = sent_to_slack
                if sent_to_slack:
                    alert.status = "sent"

            # Send to Email
            if config.email_address and config.notify_on_budget_threshold:
                sent_to_email = self.send_email_alert(config.email_address, alert)
                alert.sent_to_email = sent_to_email
                if sent_to_email:
                    alert.status = "sent"

            # Send to SMS (critical only)
            if config.sms_phone and severity == "critical":
                sent_to_sms = self.send_sms_alert(config.sms_phone, alert)
                alert.sent_to_sms = sent_to_sms

            # Save to history
            alert.sent_at = datetime.utcnow()
            self._save_alert_history(alert)

            # Update suppression cache
            self._update_suppression_cache(user_id, alert_type)

        return alert

    def send_slack_alert(self, webhook_url: str, alert: AlertHistory) -> bool:
        """Send alert to Slack via webhook"""
        try:
            color = self._get_severity_color(alert.severity)
            timestamp = int(datetime.utcnow().timestamp())

            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"🚨 PyCostAudit: {alert.alert_type.replace('_', ' ').title()}",
                        "text": alert.message,
                        "fields": [
                            {
                                "title": "Current Cost",
                                "value": f"${alert.current_cost:.2f}",
                                "short": True
                            },
                            {
                                "title": "Budget Limit",
                                "value": f"${alert.budget_limit:.2f}",
                                "short": True
                            },
                            {
                                "title": "Severity",
                                "value": alert.severity.upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                                "short": True
                            }
                        ],
                        "footer": "PyCostAudit",
                        "ts": timestamp
                    }
                ]
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200

        except Exception as e:
            logger.error("Error sending Slack alert", exc_info=True)
            return False

    def send_email_alert(self, email_address: str, alert: AlertHistory) -> bool:
        """Send alert via email"""
        try:
            # Get SMTP configuration from environment
            smtp_host = os.getenv("PYCOSTAUDIT_SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("PYCOSTAUDIT_SMTP_PORT", "587"))
            smtp_user = os.getenv("PYCOSTAUDIT_SMTP_USER")
            smtp_password = os.getenv("PYCOSTAUDIT_SMTP_PASSWORD")
            from_email = os.getenv("PYCOSTAUDIT_FROM_EMAIL", smtp_user)

            if not smtp_user or not smtp_password:
                import logging; logger = logging.getLogger(__name__); logger.warning("SMTP credentials not configured")
                return False

            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"PyCostAudit Alert: {alert.alert_type.replace('_', ' ').title()}"
            msg["From"] = from_email
            msg["To"] = email_address

            # HTML content
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #d32f2f;">🚨 PyCostAudit Alert</h2>

                        <p><strong>Alert Type:</strong> {alert.alert_type.replace('_', ' ').title()}</p>
                        <p><strong>Severity:</strong> <span style="color: {self._get_severity_color(alert.severity)}; font-weight: bold;">{alert.severity.upper()}</span></p>

                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p><strong>Current Cost:</strong> ${alert.current_cost:.2f}</p>
                            <p><strong>Budget Limit:</strong> ${alert.budget_limit:.2f}</p>
                            <p><strong>Budget Used:</strong> {(alert.current_cost/alert.budget_limit)*100:.1f}%</p>
                        </div>

                        <p><strong>Message:</strong></p>
                        <p>{alert.message}</p>

                        <p style="color: #666; font-size: 12px; margin-top: 30px;">
                            Sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC<br>
                            <a href="https://github.com/Mullassery/PyCostAudit">PyCostAudit</a> - Track your Claude costs
                        </p>
                    </div>
                </body>
            </html>
            """

            msg.attach(MIMEText(html, "html"))

            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, email_address, msg.as_string())

            return True

        except Exception as e:
            logger.error("Error sending email alert", exc_info=True)
            return False

    def send_sms_alert(self, phone_number: str, alert: AlertHistory) -> bool:
        """Send alert via SMS (placeholder - implement with Twilio)"""
        try:
            # Get Twilio configuration
            twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_from_number = os.getenv("TWILIO_PHONE_NUMBER")

            if not all([twilio_account_sid, twilio_auth_token, twilio_from_number]):
                logger.warning("Twilio credentials not configured")
                return False

            # Format message
            message = f"🚨 PyCostAudit: {alert.alert_type.replace('_', ' ').title()}\n${alert.current_cost:.2f}/${alert.budget_limit:.2f} used\n{alert.message}"

            # Send via Twilio
            from twilio.rest import Client

            client = Client(twilio_account_sid, twilio_auth_token)
            response = client.messages.create(
                body=message,
                from_=twilio_from_number,
                to=phone_number
            )

            return response.sid is not None

        except Exception as e:
            print(f"Error sending SMS alert: {e}")
            return False

    def _format_alert_message(
        self,
        alert_type: str,
        current_cost: float,
        budget_limit: float,
        percent_used: float,
        period: str
    ) -> str:
        """Format alert message based on type"""
        if alert_type == "budget_threshold":
            return (
                f"Your {period} budget is {percent_used:.1f}% used. "
                f"Current: ${current_cost:.2f} / Budget: ${budget_limit:.2f}"
            )
        elif alert_type == "budget_exceeded":
            return (
                f"⚠️ Your {period} budget has been EXCEEDED by {percent_used - 100:.1f}%. "
                f"Current: ${current_cost:.2f} / Budget: ${budget_limit:.2f}"
            )
        else:
            return f"Alert: {alert_type.replace('_', ' ').title()}"

    def _get_severity_color(self, severity: str) -> str:
        """Get hex color for severity level"""
        colors = {
            "low": "#36a64f",      # Green
            "medium": "#ffa500",   # Orange
            "high": "#ff6600",     # Dark orange
            "critical": "#d32f2f"  # Red
        }
        return colors.get(severity, "#666666")

    def _is_suppressed(self, user_id: str, alert_type: str) -> bool:
        """Check if alert should be suppressed due to cooldown"""
        cache_key = f"{user_id}:{alert_type}"

        if cache_key not in self.alert_cache:
            return False

        last_alert_time, count = self.alert_cache[cache_key]
        now = datetime.utcnow()

        # Check if within cooldown period (default 60 minutes)
        if (now - last_alert_time).total_seconds() < 3600:
            return True

        # Reset counter if outside cooldown
        return False

    def _update_suppression_cache(self, user_id: str, alert_type: str):
        """Update suppression cache after sending alert"""
        cache_key = f"{user_id}:{alert_type}"
        now = datetime.utcnow()

        if cache_key in self.alert_cache:
            _, count = self.alert_cache[cache_key]
            self.alert_cache[cache_key] = (now, count + 1)
        else:
            self.alert_cache[cache_key] = (now, 1)

    def _save_alert_history(self, alert: AlertHistory):
        """Save alert to database"""
        self.db.cursor.execute("""
            INSERT INTO alert_history (
                id, user_id, alert_config_id, alert_type, severity,
                message, current_cost, budget_limit, threshold_percent,
                status, sent_to_slack, sent_to_email, sent_to_sms,
                created_at, sent_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id, alert.user_id, alert.alert_config_id,
            alert.alert_type, alert.severity, alert.message,
            alert.current_cost, alert.budget_limit, alert.threshold_percent,
            alert.status, int(alert.sent_to_slack), int(alert.sent_to_email),
            int(alert.sent_to_sms), alert.created_at.isoformat(),
            alert.sent_at.isoformat() if alert.sent_at else None
        ))
        self.db.conn.commit()

    def get_alert_history(
        self,
        user_id: str,
        limit: int = 50,
        alert_type: Optional[str] = None
    ) -> List[AlertHistory]:
        """Get alert history for user"""
        query = "SELECT * FROM alert_history WHERE user_id = ?"
        params = [user_id]

        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.db:
            self.db.cursor.execute(query, params)
            results = []

            for row in self.db.cursor.fetchall():
                results.append(AlertHistory(
                    id=row["id"],
                    user_id=row["user_id"],
                    alert_config_id=row["alert_config_id"],
                    alert_type=row["alert_type"],
                    severity=row["severity"],
                    message=row["message"],
                    current_cost=row["current_cost"],
                    budget_limit=row["budget_limit"],
                    threshold_percent=row["threshold_percent"],
                    status=row["status"],
                    sent_to_slack=bool(row["sent_to_slack"]),
                    sent_to_email=bool(row["sent_to_email"]),
                    sent_to_sms=bool(row["sent_to_sms"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    sent_at=datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None,
                    acknowledged_at=datetime.fromisoformat(row["acknowledged_at"]) if row["acknowledged_at"] else None
                ))

            return results

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Mark alert as acknowledged"""
        try:
            with self.db:
                self.db.cursor.execute("""
                    UPDATE alert_history
                    SET acknowledged_at = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), alert_id))
                self.db.conn.commit()
                return True
        except Exception as e:
            print(f"Error acknowledging alert: {e}")
            return False

    def get_alert_stats(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Get alert statistics for user"""
        with self.db:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

            # Total alerts
            self.db.cursor.execute("""
                SELECT COUNT(*) as count FROM alert_history
                WHERE user_id = ? AND created_at > ?
            """, (user_id, cutoff_date))
            total_alerts = self.db.cursor.fetchone()["count"]

            # By type
            self.db.cursor.execute("""
                SELECT alert_type, COUNT(*) as count FROM alert_history
                WHERE user_id = ? AND created_at > ?
                GROUP BY alert_type
            """, (user_id, cutoff_date))

            by_type = {row["alert_type"]: row["count"] for row in self.db.cursor.fetchall()}

            # By severity
            self.db.cursor.execute("""
                SELECT severity, COUNT(*) as count FROM alert_history
                WHERE user_id = ? AND created_at > ?
                GROUP BY severity
            """, (user_id, cutoff_date))

            by_severity = {row["severity"]: row["count"] for row in self.db.cursor.fetchall()}

            return {
                "total_alerts": total_alerts,
                "by_type": by_type,
                "by_severity": by_severity,
                "period_days": days
            }
