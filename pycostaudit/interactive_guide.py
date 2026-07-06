"""
Interactive navigation system for Claude Code integration.
Shows available options at the end of each analysis output.
"""

from typing import List, Dict, Callable
from enum import Enum


class AnalysisType(Enum):
    """Types of analyses available"""
    TRENDS = "trends"
    HOURLY_BREAKDOWN = "hourly"
    PROJECT_COSTS = "projects"
    ANOMALIES = "anomalies"
    RECOMMENDATIONS = "recommendations"
    FORECASTING = "forecast"
    BUDGET_TRACKING = "budget"
    EFFICIENCY = "efficiency"
    WORKFLOW = "workflow"


class InteractiveGuide:
    """Displays contextual next steps after each analysis"""

    # Maps analysis type to recommended follow-ups
    ANALYSIS_FLOWS = {
        AnalysisType.ANOMALIES: [
            (3, "Which projects cost the most?", "Identify focus areas"),
            (6, "Give me personalized recommendations", "Get ROI targets"),
            (20, "Set a monthly budget", "Lock spending limits"),
        ],
        AnalysisType.PROJECT_COSTS: [
            (6, "Give me personalized recommendations", "Optimize top cost drivers"),
            (8, "What if I batch operations?", "Model cost reduction"),
            (16, "Which interactions cost most?", "Find expensive sessions"),
        ],
        AnalysisType.RECOMMENDATIONS: [
            (24, "Connect to Slack alerts", "Monitor improvements"),
            (20, "Set a monthly budget", "Track impact"),
            (11, "Generate weekly report", "Share with team"),
        ],
        AnalysisType.TRENDS: [
            (10, "Show 90-day forecast", "Plan ahead"),
            (22, "Should I upgrade plan?", "Optimize billing"),
            (9, "Compare to benchmarks", "See efficiency vs peers"),
        ],
        AnalysisType.BUDGET_TRACKING: [
            (23, "Plan next quarter", "Budget allocation"),
            (21, "What's my ROI?", "Justify spending"),
            (6, "Get recommendations", "Reduce costs"),
        ],
    }

    @staticmethod
    def show_next_steps(analysis_type: AnalysisType) -> str:
        """
        Display next action options based on current analysis.
        Returns formatted string for terminal display.
        """
        options = InteractiveGuide.ANALYSIS_FLOWS.get(
            analysis_type,
            InteractiveGuide._default_options()
        )

        output = "\n" + "=" * 80 + "\n"
        output += "🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?\n"
        output += "=" * 80 + "\n\n"

        for option_num, action, description in options:
            output += f"  {option_num}. {action}\n"
            output += f"     → {description}\n\n"

        output += "Or ask anything else about your Claude Code costs!\n"
        output += "=" * 80 + "\n"

        return output

    @staticmethod
    def _default_options() -> List[tuple]:
        """Default options shown when analysis type isn't mapped"""
        return [
            (4, "Detect anomalies", "Find unusual spending"),
            (3, "Which projects cost most?", "Identify focus areas"),
            (6, "Get recommendations", "ROI-ranked savings"),
        ]

    @staticmethod
    def show_all_options() -> str:
        """Display all 34 available analyses"""
        output = "\n" + "=" * 80 + "\n"
        output += "📚 ALL AVAILABLE ANALYSES (34 options)\n"
        output += "=" * 80 + "\n\n"

        categories = {
            "📊 Analysis & Insights": [
                (1, "Cost trends over time"),
                (2, "Most expensive hours"),
                (3, "Projects by cost"),
                (4, "Anomalies"),
                (5, "Cost per project"),
            ],
            "💡 Optimization": [
                (6, "Personalized recommendations"),
                (7, "Prompt caching savings"),
                (8, "Batch operations ROI"),
                (9, "Efficiency benchmarks"),
                (10, "90-day forecast"),
            ],
            "📋 Reporting": [
                (11, "Weekly report"),
                (12, "Executive summary"),
                (13, "Slack export"),
                (14, "Email reports"),
            ],
            "🔍 Deep Dives": [
                (15, "GitHub ops breakdown"),
                (16, "Most expensive interactions"),
                (17, "Efficiency metrics"),
                (18, "Sessions comparison"),
                (19, "Workflow patterns"),
            ],
            "🎯 Budget & Planning": [
                (20, "Set monthly budget"),
                (21, "ROI analysis"),
                (22, "Plan comparison"),
                (23, "Quarterly plan"),
            ],
            "📈 Advanced": [
                (24, "Slack alerts"),
                (25, "Observability export"),
                (26, "Team tracking"),
                (27, "Compliance audit"),
            ],
            "🛠️ Technical": [
                (28, "Python API examples"),
                (29, "SQL export"),
                (30, "Custom metrics"),
            ],
            "📚 Learning": [
                (31, "All commands"),
                (32, "Advanced filtering"),
                (33, "Cost dimensions"),
                (34, "Custom breakdowns"),
            ],
        }

        for category, options in categories.items():
            output += f"{category}\n"
            for num, name in options:
                output += f"  {num:2}. {name}\n"
            output += "\n"

        output += "=" * 80 + "\n"
        output += "Type the number to run an analysis or ask a question!\n"
        output += "=" * 80 + "\n"

        return output

    @staticmethod
    def show_learning_path() -> str:
        """Display recommended learning path for new users"""
        output = "\n" + "=" * 80 + "\n"
        output += "🚀 RECOMMENDED FIRST-TIME PATH\n"
        output += "=" * 80 + "\n\n"

        path = [
            (4, "Detect anomalies in my usage", "Find cost spikes"),
            (3, "Which projects cost the most?", "Identify where to focus"),
            (6, "Give me personalized recommendations", "Get specific ROI targets"),
            (24, "Connect to Slack for alerts", "Monitor going forward"),
            (20, "Set a monthly budget and track it", "Lock in spending limits"),
        ]

        for i, (num, action, reason) in enumerate(path, 1):
            output += f"Step {i}: {action}\n"
            output += f"  → {reason}\n"
            output += f"  (Option #{num})\n\n"

        output += "=" * 80 + "\n"
        output += "Ready? Start with: Detect anomalies (option 4)\n"
        output += "=" * 80 + "\n"

        return output

    @staticmethod
    def show_project_options(projects: dict) -> str:
        """Show cost analysis options per project"""
        output = "\n" + "=" * 80 + "\n"
        output += "📦 ANALYZE YOUR PROJECTS\n"
        output += "=" * 80 + "\n\n"

        # Sort by session count
        sorted_projects = sorted(projects.items(), key=lambda x: x[1], reverse=True)

        for project, session_count in sorted_projects:
            output += f"• {project.upper()}\n"
            output += f"  Sessions: {session_count}\n"
            output += f"  Options:\n"
            output += f"    ├─ Cost breakdown for {project}\n"
            output += f"    ├─ Anomalies in {project}\n"
            output += f"    ├─ Optimization for {project}\n"
            output += f"    └─ Trend analysis for {project}\n\n"

        output += "=" * 80 + "\n"
        output += "Type project name to analyze it specifically\n"
        output += "Type \"all\" to analyze all projects together\n"
        output += "=" * 80 + "\n"

        return output

    @staticmethod
    def format_result_with_options(
        analysis_result: str,
        analysis_type: AnalysisType,
        show_navigation: bool = True
    ) -> str:
        """
        Wrap analysis result with next-step options.

        Args:
            analysis_result: The analysis output
            analysis_type: Type of analysis just completed
            show_navigation: Whether to show navigation options

        Returns:
            Formatted string with result + next steps
        """
        output = analysis_result

        if show_navigation:
            output += InteractiveGuide.show_next_steps(analysis_type)

        return output


class PromptFlow:
    """Manages user flow through analyses"""

    @staticmethod
    def welcome_message() -> str:
        """Display welcome message with initial options"""
        output = "\n" + "=" * 80 + "\n"
        output += "🎯 PYCOSTAUDIT - WHAT WOULD YOU LIKE TO DO?\n"
        output += "=" * 80 + "\n\n"
        output += "📊 GET STARTED (Recommended first 3):\n"
        output += "  4. Detect anomalies in my usage → Find cost spikes\n"
        output += "  3. Which projects cost most? → Identify focus areas\n"
        output += "  6. Give me optimization recommendations → Get ROI targets\n\n"
        output += "📈 QUICK ACCESS:\n"
        output += "  20. Set a monthly budget\n"
        output += "  10. Show 90-day forecast\n"
        output += "  24. Connect to Slack alerts\n\n"
        output += "📚 EXPLORE:\n"
        output += "  \"all\" = See all 34 analyses\n"
        output += "  \"path\" = Recommended learning sequence\n"
        output += "  or ask anything else about your costs!\n"
        output += "\n" + "=" * 80 + "\n"
        return output

    @staticmethod
    def get_user_prompt() -> str:
        """
        Get formatted prompt for Claude Code to show user.
        This appears after each analysis.
        """
        return "✨ What next? (type a number 1-34, \"all\", \"path\", or ask)\n→ "

    @staticmethod
    def error_with_options(error_msg: str) -> str:
        """Show error message followed by valid options"""
        output = f"\n⚠️  {error_msg}\n"
        output += "\n" + "=" * 80 + "\n"
        output += "💡 TRY ONE OF THESE:\n\n"
        output += "Quick wins:\n"
        output += "  4 = Detect anomalies\n"
        output += "  3 = Project costs breakdown\n"
        output += "  6 = Save money recommendations\n\n"
        output += "Advanced:\n"
        output += "  \"all\" = Full menu (all 34 options)\n"
        output += "  \"path\" = Learning sequence\n"
        output += "  or type a number 1-34\n"
        output += "\n" + "=" * 80 + "\n"
        return output

    @staticmethod
    def parse_user_input(user_input: str) -> tuple:
        """
        Parse user input and return analysis type.

        Returns:
            (analysis_number, is_valid)
        """
        user_input = user_input.strip().lower()

        # Special commands
        if user_input == "all":
            return ("all_options", True)
        if user_input == "path":
            return ("learning_path", True)

        # Try to parse as number
        try:
            num = int(user_input)
            if 1 <= num <= 34:
                return (num, True)
        except ValueError:
            pass

        # If not a number, it's a custom question
        return (user_input, True)  # Let system handle it as natural language


def create_interactive_output(
    analysis: str,
    analysis_type: AnalysisType,
    show_steps: bool = True
) -> str:
    """
    Main function to format analysis output for Claude Code terminal.

    Shows:
    1. Analysis results
    2. Next-step options
    3. Prompt for user input
    """
    output = analysis

    if show_steps:
        output += InteractiveGuide.show_next_steps(analysis_type)

    # Don't add prompt here - let Claude Code handle it
    # The prompt should come from the user interaction layer

    return output
