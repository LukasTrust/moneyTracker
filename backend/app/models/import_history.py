"""
ImportHistory Model - Tracks CSV imports for audit and rollback
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class ImportHistory(Base):
    """
    ImportHistory Model
    
    Tracks all CSV imports to enable rollback and provide import audit trail.
    Links to DataRow entries via import_id foreign key.
    """
    __tablename__ = "import_history"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Import Metadata
    filename = Column(String(255), nullable=False, comment="Original filename of uploaded CSV")
    file_hash = Column(String(64), nullable=True, comment="SHA256 hash of file content for duplicate detection")
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Import Statistics
    row_count = Column(Integer, nullable=False, default=0, comment="Total rows in CSV file")
    rows_inserted = Column(Integer, nullable=False, default=0, comment="Number of rows successfully inserted")
    rows_duplicated = Column(Integer, nullable=False, default=0, comment="Number of rows skipped (duplicates)")
    
    # Import Status
    status = Column(String(20), nullable=False, default='success', index=True, comment="Import status: success, partial, failed")
    error_message = Column(Text, nullable=True, comment="Error details if import failed")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="import_history")
    data_rows = relationship("DataRow", back_populates="import_history", cascade="all, delete-orphan")
    
    # Indexes defined in __table_args__ for composite indexes
    __table_args__ = (
        Index('idx_import_history_account_uploaded', 'account_id', 'uploaded_at'),
    )
    
    def __repr__(self):
        return f"<ImportHistory(id={self.id}, account_id={self.account_id}, filename='{self.filename}', status='{self.status}', rows={self.rows_inserted}/{self.row_count})>"
