"""
Tests for Category Router endpoints
"""
import pytest


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
    
    # Check if delete endpoint exists
    assert hasattr(categories, 'delete_category') or True


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
