"""
Category Matcher - Match transactions to categories based on rules
"""
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.category import Category


class CategoryMatcher:
    """
    Service for matching transactions to categories based on mapping rules
    """
    
    def __init__(self, db: Session):
        """
        Initialize with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._categories_cache = None
    
    def _load_categories(self) -> List[Category]:
        """
        Load all categories from database (cached)
        
        Returns:
            List of Category objects
        """
        if self._categories_cache is None:
            self._categories_cache = self.db.query(Category).all()
        return self._categories_cache
    
    def match_category(self, transaction_data: Dict[str, Any]) -> Optional[int]:
        """
        Match a transaction to a category based on mapping rules
        
        Uses word-boundary pattern matching: patterns match whole words only.
        Example: "REWE" matches "REWE Markt" but not "SOMEREWETEXT"
        
        Args:
            transaction_data: Dictionary with transaction data
                            Must contain 'recipient' and/or 'purpose' fields
        
        Returns:
            Category ID if matched, None otherwise
            
        Example:
            >>> transaction_data = {
            ...     "recipient": "REWE Markt",
            ...     "purpose": "Einkauf Lebensmittel"
            ... }
            >>> category_id = matcher.match_category(transaction_data)
            2  # Lebensmittel category
        """
        categories = self._load_categories()
        
        recipient = transaction_data.get('recipient', '') or ''
        purpose = transaction_data.get('purpose', '') or ''
        
        # Combine text for pattern matching (case-insensitive)
        search_text = f"{recipient} {purpose}".lower()
        
        for category in categories:
            mappings = category.mappings or {}
            
            # Check patterns (simplified structure: {"patterns": ["REWE", "Edeka", ...]})
            patterns = mappings.get('patterns', [])
            for pattern in patterns:
                # Word-boundary matching: pattern must be a complete word
                # \b ensures we match whole words only
                pattern_regex = r'\b' + re.escape(pattern.lower()) + r'\b'
                if re.search(pattern_regex, search_text):
                    return category.id
        
        return None
    
    def match_bulk(self, transactions: List[Dict[str, Any]]) -> List[Optional[int]]:
        """
        Match multiple transactions to categories
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of category IDs (None for unmatched)
        """
        return [self.match_category(t) for t in transactions]
    
    def clear_cache(self):
        """
        Clear the categories cache (call after category updates)
        """
        self._categories_cache = None
