"""
CLI commands for budget alerts management.
"""

import click
import json
from datetime import datetime

from .database import DatabaseManager
from .alerts_service import AlertsService
from .backend_service import BackendService


@click.group()
def alerts():
    """Manage budget alerts and notifications"""
    pass


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--daily', type=float, help='Daily budget in USD')
@click.option('--weekly', type=float, help='Weekly budget in USD')
@click.option('--monthly', type=float, help='Monthly budget in USD')
@click.option('--slack-webhook', help='Slack webhook URL')
@click.option('--email', help='Email address for notifications')
@click.option('--sms', help='Phone number for SMS alerts (requires Twilio config)')
@click.option('--notify-at', type=float, default=0.75, help='Notify at this percentage (default: 0.75)')
def set_budget(user_id, daily, weekly, monthly, slack_webhook, email, sms, notify_at):
    """Set budget and notification preferences"""
    service = BackendService()
    service.initialize()

    config = service.set_budget(
        user_id=user_id,
        daily=daily,
        weekly=weekly,
        monthly=monthly,
        notify_at_percent=notify_at,
        slack_webhook=slack_webhook,
        email=email
    )

    click.echo(f"✅ Budget configured for {user_id}")
    click.echo(f"   Daily:  ${config.daily_budget_usd or 'Not set'}")
    click.echo(f"   Weekly: ${config.weekly_budget_usd or 'Not set'}")
    click.echo(f"   Monthly: ${config.monthly_budget_usd or 'Not set'}")
    click.echo(f"   Alert at: {config.alert_at_percent * 100:.0f}%")


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--period', type=click.Choice(['daily', 'weekly', 'monthly']), default='daily')
def check(user_id, period):
    """Check if alerts should trigger for current period"""
    service = BackendService()
    service.initialize()

    summary = service.get_daily_summary(user_id)

    db = DatabaseManager()
    db.connect()
    alerts_service = AlertsService(db)

    alerts_list = alerts_service.evaluate_budget(
        user_id=user_id,
        current_cost=summary['total_cost'],
        period=period
    )

    db.disconnect()

    if alerts_list:
        click.echo(f"🚨 {len(alerts_list)} alert(s) triggered:")
        for alert in alerts_list:
            click.echo(f"   [{alert.severity.upper()}] {alert.message}")
    else:
        click.echo("✅ No alerts triggered")
        click.echo(f"   Current cost: ${summary['total_cost']:.2f}")


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--limit', type=int, default=20, help='Number of alerts to show')
@click.option('--type', help='Filter by alert type')
def history(user_id, limit, type):
    """View alert history"""
    db = DatabaseManager()
    db.connect()
    alerts_service = AlertsService(db)

    alert_list = alerts_service.get_alert_history(user_id, limit=limit, alert_type=type)

    db.disconnect()

    if not alert_list:
        click.echo("No alerts found")
        return

    click.echo(f"Alert History ({len(alert_list)} recent):\n")

    for alert in alert_list:
        status_icon = "✅" if alert.status == "sent" else "⏳"
        click.echo(f"{status_icon} [{alert.severity.upper()}] {alert.alert_type.replace('_', ' ').title()}")
        click.echo(f"   Message: {alert.message}")
        click.echo(f"   Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        click.echo(f"   Channels: ", nl=False)

        channels = []
        if alert.sent_to_slack:
            channels.append("Slack")
        if alert.sent_to_email:
            channels.append("Email")
        if alert.sent_to_sms:
            channels.append("SMS")

        click.echo(", ".join(channels) or "None")
        click.echo()


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--alert-id', required=True, help='Alert ID to acknowledge')
def acknowledge(user_id, alert_id):
    """Mark an alert as acknowledged"""
    db = DatabaseManager()
    db.connect()
    alerts_service = AlertsService(db)

    success = alerts_service.acknowledge_alert(alert_id)

    db.disconnect()

    if success:
        click.echo(f"✅ Alert {alert_id} acknowledged")
    else:
        click.echo(f"❌ Failed to acknowledge alert")


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--days', type=int, default=7, help='Number of days to include')
def stats(user_id, days):
    """Show alert statistics"""
    db = DatabaseManager()
    db.connect()
    alerts_service = AlertsService(db)

    alert_stats = alerts_service.get_alert_stats(user_id, days=days)

    db.disconnect()

    click.echo(f"Alert Statistics (last {days} days):\n")
    click.echo(f"Total alerts: {alert_stats['total_alerts']}")

    click.echo("\nBy Type:")
    for alert_type, count in alert_stats['by_type'].items():
        click.echo(f"  {alert_type.replace('_', ' ').title()}: {count}")

    click.echo("\nBy Severity:")
    for severity, count in alert_stats['by_severity'].items():
        click.echo(f"  {severity.upper()}: {count}")


@alerts.command()
@click.option('--user-id', required=True, help='User ID')
def show_config(user_id):
    """Show current budget and alert configuration"""
    db = DatabaseManager()
    db.connect()

    config = db.get_alert_config(user_id)

    db.disconnect()

    if not config:
        click.echo(f"No configuration found for {user_id}")
        return

    click.echo("Budget Configuration:\n")
    click.echo(f"User: {user_id}")
    click.echo(f"Status: {'Enabled' if config.enabled else 'Disabled'}")

    click.echo("\nBudgets:")
    click.echo(f"  Daily:   ${config.daily_budget_usd or 'Not set'}")
    click.echo(f"  Weekly:  ${config.weekly_budget_usd or 'Not set'}")
    click.echo(f"  Monthly: ${config.monthly_budget_usd or 'Not set'}")

    click.echo("\nAlert Thresholds:")
    click.echo(f"  Alert at:   {config.alert_at_percent * 100:.0f}% of budget")
    click.echo(f"  Critical at: {config.critical_at_percent * 100:.0f}% of budget")

    click.echo("\nNotification Channels:")
    click.echo(f"  Slack:  {'Configured' if config.slack_webhook_url else 'Not configured'}")
    click.echo(f"  Email:  {'Configured' if config.email_address else 'Not configured'} ({config.email_address or 'N/A'})")
    click.echo(f"  SMS:    {'Configured' if config.sms_phone else 'Not configured'} ({config.sms_phone or 'N/A'})")

    click.echo("\nNotification Preferences:")
    click.echo(f"  Budget threshold: {'Enabled' if config.notify_on_budget_threshold else 'Disabled'}")
    click.echo(f"  Anomalies:        {'Enabled' if config.notify_on_anomaly else 'Disabled'}")
    click.echo(f"  Spikes:           {'Enabled' if config.notify_on_spike else 'Disabled'}")

    click.echo("\nAlert Suppression:")
    click.echo(f"  Cooldown: {config.alert_cooldown_minutes} minutes")
    click.echo(f"  Max alerts per day: {config.max_alerts_per_day}")


if __name__ == "__main__":
    alerts()
