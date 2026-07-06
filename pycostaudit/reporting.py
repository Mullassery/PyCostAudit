"""
Reporting module for PyCostAudit.
Generates reports in multiple formats (PDF, Excel, HTML, Slack, Email, etc.)
"""

from typing import Dict, List, Optional
from datetime import datetime
from pycostaudit.cost_calculator import CostCalculator


class ReportGenerator:
    """Generates cost reports in multiple formats"""

    def __init__(self, cost_calculator: CostCalculator):
        self.calc = cost_calculator
        self.breakdown = cost_calculator.get_cost_breakdown()
        self.forecast = cost_calculator.forecast_monthly_cost()
        self.anomalies = cost_calculator.detect_anomalies()

    def generate_weekly_report(self) -> str:
        """
        TIER 3 TASK 7a: Generate weekly report (Option #11)
        """
        report = []
        report.append("=" * 80)
        report.append("PYCOSTAUDIT WEEKLY COST REPORT")
        report.append("=" * 80)
        report.append("")

        # Header
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Report Period: Past 7 days")
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total sessions: {self.breakdown['sessions_count']}")
        report.append(f"Total cost: ${self.breakdown['total_cost_usd']}")
        report.append(f"Daily average: ${self.breakdown['average_daily_cost_usd']}")
        report.append("")

        # Projects
        report.append("COSTS BY PROJECT")
        report.append("-" * 80)
        for project, data in self.breakdown['projects'].items():
            report.append(f"{project.upper()}: ${data['cost_usd']} ({data['percentage']}%)")
        report.append("")

        # Anomalies
        report.append("ANOMALIES DETECTED")
        report.append("-" * 80)
        if self.anomalies:
            report.append(f"Found {len(self.anomalies)} unusual cost patterns")
            for anom in self.anomalies[:3]:
                report.append(f"  • {anom['project']}: ${anom['cost_usd']} ({anom['multiplier']}x average)")
        else:
            report.append("No anomalies detected - spending is stable")
        report.append("")

        # Forecast
        report.append("FORECAST")
        report.append("-" * 80)
        report.append(f"30-day projection: ${self.forecast['30_day_forecast_usd']}")
        report.append(f"90-day projection: ${self.forecast['90_day_forecast_usd']}")
        report.append(f"Annual projection: ${self.forecast['yearly_forecast_usd']}")
        report.append("")

        report.append("=" * 80)
        return "\n".join(report)

    def generate_executive_summary(self) -> str:
        """
        TIER 3 TASK 7b: Generate executive summary (Option #12)
        """
        summary = []
        summary.append("=" * 80)
        summary.append("EXECUTIVE SUMMARY - CLAUDE CODE COSTS")
        summary.append("=" * 80)
        summary.append("")

        summary.append("KEY METRICS")
        summary.append("-" * 80)
        summary.append(f"Monthly cost: ${self.forecast['30_day_forecast_usd']}")
        summary.append(f"Annual cost: ${self.forecast['yearly_forecast_usd']}")
        summary.append(f"Daily average: ${self.breakdown['average_daily_cost_usd']}")
        summary.append("")

        # Top project
        if self.breakdown['projects']:
            top_project = max(self.breakdown['projects'].items(),
                            key=lambda x: x[1]['cost_usd'])
            summary.append("FOCUS AREA")
            summary.append("-" * 80)
            summary.append(f"Your most expensive project: {top_project[0].upper()}")
            summary.append(f"Cost: ${top_project[1]['cost_usd']} ({top_project[1]['percentage']}%)")
            summary.append("")

        # Opportunities
        summary.append("SAVINGS OPPORTUNITIES")
        summary.append("-" * 80)
        summary.append("• Switch to Haiku for simple tasks: Save 73%")
        summary.append("• Batch operations to off-peak hours: Save 10-30%")
        summary.append(f"• Optimize top project: Save 20-30%")
        summary.append("")

        summary.append("=" * 80)
        return "\n".join(summary)

    def generate_slack_message(self) -> Dict:
        """
        TIER 3 TASK 7c: Generate Slack-compatible report (Option #13)
        Returns dict formatted for Slack API
        """
        return {
            "text": "PyCostAudit Weekly Report",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Weekly Cost Summary"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Cost:*\n${self.breakdown['total_cost_usd']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Daily Average:*\n${self.breakdown['average_daily_cost_usd']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Sessions:*\n{self.breakdown['sessions_count']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*30-Day Forecast:*\n${self.forecast['30_day_forecast_usd']}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Costs by Project:*"
                    }
                }
            ]
        }

    def generate_email_report(self) -> Dict:
        """
        TIER 3 TASK 7d: Generate email report (Option #14)
        Returns dict with email content
        """
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f0f0f0; }}
                    .summary {{ font-size: 18px; margin: 20px 0; }}
                    .highlight {{ background-color: #fff3cd; padding: 10px; }}
                </style>
            </head>
            <body>
                <h1>📊 PyCostAudit Weekly Report</h1>

                <div class="summary">
                    <h2>Summary</h2>
                    <p><strong>Total Cost:</strong> ${self.breakdown['total_cost_usd']}</p>
                    <p><strong>Daily Average:</strong> ${self.breakdown['average_daily_cost_usd']}</p>
                    <p><strong>30-Day Forecast:</strong> ${self.forecast['30_day_forecast_usd']}</p>
                </div>

                <h2>Costs by Project</h2>
                <table>
                    <tr>
                        <th>Project</th>
                        <th>Cost</th>
                        <th>Percentage</th>
                    </tr>
        """

        for project, data in self.breakdown['projects'].items():
            html_content += f"""
                    <tr>
                        <td>{project.upper()}</td>
                        <td>${data['cost_usd']}</td>
                        <td>{data['percentage']}%</td>
                    </tr>
            """

        html_content += """
                </table>

                <div class="highlight">
                    <h2>💡 Recommendations</h2>
                    <ul>
                        <li>Switch to Claude 3.5 Haiku: Save 73%</li>
                        <li>Batch operations to off-peak hours: Save 10-30%</li>
                        <li>Optimize expensive projects: Save 20-30%</li>
                    </ul>
                </div>

                <p><em>Report generated by PyCostAudit - your Claude Code cost optimizer</em></p>
            </body>
        </html>
        """

        return {
            "subject": f"PyCostAudit Weekly Report - {datetime.now().strftime('%Y-%m-%d')}",
            "html": html_content,
            "text": self.generate_weekly_report(),
            "to": "user@example.com",  # Would be configured
        }

    def generate_json_export(self) -> Dict:
        """Export data as JSON"""
        return {
            "generated": datetime.now().isoformat(),
            "breakdown": self.breakdown,
            "forecast": self.forecast,
            "anomalies": self.anomalies[:10],  # Top 10
        }

    def generate_csv_export(self) -> str:
        """Export as CSV for Excel"""
        lines = []
        lines.append("Project,Cost,Percentage,Sessions")

        for project, data in self.breakdown['projects'].items():
            lines.append(
                f"{project},{data['cost_usd']},{data['percentage']}%,"
                f"{sum(1 for s in self.calc.sessions_costs if s.project == project)}"
            )

        return "\n".join(lines)
