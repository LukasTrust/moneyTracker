"""
Tests for the main FastAPI application file.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import runpy

from app.main import app, init_default_categories, lifespan
from app.database import Base
from app.models.category import Category

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture to create a new database session for each test.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client():
    """
    Fixture to create a test client for the FastAPI application.
    """
    with patch("app.main.lifespan", return_value=AsyncMock()):
        with TestClient(app) as c:
            yield c

def test_root_endpoint(client):
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "Money Tracker API"
    assert "version" in json_response
    assert json_response["status"] == "running"

def test_health_check_endpoint(client):
    """
    Test the health check endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["database"] == "connected"

def test_init_default_categories_empty_db(db_session):
    """
    Test that default categories are created if the database is empty.
    """
    # Ensure the database is empty
    assert db_session.query(Category).count() == 0

    # Call the function to initialize default categories
    with patch("app.main.SessionLocal", return_value=db_session):
        init_default_categories()

    # Check that the default categories have been created
    assert db_session.query(Category).count() > 0
    
    # Verify a few default categories
    rewe_category = db_session.query(Category).filter(Category.name == "Lebensmittel").first()
    assert rewe_category is not None
    assert "REWE" in rewe_category.mappings["patterns"]

def test_init_default_categories_not_empty_db(db_session):
    """
    Test that default categories are not created if categories already exist.
    """
    # Add a category to the database
    existing_category = Category(name="Test Category", color="#ffffff", icon="🧪")
    db_session.add(existing_category)
    db_session.commit()

    assert db_session.query(Category).count() == 1

    # Call the function to initialize default categories
    with patch("app.main.SessionLocal", return_value=db_session):
        init_default_categories()

    # Check that no new categories have been created
    assert db_session.query(Category).count() == 1

@patch("app.main.get_logger")
def test_init_default_categories_exception(mock_get_logger, db_session):
    """
    Test that an exception during category creation is handled correctly.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.add.side_effect = Exception("Test Exception")
        mock_session_local.return_value = mock_db

        init_default_categories()

        mock_logger.exception.assert_called_with("Error creating default categories")
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

@pytest.mark.asyncio
async def test_lifespan():
    """
    Test the lifespan context manager.
    """
    with patch("app.main.Base.metadata.create_all") as mock_create_all, \
         patch("app.main.init_default_categories") as mock_init_default_categories, \
         patch("app.main.get_logger") as mock_get_logger:
        
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        async with lifespan(app):
            mock_create_all.assert_called_once()
            mock_init_default_categories.assert_called_once()
            mock_logger.info.assert_any_call("Database tables ensured/created")
            mock_logger.info.assert_any_call("Default categories initialization complete")

        mock_logger.info.assert_any_call("Shutting down application")

@patch("uvicorn.run")
def test_main_entrypoint(mock_uvicorn_run):
    """
    Test the main entrypoint.
    """
    with patch.dict("sys.modules", {"__main__": MagicMock(__name__="__main__")}):
        runpy.run_module("app.main", run_name="__main__")
        mock_uvicorn_run.assert_called_once()
