"""
Data persistence layer for PyTokenCalc v0.7.
Stores cost calculations in SQLite for historical tracking and auditing.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .cost_models import UsageData


class CostDatabase:
    """SQLite database for persistent cost tracking"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or "~/.pytokencalc/costs.db").expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_operations (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    provider TEXT,
                    model TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cost_usd REAL,
                    task_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider
                ON cost_operations(provider)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model
                ON cost_operations(model)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON cost_operations(timestamp)
            """)

            conn.commit()

    def save_operation(self, usage: UsageData, cost_usd: float) -> int:
        """Save a single cost operation"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO cost_operations
                (timestamp, provider, model, input_tokens, output_tokens, cost_usd, task_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.timestamp,
                usage.provider,
                usage.model,
                usage.input_tokens,
                usage.output_tokens,
                cost_usd,
                usage.task_type
            ))
            conn.commit()
            return cursor.lastrowid

    def save_operations(self, usages: List[UsageData], costs: List[float]):
        """Batch save multiple operations"""
        with sqlite3.connect(self.db_path) as conn:
            for usage, cost_usd in zip(usages, costs):
                conn.execute("""
                    INSERT INTO cost_operations
                    (timestamp, provider, model, input_tokens, output_tokens, cost_usd, task_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.timestamp,
                    usage.provider,
                    usage.model,
                    usage.input_tokens,
                    usage.output_tokens,
                    cost_usd,
                    usage.task_type
                ))
            conn.commit()

    def get_operations(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve operations from database"""
        query = "SELECT * FROM cost_operations WHERE 1=1"
        params = []

        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if model:
            query += " AND model = ?"
            params.append(model)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_total_cost(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> float:
        """Get total cost with optional filters"""
        query = "SELECT SUM(cost_usd) as total FROM cost_operations WHERE 1=1"
        params = []

        if provider:
            query += " AND provider = ?"
            params.append(provider)
        if model:
            query += " AND model = ?"
            params.append(model)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            result = cursor.fetchone()
            return result[0] or 0.0

    def clear(self):
        """Delete all operations"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM cost_operations")
            conn.commit()
