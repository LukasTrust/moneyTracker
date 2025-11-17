"""
Tests for Insight Model
"""
import pytest


def test_insight_model_exists():
    """Test that Insight model can be imported"""
    from app.models.insight import Insight
    
    assert Insight is not None
    assert hasattr(Insight, '__tablename__')


def test_insight_tablename():
    """Test that Insight has correct table name"""
    from app.models.insight import Insight
    
    assert Insight.__tablename__ == "insights"


def test_insight_has_required_columns():
    """Test that Insight has all required columns"""
    from app.models.insight import Insight
    
    assert hasattr(Insight, 'id')
    assert hasattr(Insight, 'account_id')
    assert hasattr(Insight, 'insight_type')
    assert hasattr(Insight, 'title')
    assert hasattr(Insight, 'description')  # 'description' not 'message'
    assert hasattr(Insight, 'priority')
    assert hasattr(Insight, 'is_dismissed')  # 'is_dismissed' not 'is_read'
    assert hasattr(Insight, 'created_at')


def test_insight_has_account_relationship():
    """Test that Insight has relationship to Account"""
    from app.models.insight import Insight
    
    assert hasattr(Insight, 'account')


def test_insight_default_is_dismissed():
    """Test that is_dismissed defaults to False"""
    from app.models.insight import Insight
    
    is_dismissed_col = Insight.__table__.columns['is_dismissed']
    assert is_dismissed_col.default is not None
    assert is_dismissed_col.default.arg is False


def test_insight_generation_log_exists():
    """Test that InsightGenerationLog model exists"""
    from app.models.insight import InsightGenerationLog
    
    assert InsightGenerationLog is not None
    assert hasattr(InsightGenerationLog, '__tablename__')


def test_insight_generation_log_tablename():
    """Test that InsightGenerationLog has correct table name"""
    from app.models.insight import InsightGenerationLog
    
    assert InsightGenerationLog.__tablename__ == "insight_generation_log"
