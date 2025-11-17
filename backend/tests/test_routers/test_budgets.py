"""
Tests for Budget Router endpoints
"""
import pytest


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
