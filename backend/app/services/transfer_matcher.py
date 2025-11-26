"""
Transfer Matcher Service - Auto-detects inter-account transfers
"""
from typing import List, Optional, Tuple
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models import DataRow, Transfer, Account
from app.utils import get_logger


# Module logger
logger = get_logger("app.services.transfer_matcher")


class TransferMatcher:
    """
    Service to automatically detect and match inter-account transfers.
    
    Matching criteria:
    - Same absolute amount (one negative, one positive)
    - Within ±5 days
    - Different accounts
    - Not already linked as transfers
    """
    
    DATE_TOLERANCE_DAYS = 5
    
    def __init__(self, db: Session):
        self.db = db
    
    def find_transfer_candidates(
        self,
        account_ids: Optional[List[int]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        min_confidence: float = 0.7,
        exclude_existing: bool = True
    ) -> List[dict]:
        """
        Find potential transfer pairs based on matching criteria.
        
        Args:
            account_ids: Optional list of account IDs to limit search
            date_from: Optional start date for search range
            date_to: Optional end date for search range
            min_confidence: Minimum confidence score (0.0 to 1.0)
            exclude_existing: Whether to exclude already-linked transfers
            
        Returns:
            List of transfer candidates with confidence scores
        """
        # Get all candidate transactions
        query = self.db.query(DataRow).filter(DataRow.amount != 0)
        
        if account_ids:
            query = query.filter(DataRow.account_id.in_(account_ids))
        
        if date_from:
            query = query.filter(DataRow.transaction_date >= date_from)
        
        if date_to:
            query = query.filter(DataRow.transaction_date <= date_to)
        
        # Exclude transactions that are already linked in transfers
        existing_ids = []
        if exclude_existing:
            existing_transfer_ids = self.db.query(Transfer.from_transaction_id).union(
                self.db.query(Transfer.to_transaction_id)
            ).all()
            # flatten
            existing_ids = [tid[0] for tid in existing_transfer_ids if tid and tid[0] is not None]

        candidates = []

        # Instead of loading all transactions into memory (O(n^2) when matching),
        # stream only negative transactions and for each one do a targeted query
        # for matching positive transactions within the date tolerance and amount.
        # This keeps memory usage low and leverages DB indexes for the inner lookup.

        negatives_q = query.filter(DataRow.amount < 0).order_by(DataRow.transaction_date)

        # Use yield_per so SQLAlchemy can stream results and not hydrate entire result set
        try:
            negatives_iter = negatives_q.yield_per(500)
        except Exception:
            # Some DBs/drivers may not support yield_per in the current context;
            # fall back to normal iteration (still better than loading positives as well)
            negatives_iter = negatives_q

        for tx1 in negatives_iter:
            # compute date window
            date_min = tx1.transaction_date - timedelta(days=self.DATE_TOLERANCE_DAYS)
            date_max = tx1.transaction_date + timedelta(days=self.DATE_TOLERANCE_DAYS)

            # find matching positive transactions with same absolute amount
            positives_q = (
                self.db.query(DataRow)
                .filter(
                    DataRow.amount == abs(tx1.amount),
                    DataRow.account_id != tx1.account_id,
                    DataRow.transaction_date >= date_min,
                    DataRow.transaction_date <= date_max,
                )
                .order_by(DataRow.transaction_date)
            )

            if exclude_existing and existing_ids:
                positives_q = positives_q.filter(~DataRow.id.in_(existing_ids))

            # Usually the number of candidates per tx1 is small; load them
            for tx2 in positives_q.all():
                date_diff = abs((tx2.transaction_date - tx1.transaction_date).days)
                # double-check tolerance
                if date_diff > self.DATE_TOLERANCE_DAYS:
                    continue

                confidence = self._calculate_confidence(tx1, tx2, date_diff)
                if confidence >= min_confidence:
                    candidates.append({
                        'from_transaction_id': tx1.id,
                        'to_transaction_id': tx2.id,
                        'from_transaction': self._serialize_transaction(tx1),
                        'to_transaction': self._serialize_transaction(tx2),
                        'amount': abs(tx1.amount),
                        'transfer_date': tx1.transaction_date,
                        'confidence_score': confidence,
                        'match_reason': self._generate_match_reason(tx1, tx2, date_diff, confidence)
                    })

        return candidates
    
    def _calculate_confidence(self, tx1: DataRow, tx2: DataRow, date_diff: int) -> float:
        """
        Calculate confidence score for a transfer match.
        
        Factors:
        - Date proximity (0-5 days): 0.5 to 1.0
        - Same day: +0.2 bonus
        - Purpose/recipient similarity: up to +0.15
        """
        # Base score from date proximity
        date_score = 1.0 - (date_diff / self.DATE_TOLERANCE_DAYS) * 0.5
        
        # Same day bonus
        same_day_bonus = 0.2 if date_diff == 0 else 0.0
        
        # Text similarity bonus
        text_similarity = self._calculate_text_similarity(tx1, tx2)
        text_bonus = text_similarity * 0.15
        
        confidence = min(1.0, date_score + same_day_bonus + text_bonus)
        return round(confidence, 2)
    
    def _calculate_text_similarity(self, tx1: DataRow, tx2: DataRow) -> float:
        """
        Calculate text similarity between two transactions based on purpose/recipient.
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Get text fields
        text1_parts = []
        if tx1.purpose:
            text1_parts.append(tx1.purpose.lower())
        if tx1.recipient:
            text1_parts.append(tx1.recipient.lower())
        text1 = ' '.join(text1_parts)
        
        text2_parts = []
        if tx2.purpose:
            text2_parts.append(tx2.purpose.lower())
        if tx2.recipient:
            text2_parts.append(tx2.recipient.lower())
        text2 = ' '.join(text2_parts)
        
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_match_reason(self, tx1: DataRow, tx2: DataRow, date_diff: int, confidence: float) -> str:
        """Generate human-readable explanation for the match."""
        reasons = []
        
        if date_diff == 0:
            reasons.append("same day")
        elif date_diff == 1:
            reasons.append("1 day apart")
        else:
            reasons.append(f"{date_diff} days apart")
        
        reasons.append(f"exact amount match ({abs(tx1.amount)})")
        
        text_sim = self._calculate_text_similarity(tx1, tx2)
        if text_sim > 0.3:
            reasons.append(f"similar descriptions ({int(text_sim * 100)}% match)")
        
        return "Match: " + ", ".join(reasons)
    
    def _serialize_transaction(self, tx: DataRow) -> dict:
        """Serialize a DataRow for the API response."""
        return {
            'id': tx.id,
            'account_id': tx.account_id,
            'transaction_date': tx.transaction_date.isoformat(),
            'amount': float(tx.amount),
            'recipient': tx.recipient,
            'purpose': tx.purpose,
            'category_id': tx.category_id
        }
    
    def create_transfer(
        self,
        from_transaction_id: int,
        to_transaction_id: int,
        is_auto_detected: bool = False,
        confidence_score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Transfer:
        """
        Create a new transfer link between two transactions.
        
        Args:
            from_transaction_id: Transaction with negative amount
            to_transaction_id: Transaction with positive amount
            is_auto_detected: Whether this was auto-detected
            confidence_score: Confidence score for auto-detection
            notes: Optional notes
            
        Returns:
            Created Transfer object
            
        Raises:
            ValueError: If transactions are invalid or already linked
        """
        # Validate transactions exist
        from_tx = self.db.query(DataRow).filter(DataRow.id == from_transaction_id).first()
        to_tx = self.db.query(DataRow).filter(DataRow.id == to_transaction_id).first()
        
        if not from_tx or not to_tx:
            raise ValueError("One or both transactions not found")
        
        # Validate different accounts
        if from_tx.account_id == to_tx.account_id:
            raise ValueError("Cannot create transfer between transactions in the same account")
        
        # Validate amounts
        if from_tx.amount >= 0 or to_tx.amount <= 0:
            raise ValueError("Invalid transfer: from_transaction must be negative, to_transaction must be positive")
        
        if abs(from_tx.amount) != to_tx.amount:
            raise ValueError("Transaction amounts must match (inverted)")
        
        # Check if already linked
        existing = self.db.query(Transfer).filter(
            or_(
                and_(Transfer.from_transaction_id == from_transaction_id, Transfer.to_transaction_id == to_transaction_id),
                and_(Transfer.from_transaction_id == to_transaction_id, Transfer.to_transaction_id == from_transaction_id)
            )
        ).first()
        
        if existing:
            raise ValueError("These transactions are already linked as a transfer")
        
        # Create transfer
        transfer = Transfer(
            from_transaction_id=from_transaction_id,
            to_transaction_id=to_transaction_id,
            amount=abs(from_tx.amount),
            transfer_date=from_tx.transaction_date,
            is_auto_detected=is_auto_detected,
            confidence_score=confidence_score,
            notes=notes
        )
        
        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)
        
        return transfer
    
    def auto_detect_and_create_transfers(
        self,
        account_ids: Optional[List[int]] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        min_confidence: float = 0.85
    ) -> Tuple[int, List[Transfer]]:
        """
        Auto-detect and create transfers for high-confidence matches.
        
        Args:
            account_ids: Optional list of account IDs to limit search
            date_from: Optional start date
            date_to: Optional end date
            min_confidence: Minimum confidence for auto-creation (default 0.85)
            
        Returns:
            Tuple of (number created, list of Transfer objects)
        """
        candidates = self.find_transfer_candidates(
            account_ids=account_ids,
            date_from=date_from,
            date_to=date_to,
            min_confidence=min_confidence,
            exclude_existing=True
        )
        
        created_transfers = []
        for candidate in candidates:
            try:
                transfer = self.create_transfer(
                    from_transaction_id=candidate['from_transaction_id'],
                    to_transaction_id=candidate['to_transaction_id'],
                    is_auto_detected=True,
                    confidence_score=candidate['confidence_score'],
                    notes=candidate['match_reason']
                )
                created_transfers.append(transfer)
                logger.info(
                    "Created transfer",
                    extra={
                        "transfer_id": getattr(transfer, 'id', None),
                        "from_transaction_id": candidate['from_transaction_id'],
                        "to_transaction_id": candidate['to_transaction_id'],
                        "confidence": candidate['confidence_score'],
                    },
                )
            except ValueError as e:
                # Skip if validation fails (e.g., already linked)
                logger.warning("Skipped candidate", extra={"reason": str(e)})
                continue
        
        return len(created_transfers), created_transfers
    
    def get_transfer_for_transaction(self, transaction_id: int) -> Optional[Transfer]:
        """
        Get the transfer that includes a specific transaction.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            Transfer object if found, None otherwise
        """
        return self.db.query(Transfer).filter(
            or_(
                Transfer.from_transaction_id == transaction_id,
                Transfer.to_transaction_id == transaction_id
            )
        ).first()
    
    def is_transfer_transaction(self, transaction_id: int) -> bool:
        """
        Check if a transaction is part of a transfer.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            True if transaction is part of a transfer
        """
        return self.get_transfer_for_transaction(transaction_id) is not None
