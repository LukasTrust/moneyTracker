"""
Tests for Recipients Router endpoints
"""
import pytest


def test_recipients_router_imports():
    """Test that recipients router can be imported"""
    from app.routers import recipients
    
    assert hasattr(recipients, 'router')
    assert recipients.router is not None


def test_recipients_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.recipients import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_recipient_model_used():
    """Test that Recipient model is used"""
    from app.routers.recipients import Recipient
    
    assert Recipient is not None


def test_router_uses_recipient_matcher():
    """Test that recipients router uses RecipientMatcher"""
    from app.routers.recipients import RecipientMatcher
    
    assert RecipientMatcher is not None
