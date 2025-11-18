import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from app.database import Base
from app.services.recurring_transaction_detector import RecurringTransactionDetector
from app.models.account import Account
from app.models.data_row import DataRow
from app.models.recurring_transaction import RecurringTransaction

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for each test function.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def populated_db(db_session):
    """
    Populate the database with test data for recurring transactions.
    """
    account = Account(id=1, name="Test Account", currency="EUR")
    db_session.add(account)
    db_session.commit()

    # Mock date.today() for consistent testing of is_active
    with patch('app.services.recurring_transaction_detector.date', wraps=date) as mock_date:
        mock_date.today.return_value = date(2024, 6, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw) # Allow date() constructor
        
        # Temporarily adjust ACTIVITY_THRESHOLD_DAYS for testing
        original_activity_threshold = RecurringTransactionDetector.ACTIVITY_THRESHOLD_DAYS
        RecurringTransactionDetector.ACTIVITY_THRESHOLD_DAYS = 60 # Ensure recent transactions are active

        # 1. Clear monthly recurring transaction (Netflix)
        for i in range(5):
            db_session.add(DataRow(account_id=1, row_hash=f"netflix_{i}", transaction_date=date(2024, i + 1, 15), amount=Decimal("-9.99"), recipient="Netflix", purpose="Streaming"))

            # 2. Quarterly recurring transaction with slight variations
            # Dates: 2023-07-05, 2023-10-05, 2024-01-05, 2024-04-05
            db_session.add(DataRow(account_id=1, row_hash="insurance_0", transaction_date=date(2023, 7, 5), amount=Decimal("-150.50"), recipient="Insurance Corp", purpose="Policy ABC"))
            db_session.add(DataRow(account_id=1, row_hash="insurance_1", transaction_date=date(2023, 10, 5), amount=Decimal("-149.50"), recipient="Insurance Corp", purpose="Policy ABC"))
            db_session.add(DataRow(account_id=1, row_hash="insurance_2", transaction_date=date(2024, 1, 5), amount=Decimal("-148.50"), recipient="Insurance Corp", purpose="Policy ABC"))
            db_session.add(DataRow(account_id=1, row_hash="insurance_3", transaction_date=date(2024, 4, 5), amount=Decimal("-147.50"), recipient="Insurance Corp", purpose="Policy ABC"))
        
            # 3. Inactive recurring transaction (Gym) - last transaction is 2022-06-01, which is > 60 days from 2024-06-01
            for i in range(6):
                db_session.add(DataRow(account_id=1, row_hash=f"gym_{i}", transaction_date=date(2022, i + 1, 1), amount=Decimal("-25.00"), recipient="Old Gym", purpose="Membership"))
        
            # 4. Non-recurring transactions
            db_session.add(DataRow(account_id=1, row_hash="coffee_1", transaction_date=date(2024, 5, 1), amount=Decimal("-3.50"), recipient="Coffee Shop", purpose="Coffee"))
            db_session.add(DataRow(account_id=1, row_hash="book_1", transaction_date=date(2024, 5, 2), amount=Decimal("-15.00"), recipient="Bookstore", purpose="New Book"))
        
            db_session.commit()
            yield db_session
            
            # Restore original ACTIVITY_THRESHOLD_DAYS
            RecurringTransactionDetector.ACTIVITY_THRESHOLD_DAYS = original_activity_threshold
        
        def test_detect_monthly_recurring_transaction(populated_db):
            """Test detection of a clear monthly recurring transaction."""
            detector = RecurringTransactionDetector(populated_db)
            detected = detector.detect_recurring_for_account(account_id=1)
        
            netflix_pattern = next((p for p in detected if p.recipient == "Netflix"), None)
            assert netflix_pattern is not None
            assert netflix_pattern.is_active is True
            assert netflix_pattern.occurrence_count == 5
            assert abs(netflix_pattern.average_amount + 9.99) < 0.01
            assert 28 <= netflix_pattern.average_interval_days <= 31
        
        def test_detect_quarterly_recurring_transaction(populated_db):
            """Test detection of a quarterly transaction with variations."""
            detector = RecurringTransactionDetector(populated_db)
            detected = detector.detect_recurring_for_account(account_id=1)
        
            insurance_pattern = next((p for p in detected if p.recipient == "Insurance Corp"), None)
            assert insurance_pattern is not None
            assert insurance_pattern.is_active is True
            assert insurance_pattern.occurrence_count == 4
            assert 88 <= insurance_pattern.average_interval_days <= 93
        
        def test_detect_inactive_recurring_transaction(populated_db):
            """Test that old recurring transactions are marked as inactive."""
            detector = RecurringTransactionDetector(populated_db)
            detected = detector.detect_recurring_for_account(account_id=1)
        
            gym_pattern = next((p for p in detected if p.recipient == "Old Gym"), None)
            assert gym_pattern is not None
            assert gym_pattern.is_active is False
            assert gym_pattern.occurrence_count == 6
        
        def test_no_detection_for_non_recurring(populated_db):
            """Test that no recurring patterns are detected for random transactions."""
            detector = RecurringTransactionDetector(populated_db)
            
            transactions = populated_db.query(DataRow).filter(DataRow.recipient.in_(['Coffee Shop', 'Bookstore'])).all()
            
            # Manually check a subset of transactions that should not form a pattern
            patterns = detector._detect_patterns_for_recipient(transactions, account_id=1, data_is_stale=False)
            assert len(patterns) == 0
        
        def test_update_recurring_transactions(populated_db):
            """Test the update mechanism for recurring transactions."""
            detector = RecurringTransactionDetector(populated_db)
            
            # Initial detection
            stats = detector.update_recurring_transactions(account_id=1)
            assert stats['created'] > 0
            assert stats['updated'] == 0
            assert stats['deleted'] == 0
        
            # Add a new Netflix transaction
            populated_db.add(DataRow(account_id=1, row_hash="netflix_5", transaction_date=date(2024, 5, 15), amount=Decimal("-9.99"), recipient="Netflix", purpose="Streaming"))
            populated_db.commit()
        
            # Re-run detection
            stats = detector.update_recurring_transactions(account_id=1)
            assert stats['created'] == 0
            assert stats['updated'] > 0 # Netflix pattern should be updated
            assert stats['deleted'] == 0
        
            # Check if the Netflix pattern was updated
            netflix_pattern = populated_db.query(RecurringTransaction).filter(RecurringTransaction.recipient == "Netflix").one()
            assert netflix_pattern.occurrence_count == 6
        
        def test_manual_override(populated_db):
            """Test that manual overrides are respected."""
            detector = RecurringTransactionDetector(populated_db)
            detector.update_recurring_transactions(account_id=1)
            
            # Manually mark Netflix as not recurring
            netflix_pattern = populated_db.query(RecurringTransaction).filter(RecurringTransaction.recipient == "Netflix").one()
            detector.toggle_manual_override(netflix_pattern.id, is_recurring=False)
        
            # Re-run detection
            stats = detector.update_recurring_transactions(account_id=1)
            
            # The manually overridden pattern should be skipped
            assert stats['skipped'] == 1
            
            # Verify that the pattern is still in the DB but inactive
            netflix_pattern = populated_db.query(RecurringTransaction).filter(RecurringTransaction.recipient == "Netflix").one()
            assert netflix_pattern.is_active is False
            assert netflix_pattern.is_manually_overridden is True
