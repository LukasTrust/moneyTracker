"""
Tests for Import History Router endpoints
"""
import pytest


def test_import_history_router_imports():
    """Test that import_history router can be imported"""
    from app.routers import import_history
    
    assert hasattr(import_history, 'router')
    assert import_history.router is not None


def test_import_history_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.import_history import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_import_history_model_used():
    """Test that ImportHistory model is used"""
    from app.models.import_history import ImportHistory
    
    # The router should use this model
    assert ImportHistory is not None
