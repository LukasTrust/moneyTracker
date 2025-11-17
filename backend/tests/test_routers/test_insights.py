"""
Tests for Insights Router endpoints
"""
import pytest


def test_insights_router_imports():
    """Test that insights router can be imported"""
    from app.routers import insights
    
    assert hasattr(insights, 'router')
    assert insights.router is not None


def test_router_has_get_insights_endpoint():
    """Test that get_insights endpoint exists"""
    from app.routers import insights
    
    assert hasattr(insights, 'get_insights')
    assert callable(insights.get_insights)


def test_router_has_generate_insights_endpoint():
    """Test that generate_insights endpoint exists"""
    from app.routers import insights
    
    assert hasattr(insights, 'generate_insights')
    assert callable(insights.generate_insights)


def test_router_has_dismiss_insight_endpoint():
    """Test that dismiss_insight endpoint exists"""
    from app.routers import insights
    
    # Check for dismiss or mark_as_read functionality
    assert hasattr(insights, 'dismiss_insight') or hasattr(insights, 'mark_as_read')


def test_insights_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.insights import router
    from fastapi import APIRouter
    
    assert isinstance(router, APIRouter)


def test_insight_schema_exists():
    """Test that insight schema exists"""
    from app.schemas.insight import InsightResponse
    
    assert InsightResponse is not None


def test_insight_model_exists():
    """Test that Insight model exists"""
    from app.models.insight import Insight
    
    assert Insight is not None
    assert hasattr(Insight, '__tablename__')


def test_insights_uses_generator_service():
    """Test that insights router uses InsightsGenerator service"""
    from app.routers.insights import InsightsGenerator
    
    assert InsightsGenerator is not None
