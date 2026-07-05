"""
Database models for the PyCostAudit dashboard.
Uses SQLAlchemy ORM for PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    costs = relationship("Cost", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Cost(Base):
    """Individual API cost record"""
    __tablename__ = "costs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Provider & model info
    provider = Column(String(50), nullable=False, index=True)  # openai, bedrock, gemini
    model = Column(String(100), nullable=False, index=True)

    # Token counts
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)

    # Cost breakdown
    input_cost = Column(Float, nullable=False)
    output_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False, index=True)

    # Details
    details = Column(JSON, default={})  # vision_premium, discounts, etc.
    tags = Column(JSON, default={})  # user_id, project_id, tags, etc.

    # Relationships
    user = relationship("User", back_populates="costs")

    # Indexes for common queries
    __table_args__ = (
        Index("idx_user_timestamp", "user_id", "timestamp"),
        Index("idx_provider_timestamp", "provider", "timestamp"),
        Index("idx_model_timestamp", "model", "timestamp"),
    )

    def __repr__(self):
        return f"<Cost {self.provider} {self.model} ${self.total_cost:.4f}>"


class Budget(Base):
    """User budget configuration"""
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True)

    # Budget settings
    amount = Column(Float, nullable=False)  # Total budget amount
    period = Column(String(20), default="monthly")  # monthly, weekly, daily

    # Alert thresholds
    alert_threshold_percent = Column(Float, default=0.75)  # Alert at 75%
    critical_threshold_percent = Column(Float, default=0.90)  # Critical at 90%

    # Settings
    alerts_enabled = Column(Integer, default=1)
    slack_enabled = Column(Integer, default=1)
    sms_enabled = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    period_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    period_end = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="budgets")

    def __repr__(self):
        return f"<Budget {self.period} ${self.amount}>"


class Alert(Base):
    """Alert record"""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Alert info
    alert_type = Column(String(50), nullable=False, index=True)  # budget_threshold, anomaly, etc.
    severity = Column(String(20), nullable=False)  # low, medium, high, critical

    # Content
    message = Column(String(500), nullable=False)
    provider = Column(String(50))
    cost_amount = Column(Float)

    # Status
    sent_to_slack = Column(Integer, default=0)
    sent_to_sms = Column(Integer, default=0)
    acknowledged = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    acknowledged_at = Column(DateTime)

    # Relationships
    user = relationship("User", back_populates="alerts")

    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
    )

    def __repr__(self):
        return f"<Alert {self.alert_type} {self.severity}>"


class CostSummary(Base):
    """Pre-aggregated daily cost summaries for fast queries"""
    __tablename__ = "cost_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Date
    date = Column(DateTime, nullable=False, index=True)

    # Aggregated costs
    total_cost = Column(Float, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    num_operations = Column(Integer, nullable=False)

    # By provider
    provider_breakdown = Column(JSON)  # {provider: cost, ...}
    model_breakdown = Column(JSON)  # {model: cost, ...}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_user_date", "user_id", "date"),
    )

    def __repr__(self):
        return f"<CostSummary {self.date.date()} ${self.total_cost:.2f}>"
