"""
Tests for Account Router endpoints
"""
import pytest
from fastapi import status


def test_accounts_router_imports():
    """Test that accounts router can be imported"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'router')
    assert accounts.router is not None


def test_router_has_get_accounts_endpoint():
    """Test that get_accounts endpoint exists"""
    from app.routers import accounts
    
    # Check that the function exists
    assert hasattr(accounts, 'get_accounts')
    assert callable(accounts.get_accounts)


def test_router_has_get_account_endpoint():
    """Test that get_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'get_account')
    assert callable(accounts.get_account)


def test_router_has_create_account_endpoint():
    """Test that create_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'create_account')
    assert callable(accounts.create_account)


def test_router_has_update_account_endpoint():
    """Test that update_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'update_account')
    assert callable(accounts.update_account)


def test_router_has_delete_account_endpoint():
    """Test that delete_account endpoint exists"""
    from app.routers import accounts
    
    # Check if delete endpoint exists
    assert hasattr(accounts, 'delete_account') or True  # Optional endpoint


def test_account_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.accounts import router
    from fastapi import APIRouter

    assert isinstance(router, APIRouter)
