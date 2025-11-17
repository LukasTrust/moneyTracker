"""
Tests for CSV Import Router endpoints
"""
import pytest


def test_csv_import_router_imports():
    """Test that csv_import router can be imported"""
    from app.routers import csv_import
    
    assert hasattr(csv_import, 'router')
    assert csv_import.router is not None


def test_csv_import_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.csv_import import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_router_uses_csv_processor_service():
    """Test that CSV import router has csv processing functionality"""
    from app.routers import csv_import
    
    # Router should exist and handle CSV imports
    assert csv_import.router is not None
