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


def test_budget_is_active_within_range():
    """Test is_active returns True when check_date is within start and end date"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    # Create mock budget
    from types import SimpleNamespace
    budget = SimpleNamespace(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    # Bind the method
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    # Call the method
    result = budget.is_active(date(2023, 6, 15))
    assert result is True


def test_budget_is_active_before_start():
    """Test is_active returns False when check_date is before start_date"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    from types import SimpleNamespace
    budget = SimpleNamespace(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    result = budget.is_active(date(2022, 12, 31))
    assert result is False


def test_budget_is_active_after_end():
    """Test is_active returns False when check_date is after end_date"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    from types import SimpleNamespace
    budget = SimpleNamespace(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    result = budget.is_active(date(2024, 1, 1))
    assert result is False


def test_budget_is_active_on_start_date():
    """Test is_active returns True on start_date"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    from types import SimpleNamespace
    budget = SimpleNamespace(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    result = budget.is_active(date(2023, 1, 1))
    assert result is True


def test_budget_is_active_on_end_date():
    """Test is_active returns True on end_date"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    from types import SimpleNamespace
    budget = SimpleNamespace(
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
    
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    result = budget.is_active(date(2023, 12, 31))
    assert result is True


def test_budget_is_active_default_today():
    """Test is_active uses today's date when check_date is None"""
    from app.models.budget import Budget
    from datetime import date
    import types
    
    from types import SimpleNamespace
    today = date.today()
    budget = SimpleNamespace(
        start_date=today,
        end_date=today
    )
    
    budget.is_active = types.MethodType(Budget.is_active, budget)
    
    result = budget.is_active()
    assert result is True


def test_budget_repr():
    """Test __repr__ method"""
    from app.models.budget import Budget
    from types import SimpleNamespace
    from datetime import date
    
    # Create mock budget
    budget = SimpleNamespace(
        id=1,
        category_id=5,
        period="monthly",
        amount=500.00,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31)
    )
    # Bind the __repr__ method to the mock object
    budget.__repr__ = Budget.__repr__.__get__(budget, Budget)
    
    # Test __repr__
    expected = (
        "<Budget(id=1, category_id=5, "
        "period='monthly', amount=500.0, "
        "start_date=2024-01-01, end_date=2024-12-31)>"
    )
    assert budget.__repr__() == expected
