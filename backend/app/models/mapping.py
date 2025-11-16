"""
Mapping Model - CSV-Header Zuordnungen pro Account
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Mapping(Base):
    """
    Mapping Model
    
    Speichert die Zuordnung von CSV-Headern zu standardisierten Feldnamen.
    Jedes Konto kann eigene Mappings haben.
    """
    __tablename__ = "mappings"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key to Account
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Mapping Details
    csv_header = Column(String(100), nullable=False, comment="Original CSV column name")
    standard_field = Column(String(50), nullable=False, comment="Standardized field name")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationship
    account = relationship("Account", back_populates="mappings")
    
    def __repr__(self):
        return f"<Mapping(id={self.id}, account_id={self.account_id}, '{self.csv_header}' -> '{self.standard_field}')>"
