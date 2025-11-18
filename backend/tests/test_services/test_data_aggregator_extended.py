"""
Extended tests for the DataAggregator service to ensure full coverage.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
from decimal import Decimal

from app.database import Base
from app.services.data_aggregator import DataAggregator
from app.models.account import Account
from app.models.data_row import DataRow
from app.models.category import Category
from app.models.transfer import Transfer

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Create a new database session for each test function.
    This fixture creates the tables, yields a session, and then drops the tables.
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
    Populate the database with a variety of test data.
    """
    # Create an account
    account = Account(id=1, name="Test Account", currency="EUR")
    db_session.add(account)
    db_session.commit()

    # Create categories
    cat1 = Category(id=1, name="Groceries", color="#ff0000")
    cat2 = Category(id=2, name="Salary", color="#00ff00")
    cat3 = Category(id=3, name="Rent", color="#0000ff")
    db_session.add_all([cat1, cat2, cat3])
    db_session.commit()

    # Create transactions
    transactions = [
        # Expenses
        DataRow(id=1, account_id=1, row_hash="1", transaction_date=date(2024, 1, 5), amount=Decimal("-50.00"), recipient="Supermarket", purpose="Weekly shopping", category_id=1),
        DataRow(id=2, account_id=1, row_hash="2", transaction_date=date(2024, 1, 10), amount=Decimal("-12.50"), recipient="Bakery", purpose="Bread and cakes", category_id=1),
        DataRow(id=3, account_id=1, row_hash="3", transaction_date=date(2024, 1, 1), amount=Decimal("-800.00"), recipient="Landlord", purpose="January Rent", category_id=3),
        
        # Income
        DataRow(id=4, account_id=1, row_hash="4", transaction_date=date(2024, 1, 15), amount=Decimal("2500.00"), recipient="Employer", purpose="January Salary", category_id=2),
        
        # Transaction for another month
        DataRow(id=5, account_id=1, row_hash="5", transaction_date=date(2024, 2, 5), amount=Decimal("-60.00"), recipient="Supermarket", purpose="More shopping", category_id=1),

        # Uncategorized transaction
        DataRow(id=6, account_id=1, row_hash="6", transaction_date=date(2024, 2, 10), amount=Decimal("-25.00"), recipient="Unknown Vendor", purpose="Misc"),

        # Transfer transactions
        DataRow(id=7, account_id=1, row_hash="7", transaction_date=date(2024, 1, 20), amount=Decimal("-100.00"), recipient="Transfer Out", purpose="Savings"),
        DataRow(id=8, account_id=1, row_hash="8", transaction_date=date(2024, 1, 20), amount=Decimal("100.00"), recipient="Transfer In", purpose="Savings"),
    ]
    db_session.add_all(transactions)
    db_session.commit()

    # Create a transfer
    transfer = Transfer(id=1, from_transaction_id=7, to_transaction_id=8, amount=Decimal("100.00"), transfer_date=date(2024, 1, 20))
    db_session.add(transfer)
    db_session.commit()

    return db_session

def test_get_transfer_transaction_ids(populated_db):
    """Test that transfer transaction IDs are correctly retrieved."""
    aggregator = DataAggregator(populated_db)
    transfer_ids = aggregator._get_transfer_transaction_ids()
    assert transfer_ids == {7, 8}

def test_get_summary_no_filters(populated_db):
    """Test the summary function with no filters."""
    aggregator = DataAggregator(populated_db)
    summary = aggregator.get_summary()
    
    # Expenses: -50.00, -12.50, -800.00, -60.00, -25.00 = -947.50
    # Income: 2500.00
    # Transfers (-100, +100) are excluded
    assert summary['total_income'] == 2500.00
    assert summary['total_expenses'] == -947.50
    assert summary['net_balance'] == 1552.50
    assert summary['transaction_count'] == 6 # 8 total - 2 transfers

def test_get_summary_with_date_filters(populated_db):
    """Test the summary function with date filters."""
    aggregator = DataAggregator(populated_db)
    summary = aggregator.get_summary(from_date=date(2024, 1, 1), to_date=date(2024, 1, 31))

    # Jan Expenses: -50.00, -12.50, -800.00 = -862.50
    # Jan Income: 2500.00
    assert summary['total_income'] == 2500.00
    assert summary['total_expenses'] == -862.50
    assert summary['net_balance'] == 1637.50
    assert summary['transaction_count'] == 4

def test_get_category_aggregation(populated_db):
    """Test category aggregation."""
    aggregator = DataAggregator(populated_db)
    cat_agg = aggregator.get_category_aggregation()

    assert len(cat_agg) > 0
    # Salary is the largest absolute amount
    assert cat_agg[0]['category_name'] == "Salary"
    assert cat_agg[0]['total_amount'] == 2500.00

def test_get_recipient_aggregation(populated_db):
    """Test recipient aggregation."""
    aggregator = DataAggregator(populated_db)
    rec_agg = aggregator.get_recipient_aggregation(transaction_type='expense')

    assert len(rec_agg) > 0
    # Landlord is the largest recipient of expenses
    assert rec_agg[0]['recipient'] == "Landlord"
    assert rec_agg[0]['total_amount'] == -800.00

def test_get_balance_history_monthly(populated_db):
    """Test monthly balance history."""
    aggregator = DataAggregator(populated_db)
    history = aggregator.get_balance_history(group_by='month')

    assert len(history['labels']) == 2
    assert history['labels'] == ['Jan 2024', 'Feb 2024']
    
    # Jan: 2500.00 - 862.50 = 1637.50
    assert history['income'][0] == 2500.00
    assert history['expenses'][0] == -862.50
    assert history['balance'][0] == 1637.50

    # Feb: -60.00 - 25.00 = -85.00. Cumulative balance: 1637.50 - 85.00 = 1552.50
    assert history['income'][1] == 0
    assert history['expenses'][1] == -85.00
    assert history['balance'][1] == 1552.50

def test_format_period_label():
    """Test the period label formatting utility."""
    # Full year
    assert DataAggregator._format_period_label(date(2024, 1, 1), date(2024, 12, 31)) == "2024"
    # Single month
    assert DataAggregator._format_period_label(date(2024, 12, 1), date(2024, 12, 31)) == "December 2024"
    # Date range
    assert DataAggregator._format_period_label(date(2024, 1, 15), date(2024, 2, 15)) == "15.01.2024 - 15.02.2024"

def test_get_period_comparison(populated_db):
    """Test the period comparison function."""
    aggregator = DataAggregator(populated_db)
    comparison = aggregator.get_period_comparison(
        account_id=1,
        period1_start=date(2024, 1, 1),
        period1_end=date(2024, 1, 31),
        period2_start=date(2024, 2, 1),
        period2_end=date(2024, 2, 29),
    )

    # Period 1 (Jan)
    assert comparison['period1']['total_income'] == 2500.00
    assert comparison['period1']['total_expenses'] == -862.50

    # Period 2 (Feb)
    assert comparison['period2']['total_income'] == 0.00
    assert comparison['period2']['total_expenses'] == -85.00

    # Comparison
    assert comparison['comparison']['income_diff'] == -2500.00
    assert comparison['comparison']['expenses_diff'] == 777.50 # -85.00 - (-862.50)
