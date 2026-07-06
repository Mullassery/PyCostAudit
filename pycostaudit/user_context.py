"""
User context detection from Claude Code history.
Understands user's plan, projects, and work patterns.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict
from datetime import datetime, timedelta


class UserContext:
    """
    Extracts user context from Claude Code history.
    Understands: projects, plan type, work patterns, tools used.
    """

    def __init__(self, history_path: Optional[str] = None):
        self.history_path = Path(history_path or "~/.claude/history.jsonl").expanduser()
        self.projects: Set[str] = set()
        self.tools_used: Dict[str, int] = defaultdict(int)
        self.total_tokens = 0
        self.sessions_count = 0
        self.plan_type = None
        self.active_projects: Dict[str, int] = defaultdict(int)  # project -> token count
        self._load_history()

    def _load_history(self):
        """Load and analyze Claude Code history"""
        if not self.history_path.exists():
            return

        try:
            with open(self.history_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        self._analyze_entry(entry)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    def _analyze_entry(self, entry: Dict):
        """Analyze a single history entry"""
        self.sessions_count += 1

        # Extract project from path
        project_path = entry.get("project", "")
        self._extract_project_from_path(project_path)

        # Extract context from display text (the user's query/task)
        display = entry.get("display", "").lower()
        self._extract_project_from_message({"content": display})

    def _extract_project_from_path(self, project_path: str):
        """Extract project names from directory path"""
        path_lower = project_path.lower()

        project_dirs = {
            "statguard": "statguard",
            "clusteraudiencekit": "clusteraudiencekit",
            "prismnote": "prismnote",
            "pyroboframes": "pyroboframes",
            "pycostaudit": "pycostaudit",
            "streamxl": "streamxl",
        }

        for path_part, project_name in project_dirs.items():
            if path_part in path_lower:
                self.projects.add(project_name)
                self.active_projects[project_name] += 1
                return

    def _extract_project_from_message(self, message: Dict):
        """Extract project hints from message content"""
        content = message.get("content", "").lower()

        # Common project indicators
        projects = {
            "statguard": ["statguard", "data quality", "rust"],
            "clusteraudiencekit": ["clusteraudiencekit", "audience", "segmentation"],
            "prismnote": ["prismnote", "notebook", "sql execution"],
            "pyroboframes": ["pyroboframes", "robot", "mlx", "video"],
            "pycostaudit": ["pycostaudit", "cost tracking", "audit"],
            "streamxl": ["streamxl", "excel", "xlsm"],
        }

        for project, keywords in projects.items():
            if any(kw in content for kw in keywords):
                self.projects.add(project)
                self.active_projects[project] += 1

    def get_user_profile(self) -> Dict:
        """Get comprehensive user profile"""
        return {
            "projects": sorted(list(self.projects)),
            "active_projects": dict(sorted(
                self.active_projects.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "total_tokens": self.total_tokens,
            "sessions_count": self.sessions_count,
            "tools_used": dict(sorted(
                self.tools_used.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            "daily_cost_estimate": self._estimate_daily_cost(),
            "plan_type": self._detect_plan(),
        }

    def _estimate_daily_cost(self) -> float:
        """Estimate daily cost based on token usage"""
        # Using Claude 3.5 Sonnet pricing (default)
        input_rate = 3.00 / 1_000_000
        output_rate = 15.00 / 1_000_000

        # Estimate 30/70 split between input/output
        estimated_input = self.total_tokens * 0.3
        estimated_output = self.total_tokens * 0.7

        total_cost = (estimated_input * input_rate) + (estimated_output * output_rate)
        daily_sessions = max(1, self.sessions_count)

        return total_cost / max(1, daily_sessions)

    def _detect_plan(self) -> str:
        """Detect which Claude Code plan based on usage"""
        daily_cost = self._estimate_daily_cost()

        if daily_cost < 0.50:
            return "Free"
        elif daily_cost < 5.00:
            return "Pro"
        else:
            return "Enterprise"

    def get_contextual_options(self) -> List[tuple]:
        """
        Get analysis options contextual to user's work.

        Returns options most relevant to user's active projects and usage patterns.
        """
        options = []

        # If user works on multiple projects
        if len(self.projects) > 1:
            options.append((3, "Which projects cost most?", "See spending per project"))
            options.append((26, "Team/org tracking", "Allocate costs"))

        # If high token usage
        if self.total_tokens > 100_000:
            options.append((10, "90-day forecast", "Plan quarterly budget"))
            options.append((22, "Plan comparison", "Optimize billing"))

        # If uses many tools (likely automation-focused)
        if len(self.tools_used) > 5:
            options.append((7, "Prompt caching ROI", "Cache repeated prompts"))
            options.append((8, "Batch operations", "Reduce API calls"))

        # Default discovery options
        if not options:
            options.extend([
                (4, "Detect anomalies", "Find cost spikes"),
                (3, "Project breakdown", "Where does money go?"),
                (6, "Recommendations", "Save money ROI"),
            ])

        return options

    def get_welcome_message_contextual(self) -> str:
        """Generate welcome message with user context"""
        profile = self.get_user_profile()

        output = "\n" + "=" * 80 + "\n"
        output += "👋 WELCOME BACK TO PYCOSTAUDIT!\n"
        output += "=" * 80 + "\n\n"

        output += f"📊 YOUR ACTIVITY:\n"
        output += f"   • Sessions: {profile['sessions_count']}\n"
        output += f"   • Plan: {profile['plan_type']}\n\n"

        # Show detected projects as PRIMARY navigation
        if profile["projects"]:
            output += f"📦 YOUR ACTIVE PROJECTS:\n"
            for proj, count in sorted(
                profile["active_projects"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                output += f"   • {proj.upper()}: {count} sessions\n"
            output += "\n   Type project name to analyze costs for that project\n\n"

        # Show general options
        output += "🎯 ANALYZE ACROSS ALL PROJECTS:\n"
        for num, action, reason in self.get_contextual_options()[:3]:
            output += f"   {num}. {action} → {reason}\n"

        output += "\n📚 EXPLORE:\n"
        output += '   "all" = See all 34 analysis types\n'
        output += '   "path" = Recommended learning sequence\n'
        output += "   1-34 = Run specific analysis\n"

        output += "\n" + "=" * 80 + "\n"

        return output

    def should_show_project_insights(self) -> bool:
        """Determine if project-specific insights would be valuable"""
        return len(self.projects) > 0

    def get_project_cost_question(self) -> Optional[str]:
        """Get project-specific cost question"""
        if self.projects:
            top_project = max(self.active_projects.items(), key=lambda x: x[1])[0]
            return f"How much am I spending on {top_project}?"

        return None

    def should_recommend_batching(self) -> bool:
        """Check if batching recommendations would help"""
        github_usage = self.tools_used.get("github", 0)
        return github_usage > 50  # If heavy GitHub tool usage

    def should_recommend_caching(self) -> bool:
        """Check if prompt caching would help"""
        # If using same tools/projects repeatedly
        return len(self.active_projects) >= 2 and self.sessions_count > 10

    def should_recommend_budget_alerts(self) -> bool:
        """Check if budget alerts would be valuable"""
        daily_cost = self._estimate_daily_cost()
        return daily_cost > 1.00  # If spending significantly per day

    def get_personalized_recommendation(self) -> str:
        """Get one top recommendation based on user's specific pattern"""
        profile = self.get_user_profile()

        if self.should_recommend_budget_alerts():
            return (
                "💡 QUICK WIN: You're spending ~${:.2f}/day. "
                "Set a budget alert (#20) to stay in control."
            ).format(profile["daily_cost_estimate"])

        if self.should_recommend_caching():
            return (
                "💡 QUICK WIN: You're using {0} projects repeatedly. "
                "Prompt caching (#7) could save 20-40%."
            ).format(len(self.active_projects))

        if self.should_recommend_batching():
            return (
                "💡 QUICK WIN: You use GitHub tools heavily. "
                "Batching (#8) could reduce API calls by 50%."
            )

        return (
            "💡 QUICK WIN: Run anomaly detection (#4) "
            "to find unusual spending patterns."
        )

    def get_project_cost_insights(self, project_name: str) -> str:
        """Get specific cost insights for a single project"""
        project_lower = project_name.lower()
        session_count = self.active_projects.get(project_lower, 0)

        output = "\n" + "=" * 80 + "\n"
        output += f"📊 COST ANALYSIS FOR {project_name.upper()}\n"
        output += "=" * 80 + "\n\n"

        output += f"Sessions: {session_count}\n"
        output += f"Your focus: This is one of {len(self.active_projects)} active projects\n\n"

        output += "🎯 RECOMMENDED ANALYSES FOR THIS PROJECT:\n"
        output += "  1. Cost breakdown — Where does this project's budget go?\n"
        output += "  2. Anomalies — Any unusual spending patterns?\n"
        output += "  3. Recommendations — How to optimize this project?\n"
        output += "  4. Trends — Is this project getting more expensive?\n"
        output += "  5. Comparison — How does this compare to other projects?\n"

        output += "\n" + "=" * 80 + "\n"

        return output
