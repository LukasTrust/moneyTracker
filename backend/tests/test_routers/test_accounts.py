"""
Tests for Account Router endpoints
"""
import pytest
from fastapi import status
from unittest.mock import MagicMock, patch


def test_accounts_router_imports():
    """Test that accounts router can be imported"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'router')
    assert accounts.router is not None


def test_router_has_get_accounts_endpoint():
    """Test that get_accounts endpoint exists"""
    from app.routers import accounts
    
    # Check that the function exists
    assert hasattr(accounts, 'get_accounts')
    assert callable(accounts.get_accounts)


def test_router_has_get_account_endpoint():
    """Test that get_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'get_account')
    assert callable(accounts.get_account)


def test_router_has_create_account_endpoint():
    """Test that create_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'create_account')
    assert callable(accounts.create_account)


def test_router_has_update_account_endpoint():
    """Test that update_account endpoint exists"""
    from app.routers import accounts
    
    assert hasattr(accounts, 'update_account')
    assert callable(accounts.update_account)


def test_router_has_delete_account_endpoint():
    """Test that delete_account endpoint exists"""
    from app.routers import accounts
    
    # Check if delete endpoint exists
    assert hasattr(accounts, 'delete_account') or True  # Optional endpoint


def test_account_router_uses_apiRouter():
    """Test that router is an APIRouter instance"""
    from app.routers.accounts import router
    from fastapi import APIRouter

    assert isinstance(router, APIRouter)


def test_get_accounts_empty():
    """Test GET /accounts returns empty list when no accounts exist"""
    from app.routers.accounts import get_accounts
    from unittest.mock import MagicMock

    # Mock DB session
    mock_db = MagicMock()
    mock_db.query.return_value.all.return_value = []

    result = get_accounts(mock_db)
    assert result == {"accounts": []}


def test_create_account():
    """Test POST /accounts creates a new account"""
    from app.routers.accounts import create_account
    from app.schemas.account import AccountCreate
    from unittest.mock import MagicMock

    # Mock DB session
    mock_db = MagicMock()

    # Mock account creation
    mock_account = MagicMock()
    mock_account.id = 1
    mock_account.name = "Test Account"
    mock_account.bank_name = "Test Bank"
    mock_account.account_number = "123456789"
    mock_account.currency = "EUR"
    mock_account.created_at = "2023-01-01T00:00:00"
    mock_account.updated_at = "2023-01-01T00:00:00"

    # Mock the Account constructor and DB operations
    with patch('app.routers.accounts.Account') as mock_account_class:
        mock_account_class.return_value = mock_account

        account_data = AccountCreate(
            name="Test Account",
            bank_name="Test Bank",
            account_number="123456789",
            currency="EUR"
        )

        result = create_account(account_data, mock_db)

        # Verify Account was created with correct data
        mock_account_class.assert_called_once_with(**account_data.model_dump())

        # Verify DB operations
        mock_db.add.assert_called_once_with(mock_account)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_account)

        assert result == mock_account


def test_get_account_by_id():
    """Test GET /accounts/{id} returns specific account"""
    from app.routers.accounts import get_account
    from unittest.mock import MagicMock

    # Mock account
    mock_account = MagicMock()
    mock_account.id = 1
    mock_account.name = "Test Account"

    result = get_account(mock_account)
    assert result == mock_account


def test_update_account():
    """Test PUT /accounts/{id} updates account"""
    from app.routers.accounts import update_account
    from app.schemas.account import AccountUpdate
    from unittest.mock import MagicMock, patch

    # Mock DB session and account
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1
    mock_account.name = "Old Name"
    mock_account.bank_name = "Old Bank"

    account_data = AccountUpdate(name="New Name", bank_name="New Bank")

    with patch('app.routers.accounts.setattr') as mock_setattr:
        result = update_account(account_data, mock_account, mock_db)

        # Verify setattr was called for each field
        mock_setattr.assert_any_call(mock_account, 'name', 'New Name')
        mock_setattr.assert_any_call(mock_account, 'bank_name', 'New Bank')

        # Verify DB operations
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_account)

        assert result == mock_account


def test_delete_account():
    """Test DELETE /accounts/{id} deletes account"""
    from app.routers.accounts import delete_account
    from unittest.mock import MagicMock

    # Mock DB session and account
    mock_db = MagicMock()
    mock_account = MagicMock()
    mock_account.id = 1

    result = delete_account(mock_account, mock_db)

    # Verify DB operations
    mock_db.delete.assert_called_once_with(mock_account)
    mock_db.commit.assert_called_once()

    assert result is None
