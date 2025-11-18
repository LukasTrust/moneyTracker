"""
Tests for app/database.py
"""
import pytest
import contextlib
from app.database import get_db, engine, Base


def test_database_engine_created():
    """Test that database engine is created"""
    assert engine is not None


def test_base_class_created():
    """Test that Base class is created"""
    assert Base is not None
    assert hasattr(Base, 'metadata')


def test_get_db_yields_session():
    """Test that get_db yields a database session and closes it"""
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    # Check that it's a session
    assert hasattr(db, 'close')
    assert hasattr(db, 'commit')
    # Exhaust the generator to trigger finally
    try:
        next(db_gen)
    except StopIteration:
        pass


def test_get_db_context_manager():
    """Test get_db as context manager"""
    # Use contextlib.closing to ensure the generator is closed and finally is called
    with contextlib.closing(get_db()) as db_gen:
        db = next(db_gen)
        assert db is not None
        # The finally block should be executed when the generator is closed