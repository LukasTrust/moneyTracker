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


def test_insight_repr():
    """Test Insight __repr__ method"""
    from app.models.insight import Insight
    from types import SimpleNamespace
    
    # Create mock insight
    insight = SimpleNamespace(
        id=1,
        insight_type='spending_alert',
        account_id=1,
        title='High spending detected'
    )
    
    # Call the actual __repr__ method
    repr_str = Insight.__repr__(insight)
    
    assert 'Insight' in repr_str
    assert '1' in repr_str
    assert 'spending_alert' in repr_str
    assert 'High spending detected' in repr_str


def test_insight_generation_log_exists():
    """Test that InsightGenerationLog model can be imported"""
    from app.models.insight import InsightGenerationLog
    
    assert InsightGenerationLog is not None
    assert hasattr(InsightGenerationLog, '__tablename__')


def test_insight_generation_log_tablename():
    """Test that InsightGenerationLog has correct table name"""
    from app.models.insight import InsightGenerationLog
    
    assert InsightGenerationLog.__tablename__ == "insight_generation_log"


def test_insight_generation_log_repr():
    """Test InsightGenerationLog __repr__ method"""
    from app.models.insight import InsightGenerationLog
    from types import SimpleNamespace
    
    # Create mock log
    log = SimpleNamespace(
        id=1,
        generation_type='monthly',
        account_id=1,
        insights_generated=5
    )
    
    # Call the actual __repr__ method
    repr_str = InsightGenerationLog.__repr__(log)
    
    assert 'InsightGenerationLog' in repr_str
    assert '1' in repr_str
    assert 'monthly' in repr_str
    assert '5' in repr_str
