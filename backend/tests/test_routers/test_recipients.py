"""
Tests for Recipients Router endpoints
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


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


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_recipients(mock_get_db):
    """Test get_recipients endpoint"""
    from app.routers.recipients import get_recipients
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipients
    mock_recipient1 = MagicMock()
    mock_recipient1.to_dict.return_value = {"id": 1, "name": "Test Recipient 1"}
    mock_recipient2 = MagicMock()
    mock_recipient2.to_dict.return_value = {"id": 2, "name": "Test Recipient 2"}
    
    # Mock query chain - need to properly chain the methods
    mock_query = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()
    mock_limit.all.return_value = [mock_recipient1, mock_recipient2]
    mock_offset.limit.return_value = mock_limit
    mock_query.offset.return_value = mock_offset
    mock_query.order_by.return_value = mock_query  # For sorting
    mock_db.query.return_value = mock_query
    
    # Call function
    result = await get_recipients(limit=10, offset=0, search=None, sort_by="transaction_count", sort_order="desc", db=mock_db)
    
    # Verify DB query was called
    mock_db.query.assert_called_once()
    mock_query.offset.assert_called_once_with(0)
    mock_offset.limit.assert_called_once_with(10)
    mock_limit.all.assert_called_once()
    
    # Verify result
    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Test Recipient 1"}
    assert result[1] == {"id": 2, "name": "Test Recipient 2"}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_recipients_with_search(mock_get_db):
    """Test get_recipients endpoint with search"""
    from app.routers.recipients import get_recipients
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.to_dict.return_value = {"id": 1, "name": "Test Recipient"}
    
    # Mock query chain with filter - properly chain the methods
    mock_query = MagicMock()
    mock_filtered_query = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()
    mock_limit.all.return_value = [mock_recipient]
    mock_offset.limit.return_value = mock_limit
    mock_filtered_query.offset.return_value = mock_offset
    mock_filtered_query.order_by.return_value = mock_filtered_query  # For sorting
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function with search
    result = await get_recipients(search="test", limit=100, offset=0, sort_by="transaction_count", sort_order="desc", db=mock_db)
    
    # Verify filter was applied
    mock_query.filter.assert_called_once()
    
    # Verify result
    assert len(result) == 1
    assert result[0] == {"id": 1, "name": "Test Recipient"}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_top_recipients(mock_get_db):
    """Test get_top_recipients endpoint"""
    from app.routers.recipients import get_top_recipients
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipients
    mock_recipient1 = MagicMock()
    mock_recipient1.to_dict.return_value = {"id": 1, "name": "Top Recipient 1"}
    mock_recipient2 = MagicMock()
    mock_recipient2.to_dict.return_value = {"id": 2, "name": "Top Recipient 2"}
    
    # Mock query chain
    mock_ordered_query = MagicMock()
    mock_ordered_query.limit.return_value.all.return_value = [mock_recipient1, mock_recipient2]
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_ordered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    result = await get_top_recipients(limit=5, db=mock_db)
    
    # Verify DB query was called with order_by and limit
    mock_db.query.assert_called_once()
    mock_query.order_by.assert_called_once()
    mock_ordered_query.limit.assert_called_once_with(5)
    mock_ordered_query.limit.return_value.all.assert_called_once()
    
    # Verify result
    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Top Recipient 1"}
    assert result[1] == {"id": 2, "name": "Top Recipient 2"}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_recipient(mock_get_db):
    """Test get_recipient endpoint"""
    from app.routers.recipients import get_recipient
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.to_dict.return_value = {"id": 1, "name": "Test Recipient"}
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    result = await get_recipient(recipient_id=1, db=mock_db)
    
    # Verify DB query was called
    mock_db.query.assert_called_once()
    mock_query.filter.assert_called_once()
    mock_filtered_query.first.assert_called_once()
    
    # Verify result
    assert result == {"id": 1, "name": "Test Recipient"}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_recipient_not_found(mock_get_db):
    """Test get_recipient endpoint with non-existent recipient"""
    from app.routers.recipients import get_recipient
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query chain returning None
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = None
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_recipient(recipient_id=999, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Recipient with ID 999 not found" in exc_info.value.detail


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_update_recipient(mock_get_db):
    """Test update_recipient endpoint"""
    from app.routers.recipients import update_recipient, RecipientUpdate
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.name = "Old Name"
    mock_recipient.normalized_name = "old name"
    mock_recipient.aliases = "old,alias"
    mock_recipient.to_dict.return_value = {"id": 1, "name": "New Name", "normalized_name": "new name", "aliases": ["new", "alias"]}
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    update_data = RecipientUpdate(name="New Name", aliases=["new", "alias"])
    result = await update_recipient(recipient_id=1, update=update_data, db=mock_db)
    
    # Verify DB operations
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_recipient)
    
    # Verify recipient was updated
    assert mock_recipient.name == "New Name"
    assert mock_recipient.aliases == "new,alias"
    
    # Verify result
    assert result == {"id": 1, "name": "New Name", "normalized_name": "new name", "aliases": ["new", "alias"]}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_update_recipient_not_found(mock_get_db):
    """Test update_recipient endpoint with recipient not found"""
    from app.routers.recipients import update_recipient, RecipientUpdate
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query chain to return None (recipient not found)
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = None
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function and expect HTTPException
    update_data = RecipientUpdate(name="New Name", aliases=["new", "alias"])
    
    with pytest.raises(HTTPException) as exc_info:
        await update_recipient(recipient_id=999, update=update_data, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Recipient with ID 999 not found" in exc_info.value.detail


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_delete_recipient(mock_get_db):
    """Test delete_recipient endpoint"""
    from app.routers.recipients import delete_recipient
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.name = "Test Recipient"
    
    # Mock query chains
    mock_recipient_query = MagicMock()
    mock_recipient_query.filter.return_value.first.return_value = mock_recipient
    mock_data_row_query = MagicMock()
    mock_data_row_query.filter.return_value.update.return_value = None
    
    def mock_query_side_effect(model):
        if model.__name__ == 'Recipient':
            return mock_recipient_query
        elif model.__name__ == 'DataRow':
            return mock_data_row_query
        return MagicMock()
    
    mock_db.query.side_effect = mock_query_side_effect
    
    # Call function
    result = await delete_recipient(recipient_id=1, db=mock_db)
    
    # Verify DB operations
    mock_db.delete.assert_called_once_with(mock_recipient)
    mock_db.commit.assert_called_once()
    
    # Verify data_rows were updated
    mock_data_row_query.filter.assert_called_once()
    mock_data_row_query.filter.return_value.update.assert_called_once_with({"recipient_id": None})
    
    # Verify result
    assert result == {"message": "Recipient 'Test Recipient' deleted successfully"}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_delete_recipient_not_found(mock_get_db):
    """Test delete_recipient endpoint with recipient not found"""
    from app.routers.recipients import delete_recipient
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query chain to return None (recipient not found)
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = None
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await delete_recipient(recipient_id=999, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Recipient with ID 999 not found" in exc_info.value.detail


@patch('app.routers.recipients.RecipientMatcher')
@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_merge_recipients(mock_get_db, mock_matcher_class):
    """Test merge_recipients endpoint"""
    from app.routers.recipients import merge_recipients, MergeRequest
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock matcher
    mock_matcher = MagicMock()
    mock_matcher.merge_recipients.return_value = True
    mock_matcher_class.return_value = mock_matcher
    
    # Mock updated recipient
    mock_recipient = MagicMock()
    mock_recipient.to_dict.return_value = {"id": 1, "name": "Merged Recipient"}
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    merge_request = MergeRequest(keep_id=1, merge_id=2)
    result = await merge_recipients(merge_request=merge_request, db=mock_db)
    
    # Verify matcher was called
    mock_matcher_class.assert_called_once_with(mock_db)
    mock_matcher.merge_recipients.assert_called_once_with(keep_id=1, merge_id=2)
    
    # Verify result
    assert result["message"] == "Recipients merged successfully"
    assert result["recipient"] == {"id": 1, "name": "Merged Recipient"}


@patch('app.routers.recipients.RecipientMatcher')
@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_merge_recipients_failure(mock_get_db, mock_matcher_class):
    """Test merge_recipients endpoint with failure"""
    from app.routers.recipients import merge_recipients, MergeRequest
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock matcher that fails
    mock_matcher = MagicMock()
    mock_matcher.merge_recipients.return_value = False
    mock_matcher_class.return_value = mock_matcher
    
    # Call function and expect HTTPException
    merge_request = MergeRequest(keep_id=1, merge_id=2)
    with pytest.raises(HTTPException) as exc_info:
        await merge_recipients(merge_request=merge_request, db=mock_db)
    
    assert exc_info.value.status_code == 400
    assert "Failed to merge recipients" in exc_info.value.detail


@patch('app.routers.recipients.RecipientMatcher')
@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_merge_suggestions(mock_get_db, mock_matcher_class):
    """Test get_merge_suggestions endpoint"""
    from app.routers.recipients import get_merge_suggestions
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.id = 1
    mock_recipient.name = "Test Recipient"
    
    # Mock similar recipient
    mock_similar_recipient = MagicMock()
    mock_similar_recipient.id = 2
    mock_similar_recipient.to_dict.return_value = {"id": 2, "name": "Similar Recipient"}
    
    # Mock matcher
    mock_matcher = MagicMock()
    mock_matcher.get_recipient_suggestions.return_value = [(mock_similar_recipient, 0.85)]
    mock_matcher_class.return_value = mock_matcher
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    result = await get_merge_suggestions(recipient_id=1, limit=5, db=mock_db)
    
    # Verify matcher was called
    mock_matcher_class.assert_called_once_with(mock_db)
    mock_matcher.get_recipient_suggestions.assert_called_once_with("Test Recipient", limit=6)
    
    # Verify result
    assert len(result) == 1
    assert result[0]["recipient"] == {"id": 2, "name": "Similar Recipient"}
    assert result[0]["similarity"] == 0.85


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_merge_suggestions_not_found(mock_get_db):
    """Test get_merge_suggestions endpoint with recipient not found"""
    from app.routers.recipients import get_merge_suggestions
    from fastapi import HTTPException
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock query chain to return None (recipient not found)
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = None
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await get_merge_suggestions(recipient_id=999, limit=5, db=mock_db)
    
    assert exc_info.value.status_code == 404
    assert "Recipient with ID 999 not found" in exc_info.value.detail


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_update_all_transaction_counts(mock_get_db):
    """Test update_all_transaction_counts endpoint"""
    from app.routers.recipients import update_all_transaction_counts
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipients
    mock_recipient1 = MagicMock()
    mock_recipient1.id = 1
    mock_recipient2 = MagicMock()
    mock_recipient2.id = 2
    
    # Mock data row counts
    mock_data_query = MagicMock()
    mock_data_query.filter.return_value.count.return_value = 5
    
    def mock_query_side_effect(model):
        if model.__name__ == 'Recipient':
            mock_recipient_query = MagicMock()
            mock_recipient_query.all.return_value = [mock_recipient1, mock_recipient2]
            return mock_recipient_query
        elif model.__name__ == 'DataRow':
            return mock_data_query
        return MagicMock()
    
    mock_db.query.side_effect = mock_query_side_effect
    
    # Call function
    result = await update_all_transaction_counts(db=mock_db)
    
    # Verify DB operations
    mock_db.commit.assert_called_once()
    
    # Verify transaction counts were updated
    assert mock_recipient1.transaction_count == 5
    assert mock_recipient2.transaction_count == 5
    
    # Verify result
    assert result["message"] == "Transaction counts updated"
    assert result["updated_count"] == 2


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_recipients_sort_asc(mock_get_db):
    """Test get_recipients endpoint with ascending sort"""
    from app.routers.recipients import get_recipients
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipients
    mock_recipient1 = MagicMock()
    mock_recipient1.to_dict.return_value = {"id": 1, "name": "Test Recipient 1"}
    mock_recipient2 = MagicMock()
    mock_recipient2.to_dict.return_value = {"id": 2, "name": "Test Recipient 2"}
    
    # Mock query chain - need to properly chain the methods
    mock_query = MagicMock()
    mock_offset = MagicMock()
    mock_limit = MagicMock()
    mock_limit.all.return_value = [mock_recipient1, mock_recipient2]
    mock_offset.limit.return_value = mock_limit
    mock_query.offset.return_value = mock_offset
    mock_query.order_by.return_value = mock_query  # For sorting
    mock_db.query.return_value = mock_query
    
    # Call function with asc sort
    result = await get_recipients(limit=10, offset=0, search=None, sort_by="transaction_count", sort_order="asc", db=mock_db)
    
    # Verify DB query was called
    mock_db.query.assert_called_once()
    mock_query.offset.assert_called_once_with(0)
    mock_offset.limit.assert_called_once_with(10)
    mock_limit.all.assert_called_once()
    
    # Verify result
    assert len(result) == 2


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_update_recipient_name_only(mock_get_db):
    """Test update_recipient endpoint with name only (no aliases)"""
    from app.routers.recipients import update_recipient, RecipientUpdate
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.name = "Old Name"
    mock_recipient.normalized_name = "old name"
    mock_recipient.aliases = "old,alias"
    mock_recipient.to_dict.return_value = {"id": 1, "name": "New Name", "normalized_name": "new name", "aliases": ["old", "alias"]}
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function with name only
    update_data = RecipientUpdate(name="New Name", aliases=None)
    result = await update_recipient(recipient_id=1, update=update_data, db=mock_db)
    
    # Verify DB operations
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_recipient)
    
    # Verify recipient name was updated but aliases unchanged
    assert mock_recipient.name == "New Name"
    # Aliases should not be changed since aliases=None means not updating
    assert mock_recipient.aliases == "old,alias"
    
    # Verify result
    assert result == {"id": 1, "name": "New Name", "normalized_name": "new name", "aliases": ["old", "alias"]}


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_delete_recipient_data_row_update(mock_get_db):
    """Test delete_recipient endpoint with proper DataRow update"""
    from app.routers.recipients import delete_recipient
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.name = "Test Recipient"
    
    # Mock query chains
    mock_recipient_query = MagicMock()
    mock_recipient_filtered = MagicMock()
    mock_recipient_filtered.first.return_value = mock_recipient
    mock_recipient_query.filter.return_value = mock_recipient_filtered
    
    mock_data_row_query = MagicMock()
    mock_data_row_filtered = MagicMock()
    mock_data_row_filtered.update.return_value = None
    mock_data_row_query.filter.return_value = mock_data_row_filtered
    
    def mock_query_side_effect(model):
        if hasattr(model, '__name__') and model.__name__ == 'Recipient':
            return mock_recipient_query
        elif hasattr(model, '__name__') and model.__name__ == 'DataRow':
            return mock_data_row_query
        return MagicMock()
    
    mock_db.query.side_effect = mock_query_side_effect
    
    # Call function
    result = await delete_recipient(recipient_id=1, db=mock_db)
    
    # Verify DB operations
    mock_db.delete.assert_called_once_with(mock_recipient)
    mock_db.commit.assert_called_once()
    
    # Verify data_rows were updated
    mock_data_row_query.filter.assert_called_once()
    mock_data_row_filtered.update.assert_called_once_with({"recipient_id": None})
    
    # Verify result
    assert result == {"message": "Recipient 'Test Recipient' deleted successfully"}


@patch('app.routers.recipients.RecipientMatcher')
@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_get_merge_suggestions_matcher_call(mock_get_db, mock_matcher_class):
    """Test get_merge_suggestions endpoint with matcher call"""
    from app.routers.recipients import get_merge_suggestions
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.id = 1
    mock_recipient.name = "Test Recipient"
    
    # Mock similar recipient
    mock_similar_recipient = MagicMock()
    mock_similar_recipient.id = 2
    mock_similar_recipient.to_dict.return_value = {"id": 2, "name": "Similar Recipient"}
    
    # Mock matcher
    mock_matcher = MagicMock()
    mock_matcher.get_recipient_suggestions.return_value = [(mock_similar_recipient, 0.85)]
    mock_matcher_class.return_value = mock_matcher
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function
    result = await get_merge_suggestions(recipient_id=1, limit=5, db=mock_db)
    
    # Verify matcher was instantiated and called
    mock_matcher_class.assert_called_once_with(mock_db)
    mock_matcher.get_recipient_suggestions.assert_called_once_with("Test Recipient", limit=6)
    
    # Verify result
    assert len(result) == 1
    assert result[0]["recipient"] == {"id": 2, "name": "Similar Recipient"}
    assert result[0]["similarity"] == 0.85


@patch('app.routers.recipients.get_db')
@pytest.mark.asyncio
async def test_update_recipient_aliases_only(mock_get_db):
    """Test update_recipient endpoint with aliases only (no name)"""
    from app.routers.recipients import update_recipient, RecipientUpdate
    
    # Mock DB session
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db
    
    # Mock recipient
    mock_recipient = MagicMock()
    mock_recipient.name = "Old Name"
    mock_recipient.normalized_name = "old name"
    mock_recipient.aliases = "old,alias"
    mock_recipient.to_dict.return_value = {"id": 1, "name": "Old Name", "normalized_name": "old name", "aliases": ["new", "alias"]}
    
    # Mock query chain
    mock_filtered_query = MagicMock()
    mock_filtered_query.first.return_value = mock_recipient
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filtered_query
    mock_db.query.return_value = mock_query
    
    # Call function with aliases only
    update_data = RecipientUpdate(name=None, aliases=["new", "alias"])
    result = await update_recipient(recipient_id=1, update=update_data, db=mock_db)
    
    # Verify DB operations
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once_with(mock_recipient)
    
    # Verify recipient name was not changed but aliases were
    assert mock_recipient.name == "Old Name"  # Name unchanged
    assert mock_recipient.aliases == "new,alias"
    
    # Verify result
    assert result == {"id": 1, "name": "Old Name", "normalized_name": "old name", "aliases": ["new", "alias"]}
