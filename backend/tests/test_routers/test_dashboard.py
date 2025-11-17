"""
Tests for Dashboard Router endpoints
"""
import pytest


def test_dashboard_router_imports():
    from app.routers import dashboard
    assert hasattr(dashboard, 'router')


def test_dashboard_router_uses_apiRouter():
    from app.routers.dashboard import router
    from fastapi import APIRouter
    assert isinstance(router, APIRouter)
