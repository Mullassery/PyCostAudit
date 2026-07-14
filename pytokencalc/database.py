"""
Database layer for PyTokenCalc v0.7.
Provides minimal SQLite storage for cost tracking and operations audit.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from .cost_models import UsageData


class DatabaseManager:
    """SQLite database for persistent cost operation storage"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or "~/.pytokencalc/costs.db").expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY,
                    timestamp DATETIME,
                    provider TEXT,
                    model TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cost_usd REAL,
                    task_type TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_operation(self, usage: UsageData, cost: float) -> int:
        """Save a tracked operation to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO operations
                (timestamp, provider, model, input_tokens, output_tokens, cost_usd, task_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage.timestamp,
                usage.provider,
                usage.model,
                usage.input_tokens,
                usage.output_tokens,
                cost,
                usage.task_type,
                str(usage.metadata) if usage.metadata else None
            ))
            conn.commit()
            return cursor.lastrowid

    def get_operations(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve operations from database"""
        query = "SELECT * FROM operations WHERE 1=1"
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
        query = "SELECT SUM(cost_usd) as total FROM operations WHERE 1=1"
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
            conn.execute("DELETE FROM operations")
            conn.commit()
