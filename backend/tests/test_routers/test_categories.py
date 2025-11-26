"""
Tests for Category Router endpoints
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


def test_categories_router_imports():
    """Test that categories router can be imported"""
    from app.routers import categories
    
    assert hasattr(categories, 'router')
    assert categories.router is not None


def test_router_has_get_categories_endpoint():
    """Test that get_categories endpoint exists"""
    from app.routers import categories
    
    assert hasattr(categories, 'get_categories')
    assert callable(categories.get_categories)


def test_router_has_get_category_endpoint():
    """Test that get_category endpoint exists"""
    from app.routers import categories
    
    assert hasattr(categories, 'get_category')
    assert callable(categories.get_category)


def test_router_has_create_category_endpoint():
    """Test that create_category endpoint exists"""
    from app.routers import categories
    
    assert hasattr(categories, 'create_category')
    assert callable(categories.create_category)


def test_router_has_update_category_endpoint():
    """Test that update_category endpoint exists"""
    from app.routers import categories
    
    assert hasattr(categories, 'update_category')
    assert callable(categories.update_category)


def test_router_has_delete_category_endpoint():
    """Test that delete_category endpoint exists"""
    from app.routers import categories
    
    assert hasattr(categories, 'delete_category')
    assert callable(categories.delete_category)


def test_category_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.categories import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_category_response_schema_exists():
    """Test that category response schemas exist"""
    from app.schemas.category import CategoryResponse, CategoryCreate, CategoryUpdate
    
    assert CategoryResponse is not None
    assert CategoryCreate is not None
    assert CategoryUpdate is not None


def test_category_model_exists():
    """Test that Category model exists"""
    from app.models.category import Category
    
    assert Category is not None
    assert hasattr(Category, '__tablename__')


def test_category_uses_matcher_service():
    """Test that category router uses CategoryMatcher service"""
    from app.routers.categories import CategoryMatcher
    
    assert CategoryMatcher is not None


@pytest.mark.asyncio
async def test_get_categories_empty():
    """Test get_categories with no categories"""
    from app.routers.categories import get_categories
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = []
    
    result = get_categories(mock_db)
    
    assert result == []
    mock_db.query.assert_called_once()
    mock_db.query.return_value.all.assert_called_once()


@pytest.mark.asyncio
async def test_get_categories_with_data():
    """Test get_categories with categories"""
    from app.routers.categories import get_categories
    from app.models.category import Category
    
    # Mock categories
    mock_category1 = MagicMock(spec=Category)
    mock_category1.id = 1
    mock_category1.name = "Food"
    mock_category1.color = "#ff0000"
    mock_category1.icon = "🍕"
    mock_category1.mappings = {"patterns": ["restaurant", "food"]}
    
    mock_category2 = MagicMock(spec=Category)
    mock_category2.id = 2
    mock_category2.name = "Transport"
    mock_category2.color = "#00ff00"
    mock_category2.icon = "🚗"
    mock_category2.mappings = {"patterns": ["taxi", "bus"]}
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [mock_category1, mock_category2]
    
    result = get_categories(mock_db)
    
    assert len(result) == 2
    assert result[0] == mock_category1
    assert result[1] == mock_category2


@pytest.mark.asyncio
async def test_get_category():
    """Test get_category successfully"""
    from app.routers.categories import get_category
    from app.models.category import Category
    
    # Mock category
    mock_category = MagicMock(spec=Category)
    mock_category.id = 1
    mock_category.name = "Food"
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_category
    mock_db.query.return_value = mock_query
    
    result = get_category(1, mock_db)
    
    assert result == mock_category
    mock_db.query.assert_called_once_with(Category)
    mock_query.filter.assert_called_once()
    mock_query.filter.return_value.first.assert_called_once()


@pytest.mark.asyncio
async def test_get_category_not_found():
    """Test get_category with non-existent category"""
    from app.routers.categories import get_category
    from app.models.category import Category
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        get_category(999, mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Category with ID 999 not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_create_category():
    """Test create_category successfully"""
    from app.routers.categories import create_category
    from app.models.category import Category
    from app.schemas.category import CategoryCreate
    
    # Mock category data
    category_data = CategoryCreate(
        name="New Category",
        color="#ff0000",
        icon="⭐",
        mappings={"patterns": ["test", "pattern"]}
    )
    
    # Mock category instance
    mock_category = MagicMock(spec=Category)
    mock_category.id = 1
    mock_category.name = "New Category"
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None  # No existing category
    mock_db.query.return_value = mock_query
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None
    
    # Mock Category constructor
    with patch('app.routers.categories.Category') as mock_category_class:
        mock_category_class.return_value = mock_category
        
        result = create_category(category_data, mock_db)
        
        assert result == mock_category
        mock_category_class.assert_called_once_with(
            name="New Category",
            color="#ff0000",
            icon="⭐",
            mappings={"patterns": ["test", "pattern"]}
        )
        mock_db.add.assert_called_once_with(mock_category)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_category)


@pytest.mark.asyncio
async def test_create_category_name_exists():
    """Test create_category with existing name"""
    from app.routers.categories import create_category
    from app.schemas.category import CategoryCreate
    from fastapi import HTTPException
    
    # Mock category data
    category_data = CategoryCreate(
        name="Existing Category",
        color="#ff0000",
        mappings={"patterns": []}
    )
    
    # Mock existing category
    mock_existing = MagicMock()
    mock_existing.name = "Existing Category"
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_existing
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        create_category(category_data, mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Category with name 'Existing Category' already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_category():
    """Test update_category successfully"""
    from app.routers.categories import update_category
    from app.models.category import Category
    from app.schemas.category import CategoryUpdate
    
    # Mock update data
    update_data = CategoryUpdate(
        name="Updated Name",
        color="#00ff00",
        mappings={"patterns": ["new", "patterns"]}
    )
    
    # Mock category
    mock_category = MagicMock(spec=Category)
    mock_category.id = 1
    mock_category.name = "Old Name"
    mock_category.mappings = {"patterns": ["old"]}
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_category
    mock_db.query.return_value = mock_query
    
    # Mock name uniqueness check
    mock_query2 = MagicMock()
    mock_query2.filter.return_value.first.return_value = None
    mock_db.query.side_effect = [mock_query, mock_query2]
    
    with patch('app.routers.categories.attributes.flag_modified'):
        result = update_category(1, update_data, mock_db)
        
        assert result == mock_category
        # Check that attributes were set
        assert mock_category.name == "Updated Name"
        assert mock_category.color == "#00ff00"
        assert mock_category.mappings == {"patterns": ["new", "patterns"]}


@pytest.mark.asyncio
async def test_update_category_not_found():
    """Test update_category with non-existent category"""
    from app.routers.categories import update_category
    from app.schemas.category import CategoryUpdate
    from fastapi import HTTPException
    
    # Mock update data
    update_data = CategoryUpdate(name="New Name")
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        update_category(999, update_data, mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Category with ID 999 not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_category_name_conflict():
    """Test update_category with name that already exists"""
    from app.routers.categories import update_category
    from app.schemas.category import CategoryUpdate
    from fastapi import HTTPException
    
    # Mock update data with conflicting name
    update_data = CategoryUpdate(name="Existing Name")
    
    # Mock existing category
    mock_category = MagicMock()
    mock_category.id = 1
    mock_category.name = "Old Name"
    
    # Mock conflicting category
    mock_conflicting_category = MagicMock()
    mock_conflicting_category.id = 2
    mock_conflicting_category.name = "Existing Name"
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query1 = MagicMock()
    mock_query1.filter.return_value.first.return_value = mock_category
    mock_query2 = MagicMock()
    mock_query2.filter.return_value.first.return_value = mock_conflicting_category
    mock_db.query.side_effect = [mock_query1, mock_query2]
    
    with pytest.raises(HTTPException) as exc_info:
        update_category(1, update_data, mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Category with name 'Existing Name' already exists" in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_category_pattern_too_long():
    """Test update_category with patterns that are too long"""
    from app.routers.categories import update_category
    from app.schemas.category import CategoryUpdate
    from fastapi import HTTPException
    
    # Mock update data with overly long pattern
    long_pattern = "a" * 101  # 101 characters, exceeds limit
    update_data = CategoryUpdate(mappings={"patterns": [long_pattern]})
    
    # Mock category
    mock_category = MagicMock()
    mock_category.id = 1
    mock_category.name = "Test Category"
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_category
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        update_category(1, update_data, mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Pattern length must not exceed 100 characters" in exc_info.value.detail


@pytest.mark.asyncio
async def test_delete_category():
    """Test delete_category successfully"""
    from app.routers.categories import delete_category
    from app.models.category import Category
    
    # Mock category
    mock_category = MagicMock(spec=Category)
    mock_category.id = 1
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_category
    mock_db.query.return_value = mock_query
    
    result = delete_category(1, mock_db)
    
    assert result is None
    mock_db.delete.assert_called_once_with(mock_category)
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_category_not_found():
    """Test delete_category with non-existent category"""
    from app.routers.categories import delete_category
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        delete_category(999, mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Category with ID 999 not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_remove_pattern_from_category():
    """Test remove_pattern_from_category endpoint"""
    from app.routers.categories import remove_pattern_from_category
    
    # Mock category with patterns
    mock_category = MagicMock()
    mock_category.id = 1
    mock_category.mappings = {'patterns': ['Grocery Store', 'Supermarket', 'FOOD']}
    mock_category.name = 'Food'
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = mock_category
    mock_db.query.return_value = mock_query
    
    with patch('app.routers.categories.CategoryMatcher') as mock_matcher_class:
        mock_matcher = MagicMock()
        mock_matcher_class.return_value = mock_matcher
        
        result = remove_pattern_from_category(1, 'supermarket', mock_db)
        
        # Verify pattern was removed (case-insensitive)
        assert mock_category.mappings == {'patterns': ['Grocery Store', 'FOOD']}
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_category)
        mock_matcher.clear_cache.assert_called_once()
        assert result == mock_category


@pytest.mark.asyncio
async def test_remove_pattern_from_category_not_found():
    """Test remove_pattern_from_category with category not found"""
    from app.routers.categories import remove_pattern_from_category
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_query.filter.return_value.first.return_value = None
    mock_db.query.return_value = mock_query
    
    with pytest.raises(HTTPException) as exc_info:
        remove_pattern_from_category(999, 'pattern', mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Category with ID 999 not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_check_pattern_conflict_no_conflict():
    """Test check_pattern_conflict with no conflict"""
    from app.routers.categories import check_pattern_conflict
    
    # Mock categories without conflicting patterns
    mock_category1 = MagicMock()
    mock_category1.id = 1
    mock_category1.name = 'Food'
    mock_category1.mappings = {'patterns': ['Grocery Store']}
    
    mock_category2 = MagicMock()
    mock_category2.id = 2
    mock_category2.name = 'Transport'
    mock_category2.mappings = {'patterns': ['Gas Station']}
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [mock_category1, mock_category2]
    
    result = check_pattern_conflict('Restaurant', None, mock_db)
    
    assert result == {"conflict": False}


@pytest.mark.asyncio
async def test_check_pattern_conflict_with_conflict():
    """Test check_pattern_conflict with conflict found"""
    from app.routers.categories import check_pattern_conflict
    
    # Mock categories with conflicting pattern
    mock_category1 = MagicMock()
    mock_category1.id = 1
    mock_category1.name = 'Food'
    mock_category1.color = 'green'
    mock_category1.icon = '🍎'
    mock_category1.mappings = {'patterns': ['Grocery Store', 'Restaurant']}
    
    mock_category2 = MagicMock()
    mock_category2.id = 2
    mock_category2.name = 'Transport'
    mock_category2.mappings = {'patterns': ['Gas Station']}
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [mock_category1, mock_category2]
    
    result = check_pattern_conflict('restaurant', None, mock_db)  # case-insensitive
    
    expected = {
        "conflict": True,
        "category_id": 1,
        "category_name": 'Food',
        "category_color": 'green',
        "category_icon": '🍎'
    }
    assert result == expected


@pytest.mark.asyncio
async def test_check_pattern_conflict_exclude_current_category():
    """Test check_pattern_conflict excludes current category"""
    from app.routers.categories import check_pattern_conflict
    
    # Mock categories where current category has the pattern
    mock_category1 = MagicMock()
    mock_category1.id = 1
    mock_category1.name = 'Food'
    mock_category1.mappings = {'patterns': ['Restaurant']}
    
    mock_category2 = MagicMock()
    mock_category2.id = 2
    mock_category2.name = 'Transport'
    mock_category2.mappings = {'patterns': ['Gas Station']}
    
    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = [mock_category1, mock_category2]
    
    # Check conflict excluding category 1 (should not find conflict)
    result = check_pattern_conflict('restaurant', 1, mock_db)
    
    assert result == {"conflict": False}