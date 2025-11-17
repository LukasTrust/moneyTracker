"""
Recipient Matcher Service

Handles recipient normalization, deduplication, and matching.
Uses fuzzy matching to detect similar recipients.
"""
from sqlalchemy.orm import Session
from app.models.recipient import Recipient
from difflib import SequenceMatcher
from typing import Optional, List, Tuple
from app.utils import get_logger


# Module logger
logger = get_logger("app.services.recipient_matcher")


class RecipientMatcher:
    """
    Service for matching and normalizing recipients
    
    Features:
    - Name normalization
    - Fuzzy matching for similar names
    - Automatic alias detection
    - Deduplication
    """
    
    # Similarity threshold for fuzzy matching (0.0 - 1.0)
    SIMILARITY_THRESHOLD = 0.85
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_or_create_recipient(self, name: str) -> Optional[Recipient]:
        """
        Find existing recipient or create new one
        
        Args:
            name: Recipient/sender name from transaction
            
        Returns:
            Recipient object or None if name is empty
        """
        if not name or not name.strip():
            return None
        
        # Normalize name
        normalized = Recipient.normalize_name(name)
        
        # Try exact match on normalized_name
        recipient = self.db.query(Recipient).filter(
            Recipient.normalized_name == normalized
        ).first()
        
        if recipient:
            logger.debug("Found exact recipient match: %s (id=%s)", recipient.name, getattr(recipient, 'id', None))
            return recipient
        
        # Try fuzzy matching
        similar_recipient = self._find_similar_recipient(normalized)
        if similar_recipient:
            # Add as alias and return existing recipient
            similar_recipient.add_alias(normalized)
            similar_recipient.transaction_count += 1
            self.db.commit()
            logger.info("Found similar recipient and added alias: %s -> existing id=%s", normalized, getattr(similar_recipient, 'id', None))
            return similar_recipient
        
        # Create new recipient
        new_recipient = Recipient(
            name=name.strip(),
            normalized_name=normalized,
            transaction_count=1
        )
        self.db.add(new_recipient)
        self.db.commit()
        self.db.refresh(new_recipient)
        logger.info("Created new recipient: %s (id=%s)", new_recipient.name, getattr(new_recipient, 'id', None))
        return new_recipient
    
    def _find_similar_recipient(self, normalized_name: str) -> Optional[Recipient]:
        """
        Find similar recipient using fuzzy matching
        
        Args:
            normalized_name: Normalized name to search for
            
        Returns:
            Similar recipient or None
        """
        # Get all recipients (could be optimized with database fuzzy search)
        all_recipients = self.db.query(Recipient).all()
        
        best_match = None
        best_score = 0.0
        
        for recipient in all_recipients:
            # Check similarity with normalized_name
            score = self._calculate_similarity(normalized_name, recipient.normalized_name)
            
            if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                best_score = score
                best_match = recipient
            
            # Also check aliases
            if recipient.aliases:
                aliases = [a.strip() for a in recipient.aliases.split(',')]
                for alias in aliases:
                    score = self._calculate_similarity(normalized_name, alias)
                    if score > best_score and score >= self.SIMILARITY_THRESHOLD:
                        best_score = score
                        best_match = recipient
        
        return best_match
    
    @staticmethod
    def _calculate_similarity(str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings (0.0 - 1.0)
        
        Uses SequenceMatcher for Levenshtein-like similarity
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score (0.0 = different, 1.0 = identical)
        """
        return SequenceMatcher(None, str1, str2).ratio()
    
    def merge_recipients(self, keep_id: int, merge_id: int) -> bool:
        """
        Merge two recipients (manual deduplication)
        
        Args:
            keep_id: ID of recipient to keep
            merge_id: ID of recipient to merge into keep_id
            
        Returns:
            True if successful, False otherwise
        """
        keep = self.db.query(Recipient).filter(Recipient.id == keep_id).first()
        merge = self.db.query(Recipient).filter(Recipient.id == merge_id).first()
        
        if not keep or not merge or keep.id == merge.id:
            return False
        
        # Add merged recipient's name as alias
        keep.add_alias(merge.name)
        if merge.aliases:
            for alias in merge.aliases.split(','):
                if alias.strip():
                    keep.add_alias(alias.strip())
        
        # Update all data_rows to point to kept recipient
        from app.models.data_row import DataRow
        self.db.query(DataRow).filter(
            DataRow.recipient_id == merge_id
        ).update({"recipient_id": keep_id})
        
        # Update transaction count
        keep.transaction_count += merge.transaction_count
        
        # Delete merged recipient
        self.db.delete(merge)
        self.db.commit()
        
        return True
    
    def get_recipient_suggestions(self, name: str, limit: int = 5) -> List[Tuple[Recipient, float]]:
        """
        Get similar recipient suggestions for manual matching
        
        Args:
            name: Name to search for
            limit: Maximum number of suggestions
            
        Returns:
            List of (Recipient, similarity_score) tuples
        """
        normalized = Recipient.normalize_name(name)
        all_recipients = self.db.query(Recipient).all()
        
        suggestions = []
        for recipient in all_recipients:
            score = self._calculate_similarity(normalized, recipient.normalized_name)
            if score > 0.5:  # Lower threshold for suggestions
                suggestions.append((recipient, score))
        
        # Sort by score descending
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions[:limit]
    
    def update_transaction_count(self, recipient_id: int):
        """
        Recalculate transaction count for a recipient
        
        Args:
            recipient_id: Recipient ID
        """
        recipient = self.db.query(Recipient).filter(Recipient.id == recipient_id).first()
        if recipient:
            from app.models.data_row import DataRow
            count = self.db.query(DataRow).filter(
                DataRow.recipient_id == recipient_id
            ).count()
            recipient.transaction_count = count
            self.db.commit()
