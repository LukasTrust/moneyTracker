"""
Insight Model - Personalized spending insights
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Insight(Base):
    """
    Insight Model
    
    Stores personalized spending insights for accounts.
    Insights are generated based on transaction patterns, spending trends,
    and behavioral analysis.
    """
    __tablename__ = "insights"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account (NULL = global insight across all accounts)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Insight classification
    insight_type = Column(String(50), nullable=False, index=True, comment="Type of insight (mom_increase, yoy_decrease, etc.)")
    severity = Column(String(20), nullable=False, default='info', comment="Severity level: info, success, warning, alert")
    
    # Content
    title = Column(String(200), nullable=False, comment="Short insight title")
    description = Column(Text, nullable=False, comment="Detailed insight description")
    
    # Additional data (flexible JSON structure)
    # Note: 'metadata' is reserved in SQLAlchemy, so we use 'insight_data' instead
    insight_data = Column(JSON, nullable=True, comment="Additional data: category_id, amount, percentage, period, etc.")
    
    # Priority for display ordering (higher = more important)
    priority = Column(Integer, nullable=False, default=5, index=True, comment="Display priority (1-10)")
    
    # Dismissal tracking
    is_dismissed = Column(Boolean, nullable=False, default=False, index=True, comment="User has dismissed this insight")
    dismissed_at = Column(DateTime(timezone=True), nullable=True, comment="When the insight was dismissed")
    
    # Cooldown tracking (for popup re-appearance)
    last_shown_at = Column(DateTime(timezone=True), nullable=True, index=True, comment="When this insight was last displayed")
    show_count = Column(Integer, nullable=False, default=0, comment="Number of times shown to user")
    cooldown_hours = Column(Integer, nullable=False, default=24, comment="Hours to wait before showing again")
    
    # Validity period
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    valid_until = Column(DateTime(timezone=True), nullable=True, comment="Expiration date for time-sensitive insights")
    
    # Relationships
    account = relationship("Account", back_populates="insights")
    
    def __repr__(self):
        return f"<Insight(id={self.id}, type='{self.insight_type}', account_id={self.account_id}, title='{self.title}')>"


class InsightGenerationLog(Base):
    """
    InsightGenerationLog Model
    
    Tracks when insights were last generated to avoid duplicate generation
    and provide audit trail.
    """
    __tablename__ = "insight_generation_log"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account (NULL = global generation)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Generation metadata
    generation_type = Column(String(50), nullable=False, index=True, comment="Type of generation: mom, yoy, savings_potential, full_analysis")
    insights_generated = Column(Integer, nullable=False, default=0, comment="Number of insights generated")
    
    # Timestamp
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Parameters used for generation (JSON)
    generation_params = Column(JSON, nullable=True, comment="Parameters used: from_date, to_date, thresholds, etc.")
    
    # Relationships
    account = relationship("Account", back_populates="insight_generation_logs")
    
    def __repr__(self):
        return f"<InsightGenerationLog(id={self.id}, type='{self.generation_type}', account_id={self.account_id}, insights={self.insights_generated})>"
