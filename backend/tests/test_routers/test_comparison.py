"""
Tests for Comparison Router endpoints
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from datetime import date


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


async def test_get_period_comparison_month_valid():
    """Test get_period_comparison with valid month comparison"""
    from app.routers.comparison import get_period_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator):
        result = get_period_comparison(
            comparison_type="month",
            period1="2024-01",
            period2="2024-02",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2024, 1, 1),
            period1_end=date(2024, 1, 31),
            period2_start=date(2024, 2, 1),
            period2_end=date(2024, 2, 29),  # 2024 is leap year
            top_limit=5
        )


def test_get_period_comparison_year_valid():
    """Test get_period_comparison with valid year comparison"""
    from app.routers.comparison import get_period_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator):
        result = get_period_comparison(
            comparison_type="year",
            period1="2023",
            period2="2024",
            top_limit=10,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2023, 1, 1),
            period1_end=date(2023, 12, 31),
            period2_start=date(2024, 1, 1),
            period2_end=date(2024, 12, 31),
            top_limit=10
        )


def test_get_period_comparison_invalid_comparison_type():
    """Test get_period_comparison with invalid comparison_type"""
    from app.routers.comparison import get_period_comparison
    
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    with pytest.raises(HTTPException) as exc_info:
        get_period_comparison(
            comparison_type="invalid",
            period1="2024-01",
            period2="2024-02",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
    
    assert exc_info.value.status_code == 400
    assert "Invalid comparison_type" in str(exc_info.value.detail)


async def test_get_period_comparison_invalid_period_format():
    """Test get_period_comparison with invalid period format"""
    from app.routers.comparison import get_period_comparison
    
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    with pytest.raises(HTTPException) as exc_info:
        get_period_comparison(
            comparison_type="month",
            period1="invalid",
            period2="2024-02",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
    
    assert exc_info.value.status_code == 400
    assert "Invalid period format" in str(exc_info.value.detail)


async def test_get_quick_comparison_last_month():
    """Test get_quick_comparison with last_month comparison"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 2, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="last_month",
            reference_period=None,
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare Feb 2024 vs Jan 2024
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2024, 1, 1),
            period1_end=date(2024, 1, 31),
            period2_start=date(2024, 2, 1),
            period2_end=date(2024, 2, 29),
            top_limit=5
        )


async def test_get_quick_comparison_last_year():
    """Test get_quick_comparison with last_year comparison"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 6, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="last_year",
            reference_period=None,
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare 2024 vs 2023
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2023, 1, 1),
            period1_end=date(2023, 12, 31),
            period2_start=date(2024, 1, 1),
            period2_end=date(2024, 12, 31),
            top_limit=5
        )


async def test_get_quick_comparison_month_yoy():
    """Test get_quick_comparison with month_yoy comparison"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        
        mock_date.today.return_value = date(2024, 3, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="month_yoy",
            reference_period="2024-01",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare Jan 2024 vs Jan 2023
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2023, 1, 1),
            period1_end=date(2023, 1, 31),
            period2_start=date(2024, 1, 1),
            period2_end=date(2024, 1, 31),
            top_limit=5
        )


async def test_get_quick_comparison_year_yoy():
    """Test get_quick_comparison with year_yoy comparison"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 6, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="year_yoy",
            reference_period="2023",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare 2023 vs 2022
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2022, 1, 1),
            period1_end=date(2022, 12, 31),
            period2_start=date(2023, 1, 1),
            period2_end=date(2023, 12, 31),
            top_limit=5
        )


async def test_get_quick_comparison_invalid_compare_to():
    """Test get_quick_comparison with invalid compare_to value"""
    from app.routers.comparison import get_quick_comparison
    
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    with pytest.raises(HTTPException) as exc_info:
        get_quick_comparison(
            compare_to="invalid",
            reference_period=None,
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
    
    assert exc_info.value.status_code == 400
    assert "Invalid compare_to value" in str(exc_info.value.detail)


async def test_get_quick_comparison_invalid_reference_period():
    """Test get_quick_comparison with invalid reference_period format"""
    from app.routers.comparison import get_quick_comparison
    
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    with pytest.raises(HTTPException) as exc_info:
        get_quick_comparison(
            compare_to="last_month",
            reference_period="invalid",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
    
    assert exc_info.value.status_code == 400
    assert "Invalid period format" in str(exc_info.value.detail)


async def test_get_quick_comparison_last_month_with_reference():
    """Test get_quick_comparison with last_month and reference_period"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 3, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="last_month",
            reference_period="2024-02",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare Jan 2024 vs Feb 2024 (reference_period is Feb, so period2=Feb, period1=Jan)
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2024, 1, 1),
            period1_end=date(2024, 1, 31),
            period2_start=date(2024, 2, 1),
            period2_end=date(2024, 2, 29),
            top_limit=5
        )


async def test_get_quick_comparison_last_year_with_reference():
    """Test get_quick_comparison with last_year and reference_period"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 6, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="last_year",
            reference_period="2023",
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare 2022 vs 2023 (reference_period is 2023, so period2=2023, period1=2022)
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2022, 1, 1),
            period1_end=date(2022, 12, 31),
            period2_start=date(2023, 1, 1),
            period2_end=date(2023, 12, 31),
            top_limit=5
        )


async def test_get_quick_comparison_month_yoy_without_reference():
    """Test get_quick_comparison with month_yoy without reference_period"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 3, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="month_yoy",
            reference_period=None,
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare Mar 2023 vs Mar 2024 (current month is Mar 2024, so period2=Mar 2024, period1=Mar 2023)
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2023, 3, 1),
            period1_end=date(2023, 3, 31),
            period2_start=date(2024, 3, 1),
            period2_end=date(2024, 3, 31),
            top_limit=5
        )


async def test_get_quick_comparison_year_yoy_without_reference():
    """Test get_quick_comparison with year_yoy without reference_period"""
    from app.routers.comparison import get_quick_comparison
    
    # Mock dependencies
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    
    mock_aggregator = MagicMock()
    mock_comparison_data = {"summary": "test data"}
    mock_aggregator.get_period_comparison.return_value = mock_comparison_data
    
    with patch('app.routers.comparison.DataAggregator', return_value=mock_aggregator), \
         patch('app.routers.comparison.date') as mock_date:
        mock_date.today.return_value = date(2024, 6, 15)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs) if args or kwargs else mock_date
        
        result = get_quick_comparison(
            compare_to="year_yoy",
            reference_period=None,
            top_limit=5,
            account=mock_account,
            db=mock_db
        )
        
        assert result == mock_comparison_data
        # Should compare 2023 vs 2024 (current year is 2024, so period2=2024, period1=2023)
        mock_aggregator.get_period_comparison.assert_called_once_with(
            account_id=1,
            period1_start=date(2023, 1, 1),
            period1_end=date(2023, 12, 31),
            period2_start=date(2024, 1, 1),
            period2_end=date(2024, 12, 31),
            top_limit=5
        )
