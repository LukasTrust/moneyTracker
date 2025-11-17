"""
Tests for Data Router endpoints
"""
import pytest


def test_data_router_imports():
    """Test that data router can be imported"""
    from app.routers import data
    
    assert hasattr(data, 'router')
    assert data.router is not None


def test_data_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.data import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_data_row_model_used():
    """Test that DataRow model is used"""
    from app.routers.data import DataRow
    
    assert DataRow is not None
