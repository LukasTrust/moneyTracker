"""
Transfer Model - Links inter-account transactions
"""
from sqlalchemy import Column, Integer, ForeignKey, Numeric, Date, Boolean, Text, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Transfer(Base):
    """
    Transfer Model
    
    Links two DataRow transactions that represent a transfer between accounts.
    Transfers should be excluded from income/expense statistics to avoid double-counting.
    """
    __tablename__ = "transfers"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys to DataRow transactions
    from_transaction_id = Column(
        Integer, 
        ForeignKey("data_rows.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="Transaction with negative amount (money leaving account)"
    )
    to_transaction_id = Column(
        Integer, 
        ForeignKey("data_rows.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True,
        comment="Transaction with positive amount (money entering account)"
    )
    
    # Transfer metadata
    amount = Column(
        Numeric(12, 2), 
        nullable=False,
        comment="Transfer amount (always positive)"
    )
    transfer_date = Column(
        Date, 
        nullable=False, 
        index=True,
        comment="Date of the transfer"
    )
    notes = Column(
        Text, 
        nullable=True,
        comment="Optional notes about this transfer"
    )
    
    # Detection metadata
    is_auto_detected = Column(
        Boolean, 
        nullable=False, 
        default=False, 
        index=True,
        comment="Whether this transfer was automatically detected"
    )
    confidence_score = Column(
        Numeric(3, 2), 
        nullable=True,
        comment="Confidence score for auto-detection (0.00 to 1.00)"
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    from_transaction = relationship(
        "DataRow", 
        foreign_keys=[from_transaction_id],
        backref="transfers_from"
    )
    to_transaction = relationship(
        "DataRow", 
        foreign_keys=[to_transaction_id],
        backref="transfers_to"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('from_transaction_id != to_transaction_id', name='check_different_transactions'),
        CheckConstraint('amount != 0', name='check_amount_nonzero'),
        CheckConstraint('confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)', name='check_confidence_range'),
    )
    
    def __repr__(self):
        return f"<Transfer(id={self.id}, amount={self.amount}, from={self.from_transaction_id}, to={self.to_transaction_id})>"
    
    def get_direction_for_transaction(self, transaction_id: int) -> str:
        """
        Get the direction of this transfer from the perspective of a specific transaction.
        
        Args:
            transaction_id: The ID of the transaction to check
            
        Returns:
            'outgoing' if money is leaving, 'incoming' if money is entering
        """
        if transaction_id == self.from_transaction_id:
            return 'outgoing'
        elif transaction_id == self.to_transaction_id:
            return 'incoming'
        else:
            raise ValueError(f"Transaction {transaction_id} is not part of this transfer")
    
    def get_counterpart_transaction_id(self, transaction_id: int) -> int:
        """
        Get the ID of the counterpart transaction in this transfer.
        
        Args:
            transaction_id: The ID of one transaction in the transfer
            
        Returns:
            The ID of the other transaction in the transfer
        """
        if transaction_id == self.from_transaction_id:
            return self.to_transaction_id
        elif transaction_id == self.to_transaction_id:
            return self.from_transaction_id
        else:
            raise ValueError(f"Transaction {transaction_id} is not part of this transfer")
