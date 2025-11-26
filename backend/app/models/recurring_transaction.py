"""
RecurringTransaction Model - Wiederkehrende Transaktionen (Verträge)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RecurringTransaction(Base):
    """
    RecurringTransaction Model
    
    Speichert erkannte wiederkehrende Transaktionen (z.B. Miete, Netflix, etc.)
    Wird automatisch durch den RecurringTransactionDetector nach CSV-Import analysiert.
    """
    __tablename__ = "recurring_transactions"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Transaction Pattern
    recipient = Column(String(200), nullable=False, index=True, comment="Recipient name")
    average_amount = Column(Numeric(12, 2), nullable=False, comment="Average transaction amount")
    average_interval_days = Column(Integer, nullable=False, comment="Average days between transactions")
    
    # Occurrence tracking
    first_occurrence = Column(Date, nullable=False, comment="Date of first detected occurrence")
    last_occurrence = Column(Date, nullable=False, index=True, comment="Date of last detected occurrence")
    occurrence_count = Column(Integer, nullable=False, default=0, comment="Total number of occurrences (min. 3)")
    
    # Category (optional)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True, index=True, comment="Is this recurring transaction still active?")
    is_manually_overridden = Column(Boolean, nullable=False, default=False, comment="User manually marked/unmarked this")
    
    # Prediction
    next_expected_date = Column(Date, nullable=True, index=True, comment="Predicted next occurrence date")
    
    # Quality metrics
    confidence_score = Column(Numeric(3, 2), default=1.0, comment="Confidence score (0.0 to 1.0)")
    
    # User notes
    notes = Column(Text, nullable=True, comment="User-provided notes")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    # Use passive_deletes so SQLAlchemy uses the DB's ON DELETE CASCADE
    # instead of emitting UPDATEs that try to set `account_id` to NULL
    # (which fails because the column is NOT NULL).
    account = relationship("Account", backref="recurring_transactions", passive_deletes=True)
    category = relationship("Category", backref="recurring_transactions")
    linked_transactions = relationship("RecurringTransactionLink", back_populates="recurring_transaction", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<RecurringTransaction(id={self.id}, recipient='{self.recipient}', amount={self.average_amount}, interval={self.average_interval_days}d)>"


class RecurringTransactionLink(Base):
    """
    Junction table linking RecurringTransactions to actual DataRows
    """
    __tablename__ = "recurring_transaction_links"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    recurring_transaction_id = Column(Integer, ForeignKey("recurring_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    data_row_id = Column(Integer, ForeignKey("data_rows.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    recurring_transaction = relationship("RecurringTransaction", back_populates="linked_transactions")
    data_row = relationship("DataRow", backref="recurring_link")
    
    def __repr__(self):
        return f"<RecurringTransactionLink(recurring_id={self.recurring_transaction_id}, data_row_id={self.data_row_id})>"
