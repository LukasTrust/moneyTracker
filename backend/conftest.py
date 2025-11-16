"""
Global pytest configuration and fixtures
"""
import pytest
import os
import tempfile
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.account import Account
from app.models.category import Category
from app.models.mapping import Mapping
from app.models.data_row import DataRow


# Test database URL - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create a test database engine
    Uses in-memory SQLite with StaticPool to share connection across threads
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a test database session
    
    This fixture creates a new session for each test and rolls back
    all changes after the test completes.
    """
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with test database
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_account(db_session: Session) -> Account:
    """
    Create a sample account for testing
    """
    account = Account(
        name="Test Girokonto",
        bank_name="Test Bank",
        account_number="DE89370400440532013000",
        description="Test account for unit tests"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def sample_category(db_session: Session) -> Category:
    """
    Create a sample category for testing
    """
    category = Category(
        name="Lebensmittel",
        color="#10b981",
        icon="🛒",
        mappings={
            "recipients": ["REWE", "EDEKA", "ALDI"],
            "purposes": ["Einkauf", "Lebensmittel"]
        }
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def multiple_categories(db_session: Session) -> list[Category]:
    """
    Create multiple categories for testing
    """
    categories = [
        Category(
            name="Lebensmittel",
            color="#10b981",
            icon="🛒",
            mappings={
                "recipients": ["REWE", "EDEKA", "ALDI"],
                "purposes": ["Einkauf", "Lebensmittel"]
            }
        ),
        Category(
            name="Transport",
            color="#3b82f6",
            icon="🚗",
            mappings={
                "recipients": ["SHELL", "ARAL", "DB"],
                "purposes": ["Tankstelle", "Bahn"]
            }
        ),
        Category(
            name="Gehalt",
            color="#22c55e",
            icon="💰",
            mappings={
                "recipients": ["Firma AG"],
                "purposes": ["Gehalt", "Lohn"]
            }
        ),
        Category(
            name="Miete",
            color="#ef4444",
            icon="🏠",
            mappings={
                "recipients": ["Hausverwaltung"],
                "purposes": ["Miete"]
            }
        ),
    ]
    
    for category in categories:
        db_session.add(category)
    
    db_session.commit()
    
    for category in categories:
        db_session.refresh(category)
    
    return categories


@pytest.fixture
def sample_data_rows(db_session: Session, sample_account: Account, sample_category: Category) -> list[DataRow]:
    """
    Create sample data rows for testing
    """
    from datetime import datetime, timedelta
    
    base_date = datetime(2024, 1, 1)
    
    data_rows = [
        DataRow(
            account_id=sample_account.id,
            data={
                "date": base_date.strftime("%Y-%m-%d"),
                "recipient": "REWE Supermarkt",
                "purpose": "Lebensmittel",
                "amount": "-45.50",
                "currency": "EUR"
            },
            category_id=sample_category.id,
            row_hash="hash1"
        ),
        DataRow(
            account_id=sample_account.id,
            data={
                "date": (base_date + timedelta(days=1)).strftime("%Y-%m-%d"),
                "recipient": "EDEKA",
                "purpose": "Einkauf",
                "amount": "-32.20",
                "currency": "EUR"
            },
            category_id=sample_category.id,
            row_hash="hash2"
        ),
        DataRow(
            account_id=sample_account.id,
            data={
                "date": (base_date + timedelta(days=2)).strftime("%Y-%m-%d"),
                "recipient": "Firma AG",
                "purpose": "Gehalt Januar",
                "amount": "2500.00",
                "currency": "EUR"
            },
            category_id=None,
            row_hash="hash3"
        ),
    ]
    
    for row in data_rows:
        db_session.add(row)
    
    db_session.commit()
    
    for row in data_rows:
        db_session.refresh(row)
    
    return data_rows


@pytest.fixture
def temp_csv_file():
    """
    Create a temporary CSV file for testing
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        f.write("Buchungstag;Wertstellung;Empfänger/Auftraggeber;Verwendungszweck;Betrag\n")
        f.write("01.01.2024;01.01.2024;REWE;Lebensmittel;-45,50\n")
        f.write("02.01.2024;02.01.2024;EDEKA;Einkauf;-32,20\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def sample_csv_content() -> bytes:
    """
    Get sample CSV content as bytes
    """
    csv_content = """Buchungstag;Wertstellung;Empfänger/Auftraggeber;Verwendungszweck;Betrag
01.01.2024;01.01.2024;REWE Supermarkt;Lebensmittel;-45,50
02.01.2024;02.01.2024;EDEKA Markt;Wocheneinkauf;-32,20
03.01.2024;03.01.2024;Firma AG;Gehalt Januar;2500,00
"""
    return csv_content.encode('utf-8')


@pytest.fixture
def invalid_csv_content() -> bytes:
    """
    Get invalid CSV content for error testing
    """
    return b"This is not a valid CSV file!\nJust random text..."
