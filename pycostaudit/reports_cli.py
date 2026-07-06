"""
CLI commands for automated report generation and delivery.
"""

import click
from datetime import datetime, timedelta

from .database import DatabaseManager
from .backend_service import BackendService
from .reports_service import ReportsService


@click.group()
def reports():
    """Generate and send cost reports"""
    pass


@reports.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--date', help='Report date (YYYY-MM-DD, default: today)')
@click.option('--email', help='Email to send report to')
@click.option('--preview', is_flag=True, help='Preview HTML report')
def daily(user_id, date, email, preview):
    """Generate daily cost report"""
    db = DatabaseManager()
    db.connect()

    backend = BackendService()
    backend.initialize()
    service = ReportsService(db, backend)

    # Parse date if provided
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            click.echo(f"❌ Invalid date format. Use YYYY-MM-DD")
            return
    else:
        report_date = None

    # Generate report
    report = service.generate_daily_report(user_id, report_date)

    # Preview or send
    if preview:
        html = service.render_html_report(report)
        click.echo("📧 HTML Report Preview:")
        click.echo("=" * 60)
        click.echo(html[:500] + "..." if len(html) > 500 else html)
        click.echo("=" * 60)
        click.echo(f"Total size: {len(html)} bytes")
    elif email:
        success = service.send_report_email(email, report)
        if success:
            click.echo(f"✅ Report sent to {email}")
        else:
            click.echo(f"❌ Failed to send report. Check SMTP configuration.")
    else:
        click.echo("📊 Daily Report")
        click.echo("=" * 60)
        click.echo(f"Date: {report['date']}")
        click.echo(f"Cost: ${report['daily']['total_cost']:.2f}")
        click.echo(f"Operations: {report['daily']['num_operations']}")
        click.echo()
        click.echo("Top Operations:")
        for op_type, cost in sorted(report['daily']['by_operation_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  {op_type.replace('_', ' ').title()}: ${cost:.2f}")

        if report['budget']['daily_limit']:
            click.echo()
            click.echo(f"Budget: {report['budget']['percent_used']:.1f}% used (${report['daily']['total_cost']:.2f}/${report['budget']['daily_limit']:.2f})")

    db.disconnect()


@reports.command()
@click.option('--user-id', required=True, help='User ID')
@click.option('--end-date', help='Report end date (YYYY-MM-DD, default: today)')
@click.option('--email', help='Email to send report to')
@click.option('--preview', is_flag=True, help='Preview HTML report')
def weekly(user_id, end_date, email, preview):
    """Generate weekly cost report"""
    db = DatabaseManager()
    db.connect()

    backend = BackendService()
    backend.initialize()
    service = ReportsService(db, backend)

    # Parse date if provided
    if end_date:
        try:
            report_end = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            click.echo(f"❌ Invalid date format. Use YYYY-MM-DD")
            return
    else:
        report_end = None

    # Generate report
    report = service.generate_weekly_report(user_id, report_end)

    # Preview or send
    if preview:
        html = service.render_html_report(report)
        click.echo("📧 HTML Report Preview:")
        click.echo("=" * 60)
        click.echo(html[:500] + "..." if len(html) > 500 else html)
        click.echo("=" * 60)
        click.echo(f"Total size: {len(html)} bytes")
    elif email:
        success = service.send_report_email(email, report)
        if success:
            click.echo(f"✅ Report sent to {email}")
        else:
            click.echo(f"❌ Failed to send report. Check SMTP configuration.")
    else:
        click.echo("📊 Weekly Report")
        click.echo("=" * 60)
        click.echo(f"Period: {report['start_date']} to {report['end_date']}")
        click.echo(f"Total Cost: ${report['weekly']['total_cost']:.2f}")
        click.echo(f"Daily Average: ${report['weekly']['average_daily']:.2f}")
        click.echo(f"Operations: {report['weekly']['num_operations']}")
        click.echo()
        click.echo("Top Operations:")
        for op_type, cost in sorted(report['weekly']['by_operation_type'].items(), key=lambda x: x[1], reverse=True)[:5]:
            click.echo(f"  {op_type.replace('_', ' ').title()}: ${cost:.2f}")

        click.echo()
        click.echo(f"Trend: {report['trend']['direction'].upper()} {abs(report['trend']['percent']):.1f}%")

        if report['budget']['weekly_limit']:
            click.echo()
            click.echo(f"Budget: {report['budget']['percent_used']:.1f}% used (${report['weekly']['total_cost']:.2f}/${report['budget']['weekly_limit']:.2f})")

    db.disconnect()


@reports.command()
@click.option('--user-id', required=True, help='User ID')
def schedule_daily(user_id):
    """Schedule daily reports (requires APScheduler)"""
    click.echo("📅 Daily Report Scheduling")
    click.echo("=" * 60)
    click.echo()
    click.echo("To schedule daily reports, add this to your code:")
    click.echo()
    click.echo("from apscheduler.schedulers.background import BackgroundScheduler")
    click.echo("from pycostaudit.reports_service import ReportsService")
    click.echo()
    click.echo("scheduler = BackgroundScheduler()")
    click.echo("scheduler.add_job(")
    click.echo("    lambda: ReportsService(...).send_daily_reports(),")
    click.echo("    'cron',")
    click.echo("    hour=9,")
    click.echo("    minute=0")
    click.echo(")")
    click.echo("scheduler.start()")
    click.echo()
    click.echo("Or use GitHub Actions:")
    click.echo()
    click.echo("name: Daily PyCostAudit Report")
    click.echo("on:")
    click.echo("  schedule:")
    click.echo("    - cron: '0 9 * * *'  # 9 AM UTC daily")
    click.echo("jobs:")
    click.echo("  report:")
    click.echo("    runs-on: ubuntu-latest")
    click.echo("    steps:")
    click.echo("      - run: python -m pycostaudit.reports_cli daily --user-id ${{ secrets.USER_ID }} --email ${{ secrets.EMAIL }}")


@reports.command()
@click.option('--user-id', required=True, help='User ID')
def schedule_weekly(user_id):
    """Schedule weekly reports (requires APScheduler)"""
    click.echo("📅 Weekly Report Scheduling")
    click.echo("=" * 60)
    click.echo()
    click.echo("To schedule weekly reports, add this to your code:")
    click.echo()
    click.echo("from apscheduler.schedulers.background import BackgroundScheduler")
    click.echo("from pycostaudit.reports_service import ReportsService")
    click.echo()
    click.echo("scheduler = BackgroundScheduler()")
    click.echo("scheduler.add_job(")
    click.echo("    lambda: ReportsService(...).send_weekly_reports(),")
    click.echo("    'cron',")
    click.echo("    day_of_week='mon',  # Monday")
    click.echo("    hour=9,")
    click.echo("    minute=0")
    click.echo(")")
    click.echo("scheduler.start()")
    click.echo()
    click.echo("Or use GitHub Actions:")
    click.echo()
    click.echo("name: Weekly PyCostAudit Report")
    click.echo("on:")
    click.echo("  schedule:")
    click.echo("    - cron: '0 9 * * 1'  # 9 AM UTC every Monday")
    click.echo("jobs:")
    click.echo("  report:")
    click.echo("    runs-on: ubuntu-latest")
    click.echo("    steps:")
    click.echo("      - run: python -m pycostaudit.reports_cli weekly --user-id ${{ secrets.USER_ID }} --email ${{ secrets.EMAIL }}")


if __name__ == "__main__":
    reports()
