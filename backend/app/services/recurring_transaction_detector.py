"""
Recurring Transaction Detector - Automatische Erkennung wiederkehrender Transaktionen
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from collections import defaultdict
import statistics

from app.models.data_row import DataRow
from app.models.recurring_transaction import RecurringTransaction, RecurringTransactionLink


class RecurringTransactionDetector:
    """
    Service zur Erkennung wiederkehrender Transaktionen (Verträge)
    
    Algorithmus:
    - Gleicher Empfänger
    - Ähnlicher Betrag (±2€ Toleranz)
    - Regelmäßige Abstände (28-31 Tage Toleranz für monatlich)
    - Mindestens 3 Vorkommnisse
    - Smart Detection: Nur aktiv wenn kürzliche Transaktionen vorhanden
    """
    
    # Configuration
    MIN_OCCURRENCES = 3
    AMOUNT_TOLERANCE = 2.0  # ±2 EUR
    INTERVAL_TOLERANCE_DAYS = 3  # ±3 days around expected interval
    
    # Typical intervals to check (in days)
    INTERVALS = [
        30,   # Monthly (28-33 days)
        90,   # Quarterly (87-93 days)
        365,  # Yearly (362-368 days)
        7,    # Weekly (4-10 days)
        14,   # Bi-weekly (11-17 days)
    ]
    
    # Activity threshold: if last transaction is older than this, consider inactive
    ACTIVITY_THRESHOLD_DAYS = 60
    
    def __init__(self, db: Session):
        """
        Initialize detector with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def detect_recurring_for_account(self, account_id: int) -> List[RecurringTransaction]:
        """
        Detect all recurring transactions for a specific account
        
        Args:
            account_id: Account ID to analyze
            
        Returns:
            List of detected RecurringTransaction objects
        """
        # Get all transactions for account, ordered by date, up to today
        transactions = (
            self.db.query(DataRow)
            .filter(
                DataRow.account_id == account_id,
                DataRow.transaction_date <= date.today() # Only consider transactions up to today
            )
            .order_by(DataRow.transaction_date)
            .all()
        )
        
        if len(transactions) < self.MIN_OCCURRENCES:
            return []
        
        # Check if we have recent data (avoid false positives from old data)
        most_recent_date = max(t.transaction_date for t in transactions)
        today = date.today()
        
        # If data is older than 2 years, don't flag anything as active
        data_is_stale = (today - most_recent_date).days > 730
        
        # Group transactions by recipient
        recipient_groups = self._group_by_recipient(transactions)
        
        # Detect patterns for each recipient
        detected = []
        for recipient, tx_list in recipient_groups.items():
            if len(tx_list) < self.MIN_OCCURRENCES:
                continue
            
            patterns = self._detect_patterns_for_recipient(tx_list, account_id, data_is_stale)
            detected.extend(patterns)
        
        return detected
    
    def _group_by_recipient(self, transactions: List[DataRow]) -> Dict[str, List[DataRow]]:
        """
        Group transactions by recipient name
        
        Args:
            transactions: List of DataRow objects
            
        Returns:
            Dictionary mapping recipient -> list of transactions
        """
        groups = defaultdict(list)
        for tx in transactions:
            if tx.recipient:
                # Normalize recipient name (strip whitespace, lowercase)
                recipient_key = tx.recipient.strip().lower()
                groups[recipient_key].append(tx)
        return groups
    
    def _detect_patterns_for_recipient(
        self, 
        transactions: List[DataRow], 
        account_id: int,
        data_is_stale: bool
    ) -> List[RecurringTransaction]:
        """
        Detect recurring patterns for a specific recipient
        
        Args:
            transactions: List of transactions for same recipient
            account_id: Account ID
            data_is_stale: Whether the data is older than 2 years
            
        Returns:
            List of detected patterns (usually 0 or 1)
        """
        if len(transactions) < self.MIN_OCCURRENCES:
            return []
        
        # Group by similar amounts (±2€)
        amount_groups = self._group_by_similar_amount(transactions)
        
        detected_patterns = []
        
        for amount, tx_group in amount_groups.items():
            if len(tx_group) < self.MIN_OCCURRENCES:
                continue
            
            # Check for regular intervals
            pattern = self._check_interval_pattern(tx_group, account_id, data_is_stale)
            if pattern:
                detected_patterns.append(pattern)
        
        return detected_patterns
    
    def _group_by_similar_amount(self, transactions: List[DataRow]) -> Dict[float, List[DataRow]]:
        """
        Group transactions by similar amounts
        
        Args:
            transactions: List of transactions
            
        Returns:
            Dictionary mapping representative amount -> list of similar transactions
        """
        groups = defaultdict(list)
        processed = set()
        
        for i, tx in enumerate(transactions):
            if i in processed:
                continue
            
            amount = float(tx.amount)
            similar_group = [tx]
            processed.add(i)
            
            # Find other transactions with similar amounts
            for j, other_tx in enumerate(transactions):
                if j in processed:
                    continue
                
                other_amount = float(other_tx.amount)
                if abs(amount - other_amount) <= self.AMOUNT_TOLERANCE:
                    similar_group.append(other_tx)
                    processed.add(j)
            
            if len(similar_group) >= self.MIN_OCCURRENCES:
                # Use average amount as key
                avg_amount = sum(float(t.amount) for t in similar_group) / len(similar_group)
                groups[avg_amount] = similar_group
        
        return groups
    
    def _check_interval_pattern(
        self, 
        transactions: List[DataRow], 
        account_id: int,
        data_is_stale: bool
    ) -> Optional[RecurringTransaction]:
        """
        Check if transactions follow a regular interval pattern
        
        Args:
            transactions: List of transactions with similar amounts
            account_id: Account ID
            data_is_stale: Whether the data is older than 2 years
            
        Returns:
            RecurringTransaction object if pattern detected, None otherwise
        """
        if len(transactions) < self.MIN_OCCURRENCES:
            return None
        
        # Sort by date
        sorted_tx = sorted(transactions, key=lambda t: t.transaction_date)
        
        # Calculate intervals between consecutive transactions
        intervals = []
        for i in range(len(sorted_tx) - 1):
            delta = (sorted_tx[i + 1].transaction_date - sorted_tx[i].transaction_date).days
            intervals.append(delta)
        
        if not intervals:
            return None
        
        # Check for each typical interval pattern
        for expected_interval in self.INTERVALS:
            if self._matches_interval(intervals, expected_interval):
                return self._create_recurring_transaction(
                    sorted_tx, 
                    expected_interval, 
                    account_id,
                    data_is_stale
                )
        
        return None
    
    def _matches_interval(self, intervals: List[int], expected: int) -> bool:
        """
        Check if intervals match expected pattern (with tolerance)
        
        Args:
            intervals: List of day intervals between transactions
            expected: Expected interval in days
            
        Returns:
            True if intervals match pattern
        """
        if not intervals:
            return False
        
        # Check if most intervals are within tolerance
        matches = 0
        for interval in intervals:
            if abs(interval - expected) <= self.INTERVAL_TOLERANCE_DAYS:
                matches += 1
        
        # At least 70% of intervals should match
        match_ratio = matches / len(intervals)
        return match_ratio >= 0.7
    
    def _create_recurring_transaction(
        self, 
        transactions: List[DataRow], 
        interval: int, 
        account_id: int,
        data_is_stale: bool
    ) -> RecurringTransaction:
        """
        Create RecurringTransaction object from detected pattern
        
        Args:
            transactions: List of matching transactions
            interval: Detected interval in days
            account_id: Account ID
            data_is_stale: Whether the data is older than 2 years
            
        Returns:
            RecurringTransaction object (not yet persisted)
        """
        # Calculate statistics
        avg_amount = sum(float(t.amount) for t in transactions) / len(transactions)
        
        # Calculate actual average interval
        sorted_tx = sorted(transactions, key=lambda t: t.transaction_date)
        actual_intervals = [
            (sorted_tx[i + 1].transaction_date - sorted_tx[i].transaction_date).days
            for i in range(len(sorted_tx) - 1)
        ]
        avg_interval = int(statistics.mean(actual_intervals)) if actual_intervals else interval
        
        first_date = sorted_tx[0].transaction_date
        last_date = sorted_tx[-1].transaction_date
        
        # Calculate next expected date
        next_expected = last_date + timedelta(days=avg_interval)
        
        # Determine if active
        # Active if: last occurrence is recent AND (not stale data OR next expected is not far past)
        days_since_last = (date.today() - last_date).days
        is_active = days_since_last <= self.ACTIVITY_THRESHOLD_DAYS and not data_is_stale
        
        # If data is stale but last transaction was within the data period, still might be active
        if data_is_stale and days_since_last <= self.ACTIVITY_THRESHOLD_DAYS:
            # Data stopped being recorded, don't mark as inactive based on today's date
            is_active = True
        
        # Calculate confidence score based on consistency
        if actual_intervals:
            std_dev = statistics.stdev(actual_intervals) if len(actual_intervals) > 1 else 0
            # Higher consistency = higher confidence
            confidence = max(0.5, min(1.0, 1.0 - (std_dev / avg_interval)))
        else:
            confidence = 1.0
        
        # Get most common category_id
        category_ids = [t.category_id for t in transactions if t.category_id]
        category_id = max(set(category_ids), key=category_ids.count) if category_ids else None
        
        recurring = RecurringTransaction(
            account_id=account_id,
            recipient=sorted_tx[0].recipient,  # Use original case
            average_amount=round(avg_amount, 2),
            average_interval_days=avg_interval,
            first_occurrence=first_date,
            last_occurrence=last_date,
            occurrence_count=len(transactions),
            category_id=category_id,
            is_active=is_active,
            next_expected_date=next_expected,
            confidence_score=round(confidence, 2)
        )
        
        return recurring
    
    def update_recurring_transactions(self, account_id: int) -> Dict[str, int]:
        """
        Update recurring transactions for an account
        
        This method:
        1. Detects new patterns
        2. Updates existing patterns
        3. Removes patterns that no longer match
        4. Respects manual overrides
        
        Args:
            account_id: Account ID to update
            
        Returns:
            Dictionary with statistics (created, updated, deleted, skipped counts)
        """
        # Detect current patterns
        detected_patterns = self.detect_recurring_for_account(account_id)
        
        # Get all existing recurring transactions for the account
        all_existing = self.db.query(RecurringTransaction).filter(
            RecurringTransaction.account_id == account_id
        ).all()
        
        stats = {"created": 0, "updated": 0, "deleted": 0, "skipped": 0}
        
        # Create maps for matching
        existing_map = {(r.recipient.lower(), round(float(r.average_amount), 0)): r for r in all_existing}
        detected_map = {(p.recipient.lower(), round(float(p.average_amount), 0)): p for p in detected_patterns}
        
        # Process detected patterns
        for key, pattern in detected_map.items():
            existing_pattern = existing_map.get(key)
            
            if existing_pattern:
                if existing_pattern.is_manually_overridden:
                    stats["skipped"] += 1
                    continue  # Respect manual override
                
                # Update existing pattern
                existing_pattern.average_amount = pattern.average_amount
                existing_pattern.average_interval_days = pattern.average_interval_days
                existing_pattern.last_occurrence = pattern.last_occurrence
                existing_pattern.occurrence_count = pattern.occurrence_count
                existing_pattern.is_active = pattern.is_active
                existing_pattern.next_expected_date = pattern.next_expected_date
                existing_pattern.confidence_score = pattern.confidence_score
                existing_pattern.category_id = pattern.category_id
                
                self._link_transactions(existing_pattern)
                stats["updated"] += 1
            else:
                # Create new pattern
                self.db.add(pattern)
                self._link_transactions(pattern)
                stats["created"] += 1
        
        # Delete auto-detected patterns that are no longer found
        for key, existing_pattern in existing_map.items():
            if not existing_pattern.is_manually_overridden and key not in detected_map:
                self.db.delete(existing_pattern)
                stats["deleted"] += 1
        
        self.db.commit()
        
        return stats
    
    def _link_transactions(self, recurring: RecurringTransaction):
        """
        Link transactions to a recurring transaction
        
        Args:
            recurring: RecurringTransaction object (must be persisted with ID)
        """
        if not recurring.id:
            self.db.flush()  # Ensure ID is generated
        
        # Remove old links
        self.db.query(RecurringTransactionLink).filter(
            RecurringTransactionLink.recurring_transaction_id == recurring.id
        ).delete()
        
        # Find matching transactions
        matching_transactions = (
            self.db.query(DataRow)
            .filter(
                and_(
                    DataRow.account_id == recurring.account_id,
                    DataRow.recipient.ilike(recurring.recipient),
                    DataRow.amount.between(
                        float(recurring.average_amount) - self.AMOUNT_TOLERANCE,
                        float(recurring.average_amount) + self.AMOUNT_TOLERANCE
                    ),
                    DataRow.transaction_date >= recurring.first_occurrence,
                    DataRow.transaction_date <= recurring.last_occurrence
                )
            )
            .all()
        )
        
        # Create links
        for tx in matching_transactions:
            link = RecurringTransactionLink(
                recurring_transaction_id=recurring.id,
                data_row_id=tx.id
            )
            self.db.add(link)
    
    def toggle_manual_override(self, recurring_id: int, is_recurring: bool) -> RecurringTransaction:
        """
        Manually mark/unmark a transaction pattern as recurring
        
        Args:
            recurring_id: RecurringTransaction ID
            is_recurring: True to keep as recurring, False to remove
            
        Returns:
            Updated RecurringTransaction
        """
        recurring = self.db.query(RecurringTransaction).get(recurring_id)
        if not recurring:
            raise ValueError(f"RecurringTransaction {recurring_id} not found")
        
        recurring.is_manually_overridden = True
        recurring.is_active = is_recurring
        
        self.db.commit()
        return recurring
