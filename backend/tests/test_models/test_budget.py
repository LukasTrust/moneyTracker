"""
Tests for Budget Model
"""
import pytest


def test_budget_model_exists():
    """Test that Budget model can be imported"""
    from app.models.budget import Budget
    
    assert Budget is not None
    assert hasattr(Budget, '__tablename__')


def test_budget_tablename():
    """Test that Budget has correct table name"""
    from app.models.budget import Budget
    
    assert Budget.__tablename__ == "budgets"


def test_budget_has_required_columns():
    """Test that Budget has all required columns"""
    from app.models.budget import Budget
    
    assert hasattr(Budget, 'id')
    assert hasattr(Budget, 'category_id')
    assert hasattr(Budget, 'amount')
    assert hasattr(Budget, 'start_date')
    assert hasattr(Budget, 'end_date')
    assert hasattr(Budget, 'created_at')
    assert hasattr(Budget, 'updated_at')


def test_budget_has_category_relationship():
    """Test that Budget has relationship to Category"""
    from app.models.budget import Budget
    
    assert hasattr(Budget, 'category')


def test_budget_amount_is_numeric():
    """Test that budget amount is numeric column"""
    from app.models.budget import Budget
    from sqlalchemy import Numeric
    
    amount_col = Budget.__table__.columns['amount']
    assert isinstance(amount_col.type, Numeric)
