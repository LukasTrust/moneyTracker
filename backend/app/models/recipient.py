"""
Recipient Model - Normalized Recipients/Senders

Represents a unique recipient/sender with normalized name and aliases.
Used for deduplication and better category matching.
"""
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Recipient(Base):
    """
    Recipient model for normalized recipients/senders
    
    Features:
    - Name normalization (lowercase, trimmed, whitespace cleaned)
    - Alias support for matching variations
    - Automatic deduplication
    - Transaction linking
    """
    __tablename__ = "recipients"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Original name (as it appears most commonly)
    name = Column(String(200), nullable=False)
    
    # Normalized name for matching (lowercase, trimmed, no extra spaces)
    normalized_name = Column(String(200), nullable=False, unique=True, index=True)
    
    # Comma-separated aliases (optional)
    # E.g., "Amazon DE, Amazon.de, AMAZON PAYMENTS"
    aliases = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Number of transactions (for statistics)
    transaction_count = Column(Integer, default=0, nullable=False)
    
    # Relationships
    data_rows = relationship("DataRow", back_populates="recipient_link", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_recipient_normalized', 'normalized_name'),
        Index('idx_recipient_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Recipient(id={self.id}, name='{self.name}', normalized='{self.normalized_name}')>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "normalized_name": self.normalized_name,
            "aliases": self.aliases.split(',') if self.aliases else [],
            "transaction_count": self.transaction_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize recipient name for matching
        
        - Convert to lowercase
        - Strip whitespace
        - Collapse multiple spaces to single space
        - Remove special characters (optional)
        
        Args:
            name: Original name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase and strip
        normalized = name.lower().strip()
        
        # Collapse multiple spaces
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    def add_alias(self, alias: str):
        """
        Add an alias to this recipient
        
        Args:
            alias: New alias to add
        """
        if not alias:
            return
        
        # Normalize alias
        normalized_alias = self.normalize_name(alias)
        
        # Get existing aliases
        existing = self.aliases.split(',') if self.aliases else []
        existing = [a.strip() for a in existing if a.strip()]
        
        # Add if not already present
        if normalized_alias not in existing:
            existing.append(normalized_alias)
            self.aliases = ','.join(existing)
    
    def matches(self, name: str) -> bool:
        """
        Check if a name matches this recipient (exact or alias)
        
        Args:
            name: Name to check
            
        Returns:
            True if matches, False otherwise
        """
        normalized = self.normalize_name(name)
        
        # Check normalized name
        if normalized == self.normalized_name:
            return True
        
        # Check aliases
        if self.aliases:
            aliases = [a.strip() for a in self.aliases.split(',')]
            if normalized in aliases:
                return True
        
        return False
