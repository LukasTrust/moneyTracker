"""
Category Model - Kategorien für Transaktionen
Audit reference: 04_backend_models.md - Fix mutable JSON defaults
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, text
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    """
    Category Model
    
    Globale Kategorien mit Mapping-Regeln für automatische Kategorisierung.
    """
    __tablename__ = "categories"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Category Details
    name = Column(String(100), nullable=False, unique=True, index=True)
    color = Column(String(7), nullable=False, default="#3b82f6")  # Hex color code
    icon = Column(String(10), nullable=True)  # Emoji or icon identifier
    
    # Mappings - JSON field containing patterns for matching
    # Structure: {"patterns": ["REWE", "EDEKA", "Amazon", "Gehalt"]}
    # Note: Using lambda for default to avoid mutable default issue
    # Server-side default is set via text() for database-level consistency
    mappings = Column(
        JSON,
        nullable=False,
        default=lambda: {"patterns": []},  # Client-side default (creates new dict each time)
        server_default=text("'{\"patterns\":[]}'"),  # Server-side default for direct DB inserts
        comment="Pattern list for automatic categorization"
    )
    
    # Timestamps (timezone-aware for consistency)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', color='{self.color}')>"
