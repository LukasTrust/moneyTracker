"""
Budget Model - Budgets für Kategorien
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class BudgetPeriod(str, enum.Enum):
    """Budget period types"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


class Budget(Base):
    """
    Budget Model
    
    Budgets können pro Kategorie gesetzt werden mit verschiedenen Zeiträumen.
    Ermöglicht Überwachung von Ausgaben vs. geplante Budgets.
    """
    __tablename__ = "budgets"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Category Relationship
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key to category"
    )
    
    # Budget Details
    period = Column(
        SQLEnum(BudgetPeriod),
        nullable=False,
        default=BudgetPeriod.MONTHLY,
        comment="Budget period: monthly, yearly, quarterly, or custom"
    )
    
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Budget amount (positive value representing spending limit)"
    )
    
    # Date Range
    start_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Budget start date"
    )
    
    end_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Budget end date (inclusive)"
    )
    
    # Optional: Description/Notes
    description = Column(
        String(500),
        nullable=True,
        comment="Optional description or notes for this budget"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    category = relationship("Category", backref="budgets")
    
    def __repr__(self):
        return (
            f"<Budget(id={self.id}, category_id={self.category_id}, "
            f"period='{self.period}', amount={self.amount}, "
            f"start_date={self.start_date}, end_date={self.end_date})>"
        )
    
    def is_active(self, check_date=None):
        """
        Check if budget is currently active
        
        Args:
            check_date: Date to check (defaults to today)
            
        Returns:
            bool: True if budget is active on the given date
        """
        from datetime import date
        
        if check_date is None:
            check_date = date.today()
        
        return self.start_date <= check_date <= self.end_date
