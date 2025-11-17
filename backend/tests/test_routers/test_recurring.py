"""
Tests for Recurring Transactions Router endpoints
"""
import pytest


def test_recurring_router_imports():
    """Test that recurring router can be imported"""
    from app.routers import recurring
    
    assert hasattr(recurring, 'router')
    assert recurring.router is not None


def test_router_has_get_recurring_endpoint():
    """Test that get_recurring_transactions_for_account endpoint exists"""
    from app.routers import recurring
    
    assert hasattr(recurring, 'get_recurring_transactions_for_account')
    assert callable(recurring.get_recurring_transactions_for_account)


def test_router_has_detect_recurring_endpoint():
    """Test that detect_recurring_for_account endpoint exists"""
    from app.routers import recurring
    
    assert hasattr(recurring, 'detect_recurring_for_account')
    assert callable(recurring.detect_recurring_for_account)


def test_router_has_update_recurring_endpoint():
    """Test that update_recurring_transaction endpoint exists"""
    from app.routers import recurring
    
    assert hasattr(recurring, 'update_recurring_transaction')
    assert callable(recurring.update_recurring_transaction)


def test_router_has_delete_recurring_endpoint():
    """Test that delete_recurring_transaction endpoint exists"""
    from app.routers import recurring
    
    assert hasattr(recurring, 'delete_recurring_transaction')
    assert callable(recurring.delete_recurring_transaction)


def test_recurring_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.recurring import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_recurring_schema_exists():
    """Test that recurring transaction schema exists"""
    from app.schemas.recurring_transaction import RecurringTransactionResponse
    
    assert RecurringTransactionResponse is not None


def test_recurring_model_exists():
    """Test that RecurringTransaction model exists"""
    from app.models.recurring_transaction import RecurringTransaction
    
    assert RecurringTransaction is not None
    assert hasattr(RecurringTransaction, '__tablename__')


def test_recurring_uses_detector_service():
    """Test that recurring router uses RecurringTransactionDetector service"""
    from app.routers.recurring import RecurringTransactionDetector
    
    assert RecurringTransactionDetector is not None
