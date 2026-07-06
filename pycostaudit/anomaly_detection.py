"""
ML-based anomaly detection for cost patterns.
Detects unusual spending spikes, pattern shifts, and statistical outliers.
"""

import json
import statistics
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import asdict
from enum import Enum

from .database import DatabaseManager, AnomalyRecord, TimeSeriesDataPoint


class AnomalyAlgorithm(Enum):
    """Supported anomaly detection algorithms"""
    ZSCORE = "zscore"  # Simple, fast, interpretable
    ISOLATION_FOREST = "isolation_forest"  # Robust to multiple outliers
    SEASONAL_DECOMPOSITION = "seasonal"  # Handles patterns with seasonality
    ISOLATION_FOREST_ENSEMBLE = "ensemble"  # Multiple algorithms combined


class AnomalyDetector:
    """Detect anomalous cost patterns"""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.algorithm = AnomalyAlgorithm.ZSCORE
        self.min_history_days = 7  # Need at least 7 days of data

    def detect_anomalies(
        self,
        user_id: str,
        algorithm: Optional[AnomalyAlgorithm] = None,
        sensitivity: float = 1.0  # 1.0 = normal, 0.5 = very sensitive, 2.0 = less sensitive
    ) -> List[AnomalyRecord]:
        """Detect anomalies in user's cost data"""
        if algorithm is None:
            algorithm = self.algorithm

        with self.db:
            # Get historical data
            ts_data = self.db.get_time_series(user_id, "daily", limit=90)

            if len(ts_data) < self.min_history_days:
                return []  # Not enough data

            anomalies = []

            if algorithm == AnomalyAlgorithm.ZSCORE:
                anomalies = self._detect_zscore(user_id, ts_data, sensitivity)
            elif algorithm == AnomalyAlgorithm.ISOLATION_FOREST:
                anomalies = self._detect_isolation_forest(user_id, ts_data, sensitivity)
            elif algorithm == AnomalyAlgorithm.SEASONAL_DECOMPOSITION:
                anomalies = self._detect_seasonal(user_id, ts_data, sensitivity)
            elif algorithm == AnomalyAlgorithm.ISOLATION_FOREST_ENSEMBLE:
                anomalies = self._detect_ensemble(user_id, ts_data, sensitivity)

            # Save anomalies to database
            for anomaly in anomalies:
                self._save_anomaly(anomaly)

            return anomalies

    def _detect_zscore(
        self,
        user_id: str,
        ts_data: List[TimeSeriesDataPoint],
        sensitivity: float
    ) -> List[AnomalyRecord]:
        """Z-score based anomaly detection (statistical outliers)"""
        anomalies = []

        # Extract costs
        costs = [d.total_cost for d in ts_data]

        if len(costs) < 2:
            return anomalies

        # Calculate mean and std dev
        mean_cost = statistics.mean(costs)
        stdev = statistics.stdev(costs)

        if stdev == 0:
            return anomalies  # All costs are the same

        # Threshold: 3-sigma (adjustable by sensitivity)
        # Higher sensitivity = lower threshold (more detections)
        threshold_sigma = 3.0 * sensitivity  # sensitivity < 1.0 = more sensitive

        # Check each data point
        for i, ts in enumerate(ts_data):
            cost = ts.total_cost
            z_score = (cost - mean_cost) / stdev

            if abs(z_score) > threshold_sigma:
                # Determine if spike or drop
                if cost > mean_cost:
                    anomaly_type = "spike"
                    message = f"Cost spike: ${cost:.2f} vs average ${mean_cost:.2f}"
                else:
                    anomaly_type = "drop"
                    message = f"Unusual low: ${cost:.2f} vs average ${mean_cost:.2f}"

                anomaly = AnomalyRecord(
                    user_id=user_id,
                    anomaly_type=anomaly_type,
                    severity="high" if abs(z_score) > 4 else "medium",
                    observed_value=cost,
                    expected_value=mean_cost,
                    deviation_percent=((cost - mean_cost) / mean_cost * 100) if mean_cost > 0 else 0,
                    z_score=z_score,
                    dimension="daily_cost",
                    dimension_value=ts.period_start.date().isoformat(),
                    message=message,
                    recommendation=self._get_recommendation(cost, mean_cost)
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_isolation_forest(
        self,
        user_id: str,
        ts_data: List[TimeSeriesDataPoint],
        sensitivity: float
    ) -> List[AnomalyRecord]:
        """Isolation Forest anomaly detection (robust to multiple outliers)"""
        anomalies = []

        try:
            from sklearn.ensemble import IsolationForest
        except ImportError:
            print("⚠️  scikit-learn not installed. Install with: pip install scikit-learn")
            return anomalies

        # Prepare features: [cost, day_of_week, hour_of_day, num_operations]
        features = []
        for ts in ts_data:
            features.append([
                ts.total_cost,
                ts.day_of_week,
                ts.hour_of_day,
                ts.num_operations
            ])

        if len(features) < 10:
            return anomalies  # Need minimum data points for forest

        # Train model
        contamination = 0.1 / sensitivity  # Percentage of outliers expected
        contamination = min(0.5, max(0.01, contamination))  # Clamp to reasonable range

        model = IsolationForest(contamination=contamination, random_state=42)
        predictions = model.fit_predict(features)

        # Extract anomalies
        for i, pred in enumerate(predictions):
            if pred == -1:  # Outlier detected
                ts = ts_data[i]
                costs = [d.total_cost for d in ts_data]
                mean_cost = statistics.mean(costs)

                anomaly = AnomalyRecord(
                    user_id=user_id,
                    anomaly_type="unusual_pattern",
                    severity="high",
                    observed_value=ts.total_cost,
                    expected_value=mean_cost,
                    deviation_percent=((ts.total_cost - mean_cost) / mean_cost * 100) if mean_cost > 0 else 0,
                    dimension="multi_dimensional",
                    dimension_value=ts.period_start.date().isoformat(),
                    message=f"Unusual cost pattern detected: ${ts.total_cost:.2f} with {ts.num_operations} operations",
                    recommendation="Review operations and changes from this period"
                )
                anomalies.append(anomaly)

        return anomalies

    def _detect_seasonal(
        self,
        user_id: str,
        ts_data: List[TimeSeriesDataPoint],
        sensitivity: float
    ) -> List[AnomalyRecord]:
        """Seasonal decomposition for pattern-based anomalies"""
        anomalies = []

        costs = [d.total_cost for d in ts_data]

        if len(costs) < 14:  # Need 2 weeks minimum for seasonality
            return anomalies

        # Simple seasonal decomposition: compare against same day of week
        day_of_week_costs = {i: [] for i in range(7)}

        for i, ts in enumerate(ts_data):
            day_of_week_costs[ts.day_of_week].append((ts.total_cost, i))

        # Calculate expected cost for each day of week
        day_averages = {}
        for day, costs_list in day_of_week_costs.items():
            if costs_list:
                day_averages[day] = statistics.mean([c[0] for c in costs_list])

        # Detect anomalies
        threshold_sigma = 2.5 / sensitivity

        for i, ts in enumerate(ts_data):
            expected = day_averages.get(ts.day_of_week, statistics.mean(costs))
            costs_for_day = [c[0] for c in day_of_week_costs[ts.day_of_week]]

            if len(costs_for_day) > 1:
                stdev = statistics.stdev(costs_for_day)
                if stdev > 0:
                    z_score = (ts.total_cost - expected) / stdev

                    if abs(z_score) > threshold_sigma:
                        anomaly = AnomalyRecord(
                            user_id=user_id,
                            anomaly_type="operation_type_shift",
                            severity="medium",
                            observed_value=ts.total_cost,
                            expected_value=expected,
                            deviation_percent=((ts.total_cost - expected) / expected * 100) if expected > 0 else 0,
                            z_score=z_score,
                            dimension="day_of_week",
                            dimension_value=f"day_{ts.day_of_week}",
                            message=f"Unusual for {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][ts.day_of_week]}: ${ts.total_cost:.2f} vs avg ${expected:.2f}",
                            recommendation="Check if operational patterns changed"
                        )
                        anomalies.append(anomaly)

        return anomalies

    def _detect_ensemble(
        self,
        user_id: str,
        ts_data: List[TimeSeriesDataPoint],
        sensitivity: float
    ) -> List[AnomalyRecord]:
        """Ensemble: combine multiple detection methods"""
        anomalies = []
        anomaly_scores = {}  # Track which indices were flagged multiple times

        # Run multiple detectors
        for detector in [
            self._detect_zscore,
            self._detect_isolation_forest,
            self._detect_seasonal
        ]:
            detected = detector(user_id, ts_data, sensitivity)
            for anomaly in detected:
                key = anomaly.dimension_value
                anomaly_scores[key] = anomaly_scores.get(key, 0) + 1

        # Return anomalies that were flagged by multiple detectors
        for dimension_value, count in anomaly_scores.items():
            if count >= 2:  # Flagged by at least 2 methods
                # Find the anomaly record
                all_anomalies = (
                    self._detect_zscore(user_id, ts_data, sensitivity) +
                    self._detect_isolation_forest(user_id, ts_data, sensitivity) +
                    self._detect_seasonal(user_id, ts_data, sensitivity)
                )

                for anomaly in all_anomalies:
                    if anomaly.dimension_value == dimension_value:
                        anomaly.severity = "critical"  # Upgrade severity if multiple methods agree
                        anomalies.append(anomaly)
                        break

        # Remove duplicates
        seen = set()
        unique_anomalies = []
        for anomaly in anomalies:
            key = f"{anomaly.dimension_value}_{anomaly.anomaly_type}"
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(anomaly)

        return unique_anomalies

    def _get_recommendation(self, observed: float, expected: float) -> str:
        """Get recommendation based on deviation"""
        percent_diff = abs((observed - expected) / expected * 100) if expected > 0 else 0

        if observed > expected:
            if percent_diff > 100:
                return "Spending doubled. Review recent changes and operations."
            elif percent_diff > 50:
                return "Spending increased 50%+. Investigate changes."
            else:
                return "Spending elevated. Monitor for issues."
        else:
            if percent_diff > 50:
                return "Spending significantly reduced. Verify if operational changes were intentional."
            else:
                return "Spending below average. Good cost control."

    def _save_anomaly(self, anomaly: AnomalyRecord):
        """Save anomaly to database"""
        self.db.cursor.execute("""
            INSERT INTO anomalies (
                id, user_id, anomaly_type, severity, observed_value,
                expected_value, deviation_percent, z_score, dimension,
                dimension_value, message, recommendation, acknowledged,
                investigated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            anomaly.id, anomaly.user_id, anomaly.anomaly_type, anomaly.severity,
            anomaly.observed_value, anomaly.expected_value, anomaly.deviation_percent,
            anomaly.z_score, anomaly.dimension, anomaly.dimension_value,
            anomaly.message, anomaly.recommendation, int(anomaly.acknowledged),
            int(anomaly.investigated), anomaly.created_at.isoformat()
        ))
        self.db.conn.commit()

    def get_recent_anomalies(
        self,
        user_id: str,
        limit: int = 50,
        days: int = 30
    ) -> List[AnomalyRecord]:
        """Get recent anomalies for user"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self.db:
            self.db.cursor.execute("""
                SELECT * FROM anomalies
                WHERE user_id = ? AND created_at > ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, cutoff, limit))

            anomalies = []
            for row in self.db.cursor.fetchall():
                anomalies.append(AnomalyRecord(
                    id=row["id"],
                    user_id=row["user_id"],
                    anomaly_type=row["anomaly_type"],
                    severity=row["severity"],
                    observed_value=row["observed_value"],
                    expected_value=row["expected_value"],
                    deviation_percent=row["deviation_percent"],
                    z_score=row["z_score"],
                    dimension=row["dimension"],
                    dimension_value=row["dimension_value"],
                    message=row["message"],
                    recommendation=row["recommendation"],
                    acknowledged=bool(row["acknowledged"]),
                    investigated=bool(row["investigated"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    acknowledged_at=datetime.fromisoformat(row["acknowledged_at"]) if row["acknowledged_at"] else None
                ))

            return anomalies

    def get_anomaly_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get anomaly statistics"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with self.db:
            # Total anomalies
            self.db.cursor.execute("""
                SELECT COUNT(*) as count FROM anomalies
                WHERE user_id = ? AND created_at > ?
            """, (user_id, cutoff))
            total = self.db.cursor.fetchone()["count"]

            # By type
            self.db.cursor.execute("""
                SELECT anomaly_type, COUNT(*) as count FROM anomalies
                WHERE user_id = ? AND created_at > ?
                GROUP BY anomaly_type
            """, (user_id, cutoff))
            by_type = {row["anomaly_type"]: row["count"] for row in self.db.cursor.fetchall()}

            # By severity
            self.db.cursor.execute("""
                SELECT severity, COUNT(*) as count FROM anomalies
                WHERE user_id = ? AND created_at > ?
                GROUP BY severity
            """, (user_id, cutoff))
            by_severity = {row["severity"]: row["count"] for row in self.db.cursor.fetchall()}

            # Unacknowledged
            self.db.cursor.execute("""
                SELECT COUNT(*) as count FROM anomalies
                WHERE user_id = ? AND created_at > ? AND acknowledged = 0
            """, (user_id, cutoff))
            unacknowledged = self.db.cursor.fetchone()["count"]

            return {
                "total_anomalies": total,
                "by_type": by_type,
                "by_severity": by_severity,
                "unacknowledged": unacknowledged,
                "period_days": days
            }

    def acknowledge_anomaly(self, anomaly_id: str) -> bool:
        """Mark anomaly as acknowledged"""
        try:
            with self.db:
                self.db.cursor.execute("""
                    UPDATE anomalies
                    SET acknowledged = 1, acknowledged_at = ?
                    WHERE id = ?
                """, (datetime.utcnow().isoformat(), anomaly_id))
                self.db.conn.commit()
                return True
        except Exception as e:
            print(f"Error acknowledging anomaly: {e}")
            return False

    def investigate_anomaly(self, anomaly_id: str) -> bool:
        """Mark anomaly as investigated"""
        try:
            with self.db:
                self.db.cursor.execute("""
                    UPDATE anomalies
                    SET investigated = 1
                    WHERE id = ?
                """, (anomaly_id,))
                self.db.conn.commit()
                return True
        except Exception as e:
            print(f"Error investigating anomaly: {e}")
            return False
