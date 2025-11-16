"""
Account Model - Repräsentiert ein Bankkonto
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Account(Base):
    """
    Account Model
    
    Repräsentiert ein Bankkonto, zu dem CSV-Dateien hochgeladen werden können.
    """
    __tablename__ = "accounts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Account Details
    name = Column(String(100), nullable=False, index=True)
    bank_name = Column(String(100), nullable=True)
    account_number = Column(String(50), nullable=True)
    currency = Column(String(3), nullable=False, default='EUR', comment="Account currency (ISO 4217)")
    description = Column(Text, nullable=True)
    initial_balance = Column(Numeric(precision=15, scale=2), nullable=False, default=0.0, comment="Starting balance of the account")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    mappings = relationship("Mapping", back_populates="account", cascade="all, delete-orphan")
    data_rows = relationship("DataRow", back_populates="account", cascade="all, delete-orphan")
    import_history = relationship("ImportHistory", back_populates="account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', bank='{self.bank_name}')>"
