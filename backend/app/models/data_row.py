"""
DataRow Model - Unveränderbare Transaktionsdaten
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index, Date, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class DataRow(Base):
    """
    DataRow Model
    
    Speichert unveränderbare Transaktionsdaten aus CSV-Uploads.
    Jede Zeile ist durch einen SHA256-Hash eindeutig identifizierbar.
    
    REFACTORED: Strukturierte Spalten statt JSON für bessere Performance
    """
    __tablename__ = "data_rows"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Unique Hash for duplicate detection
    row_hash = Column(String(64), nullable=False, unique=True, index=True, comment="SHA256 hash of transaction data")
    
    # ===== STRUCTURED TRANSACTION FIELDS (NEW) =====
    # Core transaction data as typed columns for performance
    transaction_date = Column(Date, nullable=False, index=True, comment="Transaction booking date (ISO format)")
    amount = Column(Numeric(12, 2), nullable=False, comment="Transaction amount (negative = expense, positive = income)")
    recipient = Column(String(200), nullable=True, comment="Recipient or sender name")  # Index defined in __table_args__
    purpose = Column(Text, nullable=True, comment="Transaction purpose/description")
    
    # Additional optional fields
    valuta_date = Column(Date, nullable=True, comment="Value date (Wertstellung)")
    currency = Column(String(3), nullable=False, default='EUR', comment="Currency code (ISO 4217)")
    
    # Raw data for audit trail and additional fields from CSV
    # Contains original CSV data plus any bank-specific fields
    raw_data = Column(JSON, nullable=True, comment="Original CSV data for audit trail")
    
    # Category ID (optional - assigned via category mapping rules)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Recipient ID (optional - normalized recipient/sender)
    recipient_id = Column(Integer, ForeignKey("recipients.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="data_rows")
    category = relationship("Category")
    recipient_link = relationship("Recipient", back_populates="data_rows")
    
    # Optimized Composite Indexes for common query patterns
    __table_args__ = (
        # Primary query pattern: Filter by account + date range
        Index('idx_account_date_range', 'account_id', 'transaction_date'),
        
        # Category-based filtering (used in dashboard and statistics)
        Index('idx_category_date', 'category_id', 'transaction_date'),
        
        # Account + Category for category aggregations
        Index('idx_account_category', 'account_id', 'category_id'),
        
        # Recipient lookup (for deduplication and search)
        Index('idx_recipient_search', 'recipient'),
        
        # Date + Amount for sorting and range queries
        Index('idx_date_amount', 'transaction_date', 'amount'),
        
        # Created timestamp for audit and recent queries
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<DataRow(id={self.id}, date={self.transaction_date}, amount={self.amount}, recipient='{self.recipient}')>"
    
    @property
    def data(self):
        """
        Backwards-compatibility property for legacy code.
        Returns dict with transaction data.
        
        DEPRECATED: Use direct field access instead (transaction_date, amount, etc.)
        """
        return {
            'date': self.transaction_date.isoformat() if self.transaction_date else None,
            'amount': str(self.amount) if self.amount is not None else None,
            'recipient': self.recipient,
            'purpose': self.purpose,
            'valuta_date': self.valuta_date.isoformat() if self.valuta_date else None,
            'currency': self.currency,
            **(self.raw_data or {})  # Include any additional fields from raw_data
        }
