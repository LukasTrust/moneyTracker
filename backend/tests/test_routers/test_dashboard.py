"""
Tests for Dashboard Router endpoints
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date


def test_dashboard_router_imports():
    from app.routers import dashboard
    assert hasattr(dashboard, 'router')


def test_dashboard_router_uses_apiRouter():
    from app.routers.dashboard import router
    from fastapi import APIRouter
    assert isinstance(router, APIRouter)


def test_get_dashboard_summary():
    """Test get_dashboard_summary endpoint"""
    from app.routers.dashboard import get_dashboard_summary
    from unittest.mock import patch

    # Mock data
    mock_summary = {
        "total_income": 5000.0,
        "total_expenses": 3000.0,
        "balance": 2000.0,
        "transaction_count": 50
    }

    with patch('app.routers.dashboard.DataAggregator') as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.get_summary.return_value = mock_summary

        # Mock DB query for account count
        mock_db = MagicMock()
        mock_db.query.return_value.distinct.return_value.count.return_value = 3

        result = get_dashboard_summary(
            from_date=None,
            to_date=None,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None,
            db=mock_db
        )

        # Verify result structure
        assert result["total_income"] == 5000.0
        assert result["total_expenses"] == 3000.0
        assert result["balance"] == 2000.0
        assert result["transaction_count"] == 50
        assert result["account_count"] == 3
        assert "period" in result

        # Verify DataAggregator was called correctly
        mock_aggregator.get_summary.assert_called_once_with(
            account_id=None,
            from_date=None,
            to_date=None,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None
        )


def test_get_dashboard_summary_with_filters():
    """Test get_dashboard_summary endpoint with filters"""
    from app.routers.dashboard import get_dashboard_summary
    from unittest.mock import patch

    # Mock data
    mock_summary = {
        "total_income": 3000.0,
        "total_expenses": 1500.0,
        "balance": 1500.0,
        "transaction_count": 25
    }

    with patch('app.routers.dashboard.DataAggregator') as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.get_summary.return_value = mock_summary

        # Mock DB query for account count with filters
        mock_db = MagicMock()
        # Set up the query chain to return 2 for count()
        mock_query_chain = MagicMock()
        mock_query_chain.count.return_value = 2
        mock_db.query.return_value.distinct.return_value.filter.return_value.filter.return_value.filter.return_value = mock_query_chain

        from_date = date(2023, 1, 1)
        to_date = date(2023, 12, 31)

        result = get_dashboard_summary(
            from_date=from_date,
            to_date=to_date,
            category_id=1,
            category_ids=None,
            min_amount=10.0,
            max_amount=None,
            recipient="test",
            purpose=None,
            transaction_type=None,
            db=mock_db
        )

        # Verify result
        assert result["account_count"] == 2
        assert result["period"]["from_date"] == "2023-01-01"
        assert result["period"]["to_date"] == "2023-12-31"

        # Verify DataAggregator was called with filters
        mock_aggregator.get_summary.assert_called_once_with(
            account_id=None,
            from_date=from_date,
            to_date=to_date,
            category_id=1,
            category_ids=None,
            min_amount=10.0,
            max_amount=None,
            recipient="test",
            purpose=None,
            transaction_type=None
        )


def test_get_dashboard_categories():
    """Test get_dashboard_categories endpoint"""
    from app.routers.dashboard import get_dashboard_categories
    from unittest.mock import patch

    # Mock data
    mock_categories = [
        {"category_id": 1, "category_name": "Food", "total_amount": -500.0, "transaction_count": 10},
        {"category_id": 2, "category_name": "Transport", "total_amount": -200.0, "transaction_count": 5}
    ]

    with patch('app.routers.dashboard.DataAggregator') as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.get_category_aggregation.return_value = mock_categories

        mock_db = MagicMock()

        result = get_dashboard_categories(
            limit=5,
            from_date=None,
            to_date=None,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None,
            db=mock_db
        )

        assert result == mock_categories

        # Verify DataAggregator was called correctly
        mock_aggregator.get_category_aggregation.assert_called_once_with(
            account_id=None,
            from_date=None,
            to_date=None,
            limit=5,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None
        )


def test_get_dashboard_balance_history():
    """Test get_dashboard_balance_history endpoint"""
    from app.routers.dashboard import get_dashboard_balance_history
    from unittest.mock import patch

    # Mock data
    mock_history = {
        "labels": ["2023-01", "2023-02", "2023-03"],
        "income": [1000.0, 1200.0, 1100.0],
        "expenses": [-800.0, -900.0, -850.0],
        "balance": [200.0, 500.0, 750.0]
    }

    with patch('app.routers.dashboard.DataAggregator') as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.get_balance_history.return_value = mock_history

        mock_db = MagicMock()

        result = get_dashboard_balance_history(
            group_by="month",
            from_date=None,
            to_date=None,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None,
            db=mock_db
        )

        assert result == mock_history

        # Verify DataAggregator was called correctly
        mock_aggregator.get_balance_history.assert_called_once_with(
            account_id=None,
            from_date=None,
            to_date=None,
            group_by="month",
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            transaction_type=None
        )


def test_get_dashboard_transactions():
    """Test get_dashboard_transactions endpoint"""
    from app.routers.dashboard import get_dashboard_transactions
    from unittest.mock import patch, MagicMock
    from app.models.data_row import DataRow

    # Mock data rows
    mock_data_rows = [
        MagicMock(spec=DataRow, id=1, amount=-50.0, recipient="Store A"),
        MagicMock(spec=DataRow, id=2, amount=-25.0, recipient="Store B")
    ]

    mock_db = MagicMock()
    # Mock the query chain
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 2
    
    # Mock the offset().limit().all() chain
    mock_offset_result = MagicMock()
    mock_query.offset.return_value = mock_offset_result
    mock_offset_result.limit.return_value.all.return_value = mock_data_rows

    result = get_dashboard_transactions(
        limit=10,
        offset=0,
        category_id=None,
        category_ids=None,
        from_date=None,
        to_date=None,
        min_amount=None,
        max_amount=None,
        recipient=None,
        purpose=None,
        transaction_type=None,
        db=mock_db
    )

    # Verify result structure
    assert result["data"] == mock_data_rows
    assert result["total"] == 2
    assert result["page"] == 1
    assert result["pages"] == 1
    assert result["limit"] == 10

    # Verify query was built correctly
    mock_db.query.assert_called_once_with(DataRow)
    mock_query.order_by.assert_called_once()
    mock_query.offset.assert_called_once_with(0)
    mock_offset_result.limit.assert_called_once_with(10)


def test_get_dashboard_transactions_with_filters():
    """Test get_dashboard_transactions endpoint with various filters"""
    from app.routers.dashboard import get_dashboard_transactions
    from unittest.mock import patch, MagicMock
    from app.models.data_row import DataRow

    mock_data_rows = [MagicMock(spec=DataRow, id=1)]

    mock_db = MagicMock()
    mock_query = MagicMock()
    mock_db.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.count.return_value = 1
    mock_query.offset.return_value.limit.return_value.all.return_value = mock_data_rows

    from_date = date(2023, 1, 1)
    to_date = date(2023, 12, 31)

    result = get_dashboard_transactions(
        limit=20,
        offset=10,
        category_id=1,
        category_ids=None,
        from_date=from_date,
        to_date=to_date,
        min_amount=5.0,
        max_amount=None,
        recipient="test",
        purpose=None,
        transaction_type="expense",
        db=mock_db
    )

    assert result["total"] == 1
    assert result["page"] == 1  # (10 // 20) + 1 = 1
    assert result["limit"] == 20

    # Verify filters were applied (query.filter should be called multiple times)
    assert mock_query.filter.call_count >= 4  # from_date, to_date, min_amount, transaction_type


def test_get_dashboard_recipients_data():
    """Test get_dashboard_recipients_data endpoint"""
    from app.routers.dashboard import get_dashboard_recipients_data
    from unittest.mock import patch

    # Mock data
    mock_recipients = [
        {"recipient": "Store A", "total_amount": -300.0, "transaction_count": 15},
        {"recipient": "Store B", "total_amount": -150.0, "transaction_count": 8}
    ]

    with patch('app.routers.dashboard.DataAggregator') as mock_aggregator_class:
        mock_aggregator = MagicMock()
        mock_aggregator_class.return_value = mock_aggregator
        mock_aggregator.get_recipient_aggregation.return_value = mock_recipients

        mock_db = MagicMock()

        result = get_dashboard_recipients_data(
            limit=10,
            transaction_type="expense",
            from_date=None,
            to_date=None,
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None,
            db=mock_db
        )

        assert result == mock_recipients

        # Verify DataAggregator was called correctly
        mock_aggregator.get_recipient_aggregation.assert_called_once_with(
            account_id=None,
            from_date=None,
            to_date=None,
            limit=10,
            transaction_type="expense",
            category_id=None,
            category_ids=None,
            min_amount=None,
            max_amount=None,
            recipient=None,
            purpose=None
        )
