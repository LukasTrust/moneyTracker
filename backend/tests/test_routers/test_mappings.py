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


def test_get_mappings():
    """Test GET /{account_id}/mappings returns mappings for account"""
    from app.routers.mappings import get_mappings, Mapping
    from unittest.mock import MagicMock

    # Mock DB session and account
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1

    # Mock mappings
    mock_mapping1 = MagicMock()
    mock_mapping1.account_id = 1
    mock_mapping2 = MagicMock()
    mock_mapping2.account_id = 1

    # Mock DB query to return mappings
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_mapping1, mock_mapping2]

    result = get_mappings(mock_account, mock_db)

    # Verify DB query was called
    mock_db.query.assert_called_once_with(Mapping)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.all.assert_called_once()

    assert result == [mock_mapping1, mock_mapping2]


def test_save_mappings():
    """Test POST /{account_id}/mappings saves mappings"""
    from app.routers.mappings import save_mappings, Mapping
    from app.schemas.mapping import MappingsUpdate, MappingCreate
    from unittest.mock import MagicMock, patch

    # Mock DB session and account
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1

    # Mock mapping data
    mapping_data1 = MappingCreate(csv_header="Date", standard_field="date")
    mapping_data2 = MappingCreate(csv_header="Amount", standard_field="amount")
    mappings_data = MappingsUpdate(mappings=[mapping_data1, mapping_data2])

    # Mock new mappings
    mock_new_mapping1 = MagicMock()
    mock_new_mapping2 = MagicMock()

    with patch('app.routers.mappings.Mapping') as mock_mapping_class:
        mock_mapping_class.side_effect = [mock_new_mapping1, mock_new_mapping2]

        result = save_mappings(mappings_data, mock_account, mock_db)

        # Verify existing mappings were deleted
        mock_db.query.assert_called_once()
        mock_db.query.return_value.filter.assert_called_once()
        mock_db.query.return_value.filter.return_value.delete.assert_called_once()

        # Verify new mappings were created
        assert mock_mapping_class.call_count == 2
        mock_mapping_class.assert_any_call(
            account_id=mock_account.id,
            csv_header="Date",
            standard_field="date"
        )
        mock_mapping_class.assert_any_call(
            account_id=mock_account.id,
            csv_header="Amount",
            standard_field="amount"
        )

        # Verify DB operations
        assert mock_db.add.call_count == 2
        mock_db.add.assert_any_call(mock_new_mapping1)
        mock_db.add.assert_any_call(mock_new_mapping2)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_any_call(mock_new_mapping1)
        mock_db.refresh.assert_any_call(mock_new_mapping2)

        assert result == [mock_new_mapping1, mock_new_mapping2]


def test_delete_mappings():
    """Test DELETE /{account_id}/mappings deletes all mappings"""
    from app.routers.mappings import delete_mappings, Mapping
    from unittest.mock import MagicMock

    # Mock DB session and account
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1

    result = delete_mappings(mock_account, mock_db)

    # Verify mappings were deleted
    mock_db.query.assert_called_once_with(Mapping)
    mock_db.query.return_value.filter.assert_called_once()
    mock_db.query.return_value.filter.return_value.delete.assert_called_once()
    mock_db.commit.assert_called_once()

    assert result is None
