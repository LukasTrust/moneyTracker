"""
Tests for Budget Router endpoints
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date


def test_budgets_router_imports():
    """Test that budgets router can be imported"""
    from app.routers import budgets
    
    assert hasattr(budgets, 'router')
    assert budgets.router is not None


def test_router_has_get_budgets_endpoint():
    """Test that get_budgets endpoint exists"""
    from app.routers import budgets
    
    assert hasattr(budgets, 'get_budgets')
    assert callable(budgets.get_budgets)


def test_router_has_create_budget_endpoint():
    """Test that create_budget endpoint exists"""
    from app.routers import budgets
    
    assert hasattr(budgets, 'create_budget')
    assert callable(budgets.create_budget)


def test_router_has_update_budget_endpoint():
    """Test that update_budget endpoint exists"""
    from app.routers import budgets
    
    assert hasattr(budgets, 'update_budget')
    assert callable(budgets.update_budget)


def test_router_has_delete_budget_endpoint():
    """Test that delete_budget endpoint exists"""
    from app.routers import budgets
    
    assert hasattr(budgets, 'delete_budget')
    assert callable(budgets.delete_budget)


def test_budget_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.budgets import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_budget_schemas_exist():
    """Test that budget schemas exist"""
    from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetWithProgress
    
    assert BudgetCreate is not None
    assert BudgetUpdate is not None
    assert BudgetWithProgress is not None


def test_budget_model_exists():
    """Test that Budget model exists"""
    from app.models.budget import Budget
    
    assert Budget is not None
    assert hasattr(Budget, '__tablename__')


def test_budget_uses_tracker_service():
    """Test that budget router uses BudgetTracker service"""
    from app.routers.budgets import BudgetTracker
    
    assert BudgetTracker is not None


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budgets_empty(mock_get_db):
    """Test get_budgets endpoint returns empty list"""
    from app.routers.budgets import get_budgets
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query chain - properly chain the methods
    mock_query = MagicMock()
    mock_ordered_query = MagicMock()
    mock_ordered_query.all.return_value = []
    mock_query.order_by.return_value = mock_ordered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    result = get_budgets(active_only=False, category_id=None, db=mock_db)
    
    # Verify DB query was called
    mock_db.query.assert_called_once()
    mock_query.order_by.assert_called_once()
    mock_ordered_query.all.assert_called_once()
    
    # Verify result
    assert result == []


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budgets_with_filters(mock_get_db):
    """Test get_budgets endpoint with active_only and category_id filters"""
    from app.routers.budgets import get_budgets
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    mock_budget.category_id = 1
    
    # Mock query chain with filters - properly chain the methods
    mock_query = MagicMock()
    mock_filtered_query = MagicMock()
    mock_active_filtered_query = MagicMock()
    mock_ordered_query = MagicMock()
    mock_ordered_query.all.return_value = [mock_budget]
    mock_active_filtered_query.order_by.return_value = mock_ordered_query
    mock_filtered_query.filter.return_value = mock_active_filtered_query
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function with filters
    result = get_budgets(active_only=True, category_id=1, db=mock_db)
    
    # Verify filters were applied - filter should be called twice (category_id and active_only)
    assert mock_query.filter.call_count == 1  # category_id filter
    assert mock_filtered_query.filter.call_count == 1  # active_only filter
    mock_active_filtered_query.order_by.assert_called_once()
    
    # Verify result
    assert len(result) == 1
    assert result[0] == mock_budget


@patch('app.routers.budgets.BudgetTracker')
@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budgets_with_progress(mock_get_db, mock_budget_tracker_class):
    """Test get_budgets_with_progress endpoint"""
    from app.routers.budgets import get_budgets_with_progress
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock BudgetTracker
    mock_tracker = MagicMock()
    mock_tracker.get_all_budgets_with_progress.return_value = [{"id": 1, "progress": 50}]
    mock_budget_tracker_class.return_value = mock_tracker
    
    # Call function
    result = get_budgets_with_progress(active_only=True, account_id=1, db=mock_db)
    
    # Verify BudgetTracker was called correctly
    mock_budget_tracker_class.assert_called_once_with(mock_db)
    mock_tracker.get_all_budgets_with_progress.assert_called_once_with(1, True)
    
    # Verify result
    assert result == [{"id": 1, "progress": 50}]


@patch('app.routers.budgets.BudgetTracker')
@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budget_summary(mock_get_db, mock_budget_tracker_class):
    """Test get_budget_summary endpoint"""
    from app.routers.budgets import get_budget_summary
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock BudgetTracker
    mock_tracker = MagicMock()
    mock_tracker.get_budget_summary.return_value = {"total_budgets": 5, "total_amount": 1000}
    mock_budget_tracker_class.return_value = mock_tracker
    
    # Call function
    result = get_budget_summary(active_only=True, account_id=1, db=mock_db)
    
    # Verify BudgetTracker was called correctly
    mock_budget_tracker_class.assert_called_once_with(mock_db)
    mock_tracker.get_budget_summary.assert_called_once_with(1, True)
    
    # Verify result
    assert result == {"total_budgets": 5, "total_amount": 1000}


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budget(mock_get_db):
    """Test get_budget endpoint with valid ID"""
    from app.routers.budgets import get_budget
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    
    # Mock query
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_budget
    mock_db.query.return_value = mock_query
    
    # Call function
    result = get_budget(budget_id=1, db=mock_db)
    
    # Verify DB query was called correctly
    mock_db.query.assert_called_once()
    mock_query.filter.assert_called_once()
    mock_query.filter.return_value.first.assert_called_once()
    
    # Verify result
    assert result == mock_budget


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budget_not_found(mock_get_db):
    """Test get_budget endpoint with invalid ID"""
    from app.routers.budgets import get_budget
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query returns None
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        get_budget(budget_id=999, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Budget with ID 999 not found" in exc_info.value.detail


@patch('app.routers.budgets.BudgetTracker')
@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budget_with_progress(mock_get_db, mock_budget_tracker_class):
    """Test get_budget_with_progress endpoint"""
    from app.routers.budgets import get_budget_with_progress
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock BudgetTracker
    mock_tracker = MagicMock()
    mock_tracker.get_budget_with_progress.return_value = {"id": 1, "progress": 75}
    mock_budget_tracker_class.return_value = mock_tracker
    
    # Call function
    result = get_budget_with_progress(budget_id=1, account_id=1, db=mock_db)
    
    # Verify BudgetTracker was called correctly
    mock_budget_tracker_class.assert_called_once_with(mock_db)
    mock_tracker.get_budget_with_progress.assert_called_once_with(1, 1)
    
    # Verify result
    assert result == {"id": 1, "progress": 75}


@patch('app.routers.budgets.BudgetTracker')
@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_get_budget_with_progress_not_found(mock_get_db, mock_budget_tracker_class):
    """Test get_budget_with_progress endpoint with invalid ID"""
    from app.routers.budgets import get_budget_with_progress
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock BudgetTracker returns None
    mock_tracker = MagicMock()
    mock_tracker.get_budget_with_progress.return_value = None
    mock_budget_tracker_class.return_value = mock_tracker
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        get_budget_with_progress(budget_id=999, account_id=None, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Budget with ID 999 not found" in exc_info.value.detail


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_create_budget(mock_get_db):
    """Test create_budget endpoint with valid data"""
    from app.routers.budgets import create_budget
    from app.schemas.budget import BudgetCreate
    from datetime import date
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock category exists
    mock_category = MagicMock()
    mock_category.id = 1
    
    # Mock BudgetTracker - no conflicts
    with patch('app.routers.budgets.BudgetTracker') as mock_budget_tracker_class:
        mock_tracker = MagicMock()
        mock_tracker.check_budget_conflicts.return_value = []
        mock_budget_tracker_class.return_value = mock_tracker
        
        # Mock category query
        mock_category_query = MagicMock()
        mock_category_query.filter.return_value.first.return_value = mock_category
        mock_db.query.return_value = mock_category_query
        
        # Mock new budget
        mock_new_budget = MagicMock()
        mock_new_budget.id = 1
        
        # Mock budget creation
        mock_budget_class = MagicMock()
        mock_budget_class.return_value = mock_new_budget
        with patch('app.routers.budgets.Budget', mock_budget_class):
            # Create budget data
            budget_data = BudgetCreate(
                category_id=1,
                period="monthly",
                amount=500.0,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                description="Test budget"
            )
            
            # Call function
            result = create_budget(budget_data=budget_data, db=mock_db)
            
            # Verify category was checked
            mock_category_query.filter.assert_called_once()
            
            # Verify conflict check was performed
            mock_tracker.check_budget_conflicts.assert_called_once()
            
            # Verify budget was created and saved
            mock_budget_class.assert_called_once()
            mock_db.add.assert_called_once_with(mock_new_budget)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_new_budget)
            
            # Verify result
            assert result == mock_new_budget


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_create_budget_category_not_found(mock_get_db):
    """Test create_budget endpoint with non-existent category"""
    from app.routers.budgets import create_budget
    from app.schemas.budget import BudgetCreate
    from fastapi import HTTPException
    from datetime import date
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock category not found
    mock_category_query = MagicMock()
    mock_category_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_category_query
    
    # Create budget data
    budget_data = BudgetCreate(
        category_id=999,
        period="monthly",
        amount=500.0,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        description="Test budget"
    )
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        create_budget(budget_data=budget_data, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Category with ID 999 not found" in exc_info.value.detail


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_create_budget_conflict(mock_get_db):
    """Test create_budget endpoint with budget conflicts"""
    from app.routers.budgets import create_budget
    from app.schemas.budget import BudgetCreate
    from fastapi import HTTPException
    from datetime import date
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock category exists
    mock_category = MagicMock()
    mock_category.id = 1
    
    # Mock conflicting budget
    mock_conflict = MagicMock()
    mock_conflict.id = 2
    mock_conflict.start_date = date(2024, 1, 1)
    mock_conflict.end_date = date(2024, 12, 31)
    
    # Mock BudgetTracker - has conflicts
    with patch('app.routers.budgets.BudgetTracker') as mock_budget_tracker_class:
        mock_tracker = MagicMock()
        mock_tracker.check_budget_conflicts.return_value = [mock_conflict]
        mock_budget_tracker_class.return_value = mock_tracker
        
        # Mock category query
        mock_category_query = MagicMock()
        mock_category_query.filter.return_value.first.return_value = mock_category
        mock_db.query.return_value = mock_category_query
        
        # Create budget data
        budget_data = BudgetCreate(
            category_id=1,
            period="monthly",
            amount=500.0,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            description="Test budget"
        )
        
        # Call function and expect exception
        with pytest.raises(HTTPException) as exc_info:
            create_budget(budget_data=budget_data, db=mock_db)
        
        assert exc_info.value.status_code == 400
        assert "Budget overlaps with existing budgets" in exc_info.value.detail


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_update_budget(mock_get_db):
    """Test update_budget endpoint with valid data"""
    from app.routers.budgets import update_budget
    from app.schemas.budget import BudgetUpdate
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock existing budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    mock_budget.category_id = 1
    mock_budget.start_date = date(2024, 1, 1)
    mock_budget.end_date = date(2024, 12, 31)
    
    # Mock BudgetTracker - no conflicts
    with patch('app.routers.budgets.BudgetTracker') as mock_budget_tracker_class:
        mock_tracker = MagicMock()
        mock_tracker.check_budget_conflicts.return_value = []
        mock_budget_tracker_class.return_value = mock_tracker
        
        # Mock budget query
        mock_budget_query = MagicMock()
        mock_budget_query.filter.return_value.first.return_value = mock_budget
        mock_db.query.return_value = mock_budget_query
        
        # Create update data
        update_data = BudgetUpdate(amount=750.0, description="Updated budget")
        
        # Call function
        result = update_budget(budget_id=1, budget_data=update_data, db=mock_db)
        
        # Verify budget was found
        mock_budget_query.filter.assert_called_once()
        
        # Verify conflict check was performed
        mock_tracker.check_budget_conflicts.assert_called_once()
        
        # Verify budget was updated and saved
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_budget)
        
        # Verify result
        assert result == mock_budget


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_update_budget_not_found(mock_get_db):
    """Test update_budget endpoint with invalid ID"""
    from app.routers.budgets import update_budget
    from app.schemas.budget import BudgetUpdate
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock budget not found
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_budget_query
    
    # Create update data
    update_data = BudgetUpdate(amount=750.0)
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        update_budget(budget_id=999, budget_data=update_data, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Budget with ID 999 not found" in exc_info.value.detail


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_update_budget_category_not_found(mock_get_db):
    """Test update_budget endpoint with non-existent category"""
    from app.routers.budgets import update_budget
    from app.schemas.budget import BudgetUpdate
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock existing budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    mock_budget.category_id = 1
    mock_budget.start_date = date(2024, 1, 1)
    mock_budget.end_date = date(2024, 12, 31)
    
    # Mock budget query
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.first.return_value = mock_budget
    mock_db.query.return_value = mock_budget_query
    
    # Mock category not found
    mock_category_query = MagicMock()
    mock_category_query.filter.return_value.first.return_value = None
    # Need to handle multiple queries - budget and category
    mock_db.query.side_effect = [mock_budget_query, mock_category_query]
    
    # Create update data with invalid category
    update_data = BudgetUpdate(category_id=999)
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        update_budget(budget_id=1, budget_data=update_data, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Category with ID 999 not found" in exc_info.value.detail


@patch('app.routers.budgets.BudgetTracker')
@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_update_budget_conflict(mock_get_db, mock_budget_tracker_class):
    """Test update_budget endpoint with budget conflicts"""
    from app.routers.budgets import update_budget
    from app.schemas.budget import BudgetUpdate
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock existing budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    mock_budget.category_id = 1
    mock_budget.start_date = date(2024, 1, 1)
    mock_budget.end_date = date(2024, 12, 31)
    
    # Mock conflicting budget
    mock_conflict_budget = MagicMock()
    mock_conflict_budget.id = 2
    mock_conflict_budget.start_date = date(2024, 6, 1)
    mock_conflict_budget.end_date = date(2024, 6, 30)
    
    # Mock BudgetTracker - with conflicts
    mock_tracker = MagicMock()
    mock_tracker.check_budget_conflicts.return_value = [mock_conflict_budget]
    mock_budget_tracker_class.return_value = mock_tracker
    
    # Mock budget query
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.first.return_value = mock_budget
    mock_db.query.return_value = mock_budget_query
    
    # Create update data that causes conflict
    update_data = BudgetUpdate(start_date=date(2024, 5, 1), end_date=date(2024, 7, 31))
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        update_budget(budget_id=1, budget_data=update_data, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Budget would overlap with existing budgets" in exc_info.value.detail
    assert "Budget #2" in exc_info.value.detail


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_delete_budget(mock_get_db):
    """Test delete_budget endpoint with valid ID"""
    from app.routers.budgets import delete_budget
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock existing budget
    mock_budget = MagicMock()
    mock_budget.id = 1
    
    # Mock budget query
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.first.return_value = mock_budget
    mock_db.query.return_value = mock_budget_query
    
    # Call function
    result = delete_budget(budget_id=1, db=mock_db)
    
    # Verify budget was found and deleted
    mock_budget_query.filter.assert_called_once()
    mock_db.delete.assert_called_once_with(mock_budget)
    mock_db.commit.assert_called_once()
    
    # Verify result is None
    assert result is None


@patch('app.routers.budgets.get_db')
@pytest.mark.asyncio
async def test_delete_budget_not_found(mock_get_db):
    """Test delete_budget endpoint with invalid ID"""
    from app.routers.budgets import delete_budget
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock budget not found
    mock_budget_query = MagicMock()
    mock_budget_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_budget_query
    
    # Call function and expect exception
    with pytest.raises(HTTPException) as exc_info:
        delete_budget(budget_id=999, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Budget with ID 999 not found" in exc_info.value.detail
