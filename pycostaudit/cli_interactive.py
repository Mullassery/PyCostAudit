"""
Interactive CLI for PyCostAudit integrated with Claude Code.
Shows options at every interaction point for seamless workflow.
"""

from typing import Optional
from .interactive_guide import (
    InteractiveGuide,
    AnalysisType,
    PromptFlow,
    create_interactive_output,
)
from .user_context import UserContext


class InteractiveCLI:
    """Main interactive interface for Claude Code integration"""

    def __init__(self):
        self.last_analysis_type = None
        self.user_context = UserContext()  # Auto-loads from ~/.claude/history.jsonl

    def welcome(self) -> str:
        """Display welcome with personalized options from user context"""
        # If user context available, show personalized welcome
        if self.user_context.sessions_count > 0:
            return self.user_context.get_welcome_message_contextual()

        # Otherwise, show generic welcome
        return PromptFlow.welcome_message()

    def process_user_input(self, user_input: str, analysis_result: Optional[str] = None) -> str:
        """
        Process user input and return result with contextual options.

        This is the main entry point for Claude Code integration.
        Every response includes available next steps.
        """
        user_input = user_input.strip()
        user_input_lower = user_input.lower()

        # Handle special commands
        if user_input_lower == "all":
            return InteractiveGuide.show_all_options()

        if user_input_lower == "path":
            return InteractiveGuide.show_learning_path()

        if user_input_lower == "help":
            return self._show_help_with_options()

        if user_input_lower in ["quit", "exit"]:
            return "Thanks for using PyCostAudit! 👋\nBye!"

        if user_input_lower == "projects":
            return InteractiveGuide.show_project_options(self.user_context.active_projects)

        # Check if input is a project name
        if user_input_lower in self.user_context.active_projects:
            return self.user_context.get_project_cost_insights(user_input)

        # Try to parse as analysis number
        try:
            num = int(user_input)
            if 1 <= num <= 34:
                return self._get_analysis_prompt(num)
            else:
                return PromptFlow.error_with_options(
                    f"Option {num} not found. Valid range: 1-34"
                )
        except ValueError:
            pass

        # If not a number or known project, show error with suggestions
        return PromptFlow.error_with_options(
            f"Didn't recognize '{user_input}'. Try:\n"
            "  • A number 1-34 (analysis)\n"
            "  • Project name (statguard, prismnote, etc.)\n"
            "  • \"all\" (see all options)\n"
            "  • \"projects\" (list your projects)"
        )

    def _get_analysis_prompt(self, option_num: int) -> str:
        """Get the analysis description and next options"""
        analyses = {
            1: ("Cost trends over time", AnalysisType.TRENDS),
            2: ("Most expensive hours", AnalysisType.HOURLY_BREAKDOWN),
            3: ("Which projects cost most?", AnalysisType.PROJECT_COSTS),
            4: ("Detect anomalies", AnalysisType.ANOMALIES),
            5: ("Cost per project per day", AnalysisType.PROJECT_COSTS),
            6: ("Personalized recommendations", AnalysisType.RECOMMENDATIONS),
            7: ("Prompt caching ROI", AnalysisType.RECOMMENDATIONS),
            8: ("Batch operations impact", AnalysisType.RECOMMENDATIONS),
            9: ("Efficiency benchmarks", AnalysisType.RECOMMENDATIONS),
            10: ("90-day forecast", AnalysisType.FORECASTING),
            11: ("Weekly report", AnalysisType.TRENDS),
            12: ("Executive summary", AnalysisType.TRENDS),
            13: ("Slack export", AnalysisType.TRENDS),
            14: ("Email reports", AnalysisType.TRENDS),
            15: ("GitHub breakdown", AnalysisType.PROJECT_COSTS),
            16: ("Most expensive interactions", AnalysisType.PROJECT_COSTS),
            17: ("Efficiency metrics", AnalysisType.EFFICIENCY),
            18: ("Session comparison", AnalysisType.EFFICIENCY),
            19: ("Workflow patterns", AnalysisType.WORKFLOW),
            20: ("Set monthly budget", AnalysisType.BUDGET_TRACKING),
            21: ("ROI analysis", AnalysisType.BUDGET_TRACKING),
            22: ("Plan comparison", AnalysisType.BUDGET_TRACKING),
            23: ("Quarterly planning", AnalysisType.BUDGET_TRACKING),
            24: ("Slack alerts", AnalysisType.RECOMMENDATIONS),
            25: ("Observability export", AnalysisType.TRENDS),
            26: ("Team tracking", AnalysisType.PROJECT_COSTS),
            27: ("Compliance audit", AnalysisType.TRENDS),
            28: ("Python API examples", AnalysisType.TRENDS),
            29: ("SQL export", AnalysisType.TRENDS),
            30: ("Custom metrics", AnalysisType.TRENDS),
            31: ("All commands", AnalysisType.TRENDS),
            32: ("Advanced filtering", AnalysisType.TRENDS),
            33: ("Cost dimensions explained", AnalysisType.TRENDS),
            34: ("Custom breakdowns", AnalysisType.TRENDS),
        }

        if option_num not in analyses:
            return PromptFlow.error_with_options(f"Option {option_num} not found")

        title, analysis_type = analyses[option_num]
        self.last_analysis_type = analysis_type

        # In production, actual analysis would run here
        output = f"\n📊 RUNNING: {title}\n"
        output += "=" * 80 + "\n"
        output += "[Analysis would run here with real data]\n"
        output += "=" * 80 + "\n"

        # Show personalized recommendation on first analysis
        if self.user_context.sessions_count > 0:
            output += self.user_context.get_personalized_recommendation() + "\n\n"

        # Show next steps based on this analysis type
        output += InteractiveGuide.show_next_steps(analysis_type)

        return output

    def _show_help_with_options(self) -> str:
        """Display help message with action options"""
        output = "\n" + "=" * 80 + "\n"
        output += "📖 HELP - WHAT CAN PYCOSTAUDIT DO?\n"
        output += "=" * 80 + "\n\n"
        output += "PyCostAudit tracks Claude Code costs across 34 different analyses.\n"
        output += "Start by picking ANY of these:\n\n"
        output += "👉 FOR FIRST-TIME USERS:\n"
        output += "   type: path\n"
        output += "   (Shows 5-step learning sequence)\n\n"
        output += "👉 TO SEE ALL OPTIONS:\n"
        output += "   type: all\n"
        output += "   (Shows all 34 analyses)\n\n"
        output += "👉 TO RUN AN ANALYSIS:\n"
        output += "   type: 1-34\n"
        output += "   (Example: type \"4\" for anomaly detection)\n\n"
        output += "=" * 80 + "\n"
        output += InteractiveGuide.show_next_steps(AnalysisType.ANOMALIES)

        return output


def main_interactive_loop():
    """
    Main entry point for interactive Claude Code integration.
    Demonstrates the flow at every step.
    """
    cli = InteractiveCLI()

    print(cli.welcome())

    while True:
        try:
            user_input = input(PromptFlow.get_user_prompt()).strip()

            if not user_input:
                print(PromptFlow.error_with_options("Please enter a command or option"))
                continue

            result = cli.process_user_input(user_input)
            print(result)

            if user_input in ["quit", "exit"]:
                break

        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(PromptFlow.error_with_options(f"Error: {str(e)}"))


if __name__ == "__main__":
    main_interactive_loop()
