"""
Category Matcher - Match transactions to categories based on rules
"""
import re
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.category import Category


CompiledPattern = Tuple[re.Pattern, int, str]


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
        # Precompiled flat list of (regex, category_id, pattern)
        self._compiled_patterns: List[CompiledPattern] = []
    
    def _load_categories(self) -> List[Category]:
        """
        Load all categories from database (cached)
        
        Returns:
            List of Category objects
        """
        if self._categories_cache is None:
            self._categories_cache = self.db.query(Category).all()
            # Build compiled pattern cache for faster matching
            compiled: List[CompiledPattern] = []
            for category in self._categories_cache:
                mappings = category.mappings or {}
                patterns = mappings.get('patterns', [])
                # Sort patterns by length desc to prefer longer (more specific) patterns
                patterns_sorted = sorted(patterns, key=lambda p: len(p or ""), reverse=True)
                for pattern in patterns_sorted:
                    if not pattern:
                        continue
                    try:
                        regex = re.compile(r"\b" + re.escape(pattern.lower()) + r"\b")
                        compiled.append((regex, category.id, pattern))
                    except re.error:
                        # Skip invalid patterns but keep system stable
                        continue

            self._compiled_patterns = compiled

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
        # Ensure compiled patterns are ready
        self._load_categories()

        recipient = transaction_data.get('recipient', '') or ''
        purpose = transaction_data.get('purpose', '') or ''

        # Combine text for pattern matching (case-insensitive)
        search_text = f"{recipient} {purpose}".lower()

        # Iterate precompiled patterns (already prioritized by length)
        for regex, category_id, pattern in self._compiled_patterns:
            if regex.search(search_text):
                return category_id
        
        return None
    
    def match_bulk(self, transactions: List[Dict[str, Any]]) -> List[Optional[int]]:
        """
        Match multiple transactions to categories
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of category IDs (None for unmatched)
        """
        # Bulk match using precompiled patterns for efficiency
        # Prepare compiled list if not present
        self._load_categories()

        results: List[Optional[int]] = []
        for t in transactions:
            recipient = t.get('recipient', '') or ''
            purpose = t.get('purpose', '') or ''
            search_text = f"{recipient} {purpose}".lower()
            matched: Optional[int] = None
            for regex, category_id, _ in self._compiled_patterns:
                if regex.search(search_text):
                    matched = category_id
                    break
            results.append(matched)

        return results
    
    def clear_cache(self):
        """
        Clear the categories cache (call after category updates)
        """
        self._categories_cache = None
        self._compiled_patterns = []
