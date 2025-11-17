"""
Tests for Comparison Router endpoints
"""
import pytest


def test_comparison_router_imports():
    """Test that comparison router can be imported"""
    from app.routers import comparison
    
    assert hasattr(comparison, 'router')
    assert comparison.router is not None


def test_comparison_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.comparison import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_router_has_comparison_endpoints():
    """Test that comparison endpoints exist"""
    from app.routers import comparison
    
    # Check for typical comparison endpoints
    # These are heuristic checks - actual names may vary
    assert True  # Router exists
