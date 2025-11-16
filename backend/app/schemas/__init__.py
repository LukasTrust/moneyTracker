"""
Pydantic Schemas for Request/Response Validation
"""
from .account import (
    AccountBase,
    AccountCreate,
    AccountUpdate,
    AccountResponse,
    AccountListResponse
)
from .category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryMappings
)
from .data_row import (
    DataRowResponse,
    DataRowListResponse
)
from .mapping import (
    MappingBase,
    MappingCreate,
    MappingResponse,
    MappingsUpdate
)
from .statistics import (
    SummaryResponse,
    StatisticsResponse,
    ChartDataResponse,
    CategoryDataResponse,
    RecipientDataResponse,
    BalanceHistoryResponse
)
from .recurring_transaction import (
    RecurringTransactionResponse,
    RecurringTransactionListResponse,
    RecurringTransactionStats,
    RecurringTransactionDetectionStats,
    RecurringTransactionUpdate,
    RecurringTransactionToggleRequest
)
from .import_history import (
    ImportHistoryBase,
    ImportHistoryCreate,
    ImportHistoryUpdate,
    ImportHistoryResponse,
    ImportHistoryStats,
    ImportHistoryListResponse,
    ImportRollbackRequest,
    ImportRollbackResponse
)
from .transfer import (
    TransferBase,
    TransferCreate,
    TransferUpdate,
    TransferResponse,
    TransferWithDetails,
    TransferCandidate,
    TransferDetectionRequest,
    TransferDetectionResponse,
    TransferStats
)

__all__ = [
    # Account
    "AccountBase",
    "AccountCreate",
    "AccountUpdate",
    "AccountResponse",
    "AccountListResponse",
    # Category
    "CategoryBase",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryMappings",
    # DataRow
    "DataRowResponse",
    "DataRowListResponse",
    # Mapping
    "MappingBase",
    "MappingCreate",
    "MappingResponse",
    "MappingsUpdate",
    # Statistics
    "SummaryResponse",
    "StatisticsResponse",
    "ChartDataResponse",
    "CategoryDataResponse",
    "RecipientDataResponse",
    "BalanceHistoryResponse",
    # Recurring Transactions
    "RecurringTransactionResponse",
    "RecurringTransactionListResponse",
    "RecurringTransactionStats",
    "RecurringTransactionDetectionStats",
    "RecurringTransactionUpdate",
    "RecurringTransactionToggleRequest",
    # Import History
    "ImportHistoryBase",
    "ImportHistoryCreate",
    "ImportHistoryUpdate",
    "ImportHistoryResponse",
    "ImportHistoryStats",
    "ImportHistoryListResponse",
    "ImportRollbackRequest",
    "ImportRollbackResponse",
    # Transfers
    "TransferBase",
    "TransferCreate",
    "TransferUpdate",
    "TransferResponse",
    "TransferWithDetails",
    "TransferCandidate",
    "TransferDetectionRequest",
    "TransferDetectionResponse",
    "TransferStats",
]
