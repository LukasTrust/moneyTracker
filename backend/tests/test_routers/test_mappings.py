"""
Tests for Mappings Router endpoints
"""
import pytest


def test_mappings_router_imports():
    """Test that mappings router can be imported"""
    from app.routers import mappings
    
    assert hasattr(mappings, 'router')
    assert mappings.router is not None


def test_mappings_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.mappings import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_mapping_model_used():
    """Test that Mapping model is used"""
    from app.routers.mappings import Mapping
    
    assert Mapping is not None
