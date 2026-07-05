#!/usr/bin/env python3
"""
CostReporter Quick Start Example

Shows the MVP MVP flow:
1. Track operations silently
2. Analyze costs with multipliers
3. Get optimization recommendations
"""

from pycost_reporter import CostReporter
import json


def main():
    # Initialize (creates local SQLite database)
    reporter = CostReporter(db_path="~/.cost-reporter/demo.db")

    print("🚀 CostReporter MVP Demo")
    print("=" * 60)

    # Example 1: Simple API call (baseline cost)
    print("\n1️⃣ Simple API call (baseline)")
    cost = reporter.track_operation(
        operation_type="api_call",
        tokens_input=1000,
        tokens_output=500,
        model="claude-3-5-haiku",
    )
    print(f"   Cost: ${cost['cost_usd']:.4f}")
    print(f"   Multiplier: {cost['multiplier']}x")

    # Example 2: PDF read from local disk (1.2x multiplier)
    print("\n2️⃣ PDF read from local disk (1.2x multiplier)")
    cost = reporter.track_operation(
        operation_type="file_read",
        tokens_input=450,
        tokens_output=120,
        model="claude-3-5-haiku",
        file_source="pdf_local",
    )
    print(f"   Cost: ${cost['cost_usd']:.4f}")
    print(f"   Multiplier: {cost['multiplier']}x")

    # Example 3: PDF read via URL (3.6x multiplier!) - EXPENSIVE
    print("\n3️⃣ PDF read via URL (3.6x multiplier) ⚠️ EXPENSIVE")
    cost = reporter.track_operation(
        operation_type="file_read",
        tokens_input=450,
        tokens_output=120,
        model="claude-3-5-haiku",
        file_source="pdf_url",
    )
    print(f"   Cost: ${cost['cost_usd']:.4f}")
    print(f"   Multiplier: {cost['multiplier']}x")
    print(f"   💡 Moving to disk would save: ${cost['cost_usd'] * (1 - 1.0/3.6):.4f}")

    # Example 4: Browser scraping (55x multiplier!) - KILLER
    print("\n4️⃣ Browser scraping (55x multiplier) 🔴 KILLER COST")
    cost = reporter.track_operation(
        operation_type="browser_op",
        tokens_input=1000,
        tokens_output=500,
        model="claude-3-5-haiku",
    )
    print(f"   Cost: ${cost['cost_usd']:.4f}")
    print(f"   Multiplier: {cost['multiplier']}x")

    # Example 5: MCP invocation (2.4x multiplier)
    print("\n5️⃣ MCP invocation (2.4x multiplier)")
    cost = reporter.track_operation(
        operation_type="mcp_invocation",
        tokens_input=100,
        tokens_output=300,
        model="claude-3-5-haiku",
        mcp_name="web_search",
    )
    print(f"   Cost: ${cost['cost_usd']:.4f}")
    print(f"   Multiplier: {cost['multiplier']}x")

    # Example 6: Session-based tracking (root cause analysis)
    print("\n6️⃣ Session-based tracking (group related operations)")
    session_id = reporter.start_session("feature/auth-oauth")
    reporter.tag_session("branch", "main", session_id)
    reporter.tag_session("feature", "oauth2", session_id)

    # Track multiple operations in session
    reporter.track_operation(
        operation_type="api_call",
        tokens_input=500,
        tokens_output=200,
        model="claude-3-5-haiku",
        session_id=session_id,
    )
    reporter.track_operation(
        operation_type="file_read",
        tokens_input=450,
        tokens_output=120,
        model="claude-3-5-haiku",
        file_source="pdf_url",  # 3.6x!
        session_id=session_id,
    )

    analysis = reporter.end_session(session_id)
    print(f"   Session cost: ${analysis['total_cost_usd']:.4f}")

    # Example 7: Daily cost breakdown
    print("\n7️⃣ Daily cost breakdown")
    breakdown = reporter.analyze_daily()
    print(f"   Total spend today: ${breakdown['total_cost_usd']:.2f}")
    print(f"   Total tokens: {breakdown['total_tokens']:,}")

    # Example 8: Get recommendations
    print("\n8️⃣ Cost optimization recommendations")
    recs = reporter.get_recommendations()
    if "recommendations" in recs:
        for i, rec in enumerate(recs["recommendations"][:3], 1):
            print(f"   {i}. {rec.get('action', 'N/A')}")
            print(f"      Savings: ${rec.get('savings', 'N/A')}")

    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("\nKey insights:")
    print("  • PDF via URL = 3.6x more expensive than local disk")
    print("  • Browser scraping = 55x more expensive than file read")
    print("  • Instruction context = 10-50x hidden overhead")
    print("  • Data warehouse queries = 100x-1000x+ expensive")
    print("  • SaaS MCPs = 10-100x hidden internal overhead")


if __name__ == "__main__":
    main()
