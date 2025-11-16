"""
API Routers
"""
from . import accounts
from . import categories
from . import data
from . import dashboard
from . import mappings
from . import csv_import
from . import recipients
from . import budgets
from . import recurring
from . import import_history
from . import transfers

__all__ = [
    "accounts",
    "categories",
    "data",
    "dashboard",
    "mappings",
    "csv_import",
    "recipients",
    "budgets",
    "recurring",
    "import_history",
    "transfers",
]
