"""
Tests for Transfer Router endpoints
"""
import pytest


def test_transfers_router_imports():
    """Test that transfers router can be imported"""
    from app.routers import transfers
    
    assert hasattr(transfers, 'router')
    assert transfers.router is not None


def test_router_has_get_transfers_endpoint():
    """Test that get_all_transfers endpoint exists"""
    from app.routers import transfers
    
    assert hasattr(transfers, 'get_all_transfers')
    assert callable(transfers.get_all_transfers)


def test_router_has_create_transfer_endpoint():
    """Test that create_transfer endpoint exists"""
    from app.routers import transfers
    
    assert hasattr(transfers, 'create_transfer')
    assert callable(transfers.create_transfer)


def test_router_has_delete_transfer_endpoint():
    """Test that delete_transfer endpoint exists"""
    from app.routers import transfers
    
    assert hasattr(transfers, 'delete_transfer')
    assert callable(transfers.delete_transfer)


def test_transfer_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.transfers import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_transfer_schemas_exist():
    """Test that transfer schemas exist"""
    from app.schemas.transfer import TransferCreate, TransferResponse
    
    assert TransferCreate is not None
    assert TransferResponse is not None


def test_transfer_model_exists():
    """Test that Transfer model exists"""
    from app.models.transfer import Transfer
    
    assert Transfer is not None
    assert hasattr(Transfer, '__tablename__')


def test_transfer_uses_matcher_service():
    """Test that transfer router uses TransferMatcher service"""
    from app.routers.transfers import TransferMatcher
    
    assert TransferMatcher is not None
