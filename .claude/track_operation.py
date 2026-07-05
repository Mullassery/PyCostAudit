#!/usr/bin/env python3
"""Track Claude Code operations for cost analysis"""

import json
import sys
from datetime import datetime
from pathlib import Path

def track_operation(operation: str, input_tokens: int, output_tokens: int):
    """Record an operation for cost tracking"""

    db_path = Path.home() / ".pycostaudit" / "skill_data.json"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data
    if db_path.exists():
        with open(db_path) as f:
            data = json.load(f)
    else:
        data = {"session_id": f"session-{datetime.now().isoformat()}", "costs": []}

    # Calculate cost (Claude Opus pricing)
    input_cost = (input_tokens / 1_000_000) * 15.00
    output_cost = (output_tokens / 1_000_000) * 75.00
    total_cost = input_cost + output_cost

    # Record operation
    operation_record = {
        "timestamp": datetime.now().isoformat(),
        "operation": operation,
        "model": "claude-opus-4-8",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "estimated_cost": total_cost,
    }

    data["costs"].append(operation_record)

    # Save
    with open(db_path, "w") as f:
        json.dump(data, f, indent=2)

    return total_cost

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        operation = sys.argv[1]
        input_tokens = int(sys.argv[2])
        output_tokens = int(sys.argv[3])

        cost = track_operation(operation, input_tokens, output_tokens)
        print(f"[PyCostAudit] {operation}: ${cost:.4f}", file=sys.stderr)
    else:
        print("Usage: track_operation.py <operation> <input_tokens> <output_tokens>", file=sys.stderr)
