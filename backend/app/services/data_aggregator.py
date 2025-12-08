"""
Data Aggregator - Aggregate transaction data for statistics and charts
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import calendar

from app.models.data_row import DataRow
from app.models.category import Category
from app.models.transfer import Transfer
from app.models.account import Account


class DataAggregator:
    """
    Service for aggregating transaction data
    """
    
    def __init__(self, db: Session):
        """
        Initialize with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def _get_transfer_transaction_ids(self) -> Set[int]:
        """
        Get set of all transaction IDs that are part of transfers.
        These should be excluded from income/expense calculations.
        
        Returns:
            Set of transaction IDs involved in transfers
        """
        transfer_ids = set()
        
        # Get all from_transaction_ids
        from_ids = self.db.query(Transfer.from_transaction_id).all()
        transfer_ids.update([tid[0] for tid in from_ids])
        
        # Get all to_transaction_ids
        to_ids = self.db.query(Transfer.to_transaction_id).all()
        transfer_ids.update([tid[0] for tid in to_ids])
        
        return transfer_ids
    
    @staticmethod
    def parse_amount(amount_str: str) -> float:
        """
        Parse amount string to float, handling German and English formats
        
        Args:
            amount_str: Amount as string (e.g., "-50,00", "-50.00", "1.234,56")
            
        Returns:
            Parsed amount as float
        """
        if not amount_str:
            return 0.0
        
        # Convert to string if not already
        amount_str = str(amount_str).strip()
        
        # Remove currency symbols and whitespace
        amount_str = amount_str.replace('€', '').replace('$', '').strip()
        
        # Check if German format (comma as decimal separator)
        if ',' in amount_str and '.' in amount_str:
            # Format like "1.234,56" - remove thousands separator, replace comma
            amount_str = amount_str.replace('.', '').replace(',', '.')
        elif ',' in amount_str:
            # Format like "-50,00" - replace comma with dot
            amount_str = amount_str.replace(',', '.')
        
        try:
            return float(amount_str)
        except (ValueError, TypeError):
            return 0.0
    
    def get_summary(
        self,
        account_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        category_id: Optional[int] = None,
        category_ids: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        recipient: Optional[str] = None,
        purpose: Optional[str] = None,
        transaction_type: Optional[str] = None,
        uncategorized: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics (income, expenses, balance, count)
        
        REFACTORED: Uses direct column access instead of json_extract()
        
        Args:
            account_id: Filter by account ID (None for all accounts)
            from_date: Start date filter
            to_date: End date filter
            category_id: Filter by single category ID (None for all categories)
            category_ids: Filter by multiple categories (comma-separated, OR logic)
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            recipient: Recipient search query
            purpose: Purpose search query
            transaction_type: Filter by type ('income', 'expense', 'all')
            
        Returns:
            Dictionary with summary statistics
        """
        # Use SQL aggregation for better performance
        from sqlalchemy import case, cast, Float
        
        # Exclude transfers from calculations
        transfer_ids = self._get_transfer_transaction_ids()
        
        query = self.db.query(
            func.sum(case((DataRow.amount > 0, DataRow.amount), else_=0)).label('total_income'),
            func.sum(case((DataRow.amount < 0, DataRow.amount), else_=0)).label('total_expenses'),
            func.sum(DataRow.amount).label('net_balance'),
            func.count(DataRow.id).label('transaction_count')
        )
        
        # Exclude transfer transactions
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        # Apply uncategorized filter (takes precedence over category filters)
        if uncategorized:
            query = query.filter(DataRow.category_id.is_(None))
        # Apply category filter (support both single and multiple)
        elif category_ids:
            try:
                cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                if cat_id_list:
                    if -1 in cat_id_list:
                        other_cats = [cid for cid in cat_id_list if cid != -1]
                        if other_cats:
                            query = query.filter(
                                or_(
                                    DataRow.category_id.is_(None),
                                    DataRow.category_id.in_(other_cats)
                                )
                            )
                        else:
                            query = query.filter(DataRow.category_id.is_(None))
                    else:
                        query = query.filter(DataRow.category_id.in_(cat_id_list))
            except (ValueError, AttributeError):
                pass
        elif category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
        # Apply amount filters
        if min_amount is not None:
            query = query.filter(DataRow.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(DataRow.amount <= max_amount)
        
        # Apply recipient filter
        if recipient:
            query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
        
        # Apply purpose filter
        if purpose:
            query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
        
        # Apply transaction type filter
        if transaction_type and transaction_type != 'all':
            if transaction_type == 'income':
                query = query.filter(DataRow.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(DataRow.amount < 0)
        
        # Execute query
        result = query.first()
        # Determine effective to_date for current balance calculation:
        # - if `to_date` provided, use it
        # - else if there are any transactions matching filters, use the latest transaction date
        # - otherwise use today
        effective_to_date = to_date
        if not effective_to_date:
            # find latest transaction date matching non-date filters
            latest_q = self.db.query(func.max(DataRow.transaction_date).label('latest'))
            # Exclude transfers
            if transfer_ids:
                latest_q = latest_q.filter(~DataRow.id.in_(transfer_ids))
            if account_id:
                latest_q = latest_q.filter(DataRow.account_id == account_id)
            if category_ids:
                try:
                    cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                    if cat_id_list:
                        if -1 in cat_id_list:
                            other_cats = [cid for cid in cat_id_list if cid != -1]
                            if other_cats:
                                latest_q = latest_q.filter(
                                    or_(
                                        DataRow.category_id.is_(None),
                                        DataRow.category_id.in_(other_cats)
                                    )
                                )
                            else:
                                latest_q = latest_q.filter(DataRow.category_id.is_(None))
                        else:
                            latest_q = latest_q.filter(DataRow.category_id.in_(cat_id_list))
                except Exception:
                    pass
            elif category_id is not None:
                if category_id == -1:
                    latest_q = latest_q.filter(DataRow.category_id.is_(None))
                else:
                    latest_q = latest_q.filter(DataRow.category_id == category_id)
            if min_amount is not None:
                latest_q = latest_q.filter(DataRow.amount >= min_amount)
            if max_amount is not None:
                latest_q = latest_q.filter(DataRow.amount <= max_amount)
            if recipient:
                latest_q = latest_q.filter(DataRow.recipient.ilike(f"%{recipient}%"))
            if purpose:
                latest_q = latest_q.filter(DataRow.purpose.ilike(f"%{purpose}%"))
            if transaction_type and transaction_type != 'all':
                if transaction_type == 'income':
                    latest_q = latest_q.filter(DataRow.amount > 0)
                elif transaction_type == 'expense':
                    latest_q = latest_q.filter(DataRow.amount < 0)

            latest_res = latest_q.first()
            latest_date = latest_res.latest if latest_res is not None else None
            effective_to_date = latest_date or date.today()

        # Sum of transactions up to effective_to_date (inclusive)
        tx_q = self.db.query(func.sum(DataRow.amount).label('sum_up_to'))
        if transfer_ids:
            tx_q = tx_q.filter(~DataRow.id.in_(transfer_ids))
        if account_id:
            tx_q = tx_q.filter(DataRow.account_id == account_id)
        # apply same category/account/recipient/purpose/amount filters
        if category_ids:
            try:
                cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                if cat_id_list:
                    if -1 in cat_id_list:
                        other_cats = [cid for cid in cat_id_list if cid != -1]
                        if other_cats:
                            tx_q = tx_q.filter(
                                or_(
                                    DataRow.category_id.is_(None),
                                    DataRow.category_id.in_(other_cats)
                                )
                            )
                        else:
                            tx_q = tx_q.filter(DataRow.category_id.is_(None))
                    else:
                        tx_q = tx_q.filter(DataRow.category_id.in_(cat_id_list))
            except Exception:
                pass
        elif category_id is not None:
            if category_id == -1:
                tx_q = tx_q.filter(DataRow.category_id.is_(None))
            else:
                tx_q = tx_q.filter(DataRow.category_id == category_id)
        if min_amount is not None:
            tx_q = tx_q.filter(DataRow.amount >= min_amount)
        if max_amount is not None:
            tx_q = tx_q.filter(DataRow.amount <= max_amount)
        if recipient:
            tx_q = tx_q.filter(DataRow.recipient.ilike(f"%{recipient}%"))
        if purpose:
            tx_q = tx_q.filter(DataRow.purpose.ilike(f"%{purpose}%"))
        if transaction_type and transaction_type != 'all':
            if transaction_type == 'income':
                tx_q = tx_q.filter(DataRow.amount > 0)
            elif transaction_type == 'expense':
                tx_q = tx_q.filter(DataRow.amount < 0)

        # Date upper bound
        tx_q = tx_q.filter(DataRow.transaction_date <= effective_to_date)
        tx_res = tx_q.first()
        sum_up_to = float(tx_res.sum_up_to or 0)

        # Sum initial balances for accounts in scope
        init_sum = 0.0
        try:
            init_q = self.db.query(func.sum(Account.initial_balance).label('init_sum'))
            if account_id:
                init_q = init_q.filter(Account.id == account_id)
            init_res = init_q.first()
            init_sum = float(init_res.init_sum or 0)
        except Exception:
            init_sum = 0.0

        # current_balance = initial balances + sum of transactions up to effective_to_date
        current_balance = round(init_sum + sum_up_to, 2)

        return {
            'total_income': round(float(result.total_income or 0), 2),
            'total_expenses': round(float(result.total_expenses or 0), 2),
            'current_balance': current_balance,
            'transaction_count': result.transaction_count or 0
        }
    
    def get_category_aggregation(
        self,
        account_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 10,
        category_id: Optional[int] = None,
        category_ids: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        recipient: Optional[str] = None,
        purpose: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated data by category
        
        REFACTORED: Uses SQL aggregation instead of Python loops
        
        Args:
            account_id: Filter by account ID (None for all accounts)
            from_date: Start date filter
            to_date: End date filter
            limit: Maximum number of categories to return
            category_id: Filter by specific category ID
            category_ids: Filter by multiple categories (comma-separated)
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            recipient: Recipient search query
            purpose: Purpose search query
            transaction_type: Filter by type ('income', 'expense', 'all')
            
        Returns:
            List of category aggregations
        """
        from sqlalchemy import case
        
        # Exclude transfers from calculations
        transfer_ids = self._get_transfer_transaction_ids()
        
        # Build aggregation query
        query = self.db.query(
            DataRow.category_id,
            func.sum(DataRow.amount).label('total_amount'),
            func.count(DataRow.id).label('count')
        )
        
        # Exclude transfer transactions
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        # Apply category filter (when filtering specific categories in aggregation)
        if category_ids:
            try:
                cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                if cat_id_list:
                    if -1 in cat_id_list:
                        other_cats = [cid for cid in cat_id_list if cid != -1]
                        if other_cats:
                            query = query.filter(
                                or_(
                                    DataRow.category_id.is_(None),
                                    DataRow.category_id.in_(other_cats)
                                )
                            )
                        else:
                            query = query.filter(DataRow.category_id.is_(None))
                    else:
                        query = query.filter(DataRow.category_id.in_(cat_id_list))
            except (ValueError, AttributeError):
                pass
        elif category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
        # Apply amount filters
        if min_amount is not None:
            query = query.filter(DataRow.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(DataRow.amount <= max_amount)
        
        # Apply recipient filter
        if recipient:
            query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
        
        # Apply purpose filter
        if purpose:
            query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
        
        # Apply transaction type filter
        if transaction_type and transaction_type != 'all':
            if transaction_type == 'income':
                query = query.filter(DataRow.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(DataRow.amount < 0)
        
        # Group by category and order by absolute amount (descending)
        query = query.group_by(DataRow.category_id)
        query = query.order_by(func.abs(func.sum(DataRow.amount)).desc())
        query = query.limit(limit)
        
        # Execute query
        results = query.all()
        
        # Calculate total for percentage
        total_query = self.db.query(
            func.sum(func.abs(DataRow.amount))
        )
        if account_id:
            total_query = total_query.filter(DataRow.account_id == account_id)
        if from_date:
            total_query = total_query.filter(DataRow.transaction_date >= from_date)
        if to_date:
            total_query = total_query.filter(DataRow.transaction_date <= to_date)
        
        total_absolute = float(total_query.scalar() or 0)
        
        # Get category details
        category_ids = [r.category_id for r in results if r.category_id]
        categories = {c.id: c for c in self.db.query(Category).filter(Category.id.in_(category_ids)).all()}
        
        # Build result
        result = []
        for row in results:
            category_id = row.category_id
            
            if category_id is None:
                category_info = {
                    'id': None,
                    'name': 'Unkategorisiert',
                    'color': '#9ca3af',
                    'icon': '❓'
                }
            else:
                category = categories.get(category_id)
                if not category:
                    continue
                category_info = {
                    'id': category.id,
                    'name': category.name,
                    'color': category.color,
                    'icon': category.icon
                }
            
            total_amount = float(row.total_amount or 0)
            percentage = (abs(total_amount) / total_absolute * 100) if total_absolute > 0 else 0
            
            result.append({
                'category_id': category_info['id'],
                'category_name': category_info['name'],
                'color': category_info['color'],
                'icon': category_info['icon'],
                'total_amount': round(total_amount, 2),
                'transaction_count': row.count,
                'percentage': round(percentage, 2)
            })
        
        return result
    
    def get_recipient_aggregation(
        self,
        account_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 10,
        transaction_type: str = 'all',
        category_id: Optional[int] = None,
        category_ids: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        recipient: Optional[str] = None,
        purpose: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated data by recipient
        
        Args:
            account_id: Filter by account ID
            from_date: Start date filter
            to_date: End date filter
            limit: Maximum number of recipients to return
            transaction_type: Filter by transaction type ('all', 'income', 'expense')
            category_id: Filter by single category ID
            category_ids: Filter by multiple categories (comma-separated)
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            recipient: Recipient search query
            purpose: Purpose search query
            
        Returns:
            List of recipient aggregations
        """
        # Exclude transfers from calculations
        transfer_ids = self._get_transfer_transaction_ids()
        
        query = self.db.query(DataRow)
        
        # Exclude transfer transactions
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        # Filter by category
        if category_ids:
            try:
                cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                if cat_id_list:
                    if -1 in cat_id_list:
                        other_cats = [cid for cid in cat_id_list if cid != -1]
                        if other_cats:
                            query = query.filter(
                                or_(
                                    DataRow.category_id.is_(None),
                                    DataRow.category_id.in_(other_cats)
                                )
                            )
                        else:
                            query = query.filter(DataRow.category_id.is_(None))
                    else:
                        query = query.filter(DataRow.category_id.in_(cat_id_list))
            except (ValueError, AttributeError):
                pass
        elif category_id is not None:
            query = query.filter(DataRow.category_id == category_id)
        
        # Apply amount filters
        if min_amount is not None:
            query = query.filter(DataRow.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(DataRow.amount <= max_amount)
        
        # Apply recipient filter
        if recipient:
            query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
        
        # Apply purpose filter
        if purpose:
            query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
        
        # Apply transaction type filter (before aggregation)
        if transaction_type and transaction_type != 'all':
            if transaction_type == 'income':
                query = query.filter(DataRow.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(DataRow.amount < 0)
        
        # Get all transactions
        transactions = query.all()
        
        # Aggregate by recipient
        recipient_data = defaultdict(lambda: {
            'total_amount': 0.0,
            'count': 0,
            'category_id': None,
            'category_name': None
        })
        total_absolute = 0.0
        
        for transaction in transactions:
            # Use structured fields (refactored model)
            recipient_name = transaction.recipient or 'Unbekannt'
            if not recipient_name.strip():
                recipient_name = 'Unbekannt'
            
            amount = float(transaction.amount or 0)
            
            recipient_data[recipient_name]['total_amount'] += amount
            recipient_data[recipient_name]['count'] += 1
            total_absolute += abs(amount)
            
            # Store category info (use first occurrence)
            if transaction.category_id and not recipient_data[recipient_name]['category_id']:
                category = self.db.query(Category).filter(
                    Category.id == transaction.category_id
                ).first()
                if category:
                    recipient_data[recipient_name]['category_id'] = category.id
                    recipient_data[recipient_name]['category_name'] = category.name
        
        # Build result
        result = []
        for recipient, data in recipient_data.items():
            percentage = (abs(data['total_amount']) / total_absolute * 100) if total_absolute > 0 else 0
            
            result.append({
                'recipient': recipient,
                'total_amount': round(data['total_amount'], 2),
                'transaction_count': data['count'],
                'percentage': round(percentage, 2),
                'category_id': data['category_id'],
                'category_name': data['category_name']
            })
        
        # Sort by absolute amount
        result.sort(key=lambda x: abs(x['total_amount']), reverse=True)
        
        return result[:limit]
    
    def get_balance_history(
        self,
        account_id: Optional[int] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        group_by: str = 'month',
        category_id: Optional[int] = None,
        category_ids: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        recipient: Optional[str] = None,
        purpose: Optional[str] = None,
        transaction_type: Optional[str] = None,
        uncategorized: Optional[bool] = None
    ) -> Dict[str, List]:
        """
        Get balance history grouped by time period
        
        REFACTORED: Uses SQL strftime for date grouping (much faster!)
        
        Args:
            account_id: Filter by account ID
            from_date: Start date filter
            to_date: End date filter
            group_by: Grouping period ('day', 'month', 'year')
            category_id: Filter by single category ID
            category_ids: Filter by multiple categories (comma-separated)
            min_amount: Minimum amount filter
            max_amount: Maximum amount filter
            recipient: Recipient search query
            purpose: Purpose search query
            transaction_type: Filter by type ('income', 'expense', 'all')
            
        Returns:
            Dictionary with labels, income, expenses, balance arrays
        """
        from sqlalchemy import case
        
        # Exclude transfers from calculations
        transfer_ids = self._get_transfer_transaction_ids()
        
        # Define grouping format based on group_by
        if group_by == 'day':
            date_format = '%Y-%m-%d'
        elif group_by == 'year':
            date_format = '%Y'
        else:  # month (default)
            date_format = '%Y-%m'
        
        # Build aggregation query using SQL strftime
        query = self.db.query(
            func.strftime(date_format, DataRow.transaction_date).label('period'),
            func.sum(case((DataRow.amount > 0, DataRow.amount), else_=0)).label('income'),
            func.sum(case((DataRow.amount < 0, DataRow.amount), else_=0)).label('expenses')
        )
        
        # Exclude transfer transactions
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        # Apply uncategorized filter (takes precedence over category filters)
        if uncategorized:
            query = query.filter(DataRow.category_id.is_(None))
        # Apply category filter
        elif category_ids:
            try:
                cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                if cat_id_list:
                    if -1 in cat_id_list:
                        other_cats = [cid for cid in cat_id_list if cid != -1]
                        if other_cats:
                            query = query.filter(
                                or_(
                                    DataRow.category_id.is_(None),
                                    DataRow.category_id.in_(other_cats)
                                )
                            )
                        else:
                            query = query.filter(DataRow.category_id.is_(None))
                    else:
                        query = query.filter(DataRow.category_id.in_(cat_id_list))
            except (ValueError, AttributeError):
                pass
        elif category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
        # Apply amount filters
        if min_amount is not None:
            query = query.filter(DataRow.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(DataRow.amount <= max_amount)
        
        # Apply recipient filter
        if recipient:
            query = query.filter(DataRow.recipient.ilike(f"%{recipient}%"))
        
        # Apply purpose filter
        if purpose:
            query = query.filter(DataRow.purpose.ilike(f"%{purpose}%"))
        
        # Apply transaction type filter
        if transaction_type and transaction_type != 'all':
            if transaction_type == 'income':
                query = query.filter(DataRow.amount > 0)
            elif transaction_type == 'expense':
                query = query.filter(DataRow.amount < 0)
        
        # Group by period and order chronologically
        query = query.group_by('period').order_by('period')
        
        # Execute query
        results = query.all()
        
        # Build response arrays
        labels = []
        income = []
        expenses = []
        balance = []

        # Compute opening balance (sum of all transactions before from_date)
        opening_balance = 0.0
        if from_date:
            open_query = self.db.query(
                func.sum(DataRow.amount).label('opening_net')
            )

            # Exclude transfer transactions
            if transfer_ids:
                open_query = open_query.filter(~DataRow.id.in_(transfer_ids))

            # Apply same non-date filters as above
            if account_id:
                open_query = open_query.filter(DataRow.account_id == account_id)

            open_query = open_query.filter(DataRow.transaction_date < from_date)

            if category_ids:
                try:
                    cat_id_list = [int(cid.strip()) for cid in category_ids.split(',') if cid.strip()]
                    if cat_id_list:
                        if -1 in cat_id_list:
                            other_cats = [cid for cid in cat_id_list if cid != -1]
                            if other_cats:
                                open_query = open_query.filter(
                                    or_(
                                        DataRow.category_id.is_(None),
                                        DataRow.category_id.in_(other_cats)
                                    )
                                )
                            else:
                                open_query = open_query.filter(DataRow.category_id.is_(None))
                        else:
                            open_query = open_query.filter(DataRow.category_id.in_(cat_id_list))
                except (ValueError, AttributeError):
                    pass
            elif category_id is not None:
                if category_id == -1:
                    open_query = open_query.filter(DataRow.category_id.is_(None))
                else:
                    open_query = open_query.filter(DataRow.category_id == category_id)

            # Amount filters
            if min_amount is not None:
                open_query = open_query.filter(DataRow.amount >= min_amount)

            if max_amount is not None:
                open_query = open_query.filter(DataRow.amount <= max_amount)

            # Recipient / purpose filters
            if recipient:
                open_query = open_query.filter(DataRow.recipient.ilike(f"%{recipient}%"))

            if purpose:
                open_query = open_query.filter(DataRow.purpose.ilike(f"%{purpose}%"))

            # Transaction type
            if transaction_type and transaction_type != 'all':
                if transaction_type == 'income':
                    open_query = open_query.filter(DataRow.amount > 0)
                elif transaction_type == 'expense':
                    open_query = open_query.filter(DataRow.amount < 0)

            opening_result = open_query.first()
            opening_balance = float(opening_result.opening_net or 0)

        # Include account initial balances into opening_balance so the graph starts
        # from the real account starting value (if account filter applied, limit to that account)
        try:
            init_q = self.db.query(func.sum(Account.initial_balance).label('init_sum'))
            if account_id:
                init_q = init_q.filter(Account.id == account_id)
            init_res = init_q.first()
            init_sum = float(init_res.init_sum or 0)
            opening_balance += init_sum
        except Exception:
            # If account table not available or any error occurs, keep opening_balance as-is
            pass

        cumulative = opening_balance
        
        for row in results:
            period = row.period
            
            # Format label based on grouping
            if group_by == 'month' and period:
                try:
                    year, month = period.split('-')
                    month_name = calendar.month_abbr[int(month)]
                    label = f"{month_name} {year}"
                except:
                    label = period
            else:
                label = period or 'Unknown'
            
            labels.append(label)
            
            period_income = float(row.income or 0)
            period_expenses = float(row.expenses or 0)
            
            income.append(round(period_income, 2))
            expenses.append(round(period_expenses, 2))
            
            cumulative += period_income + period_expenses
            balance.append(round(cumulative, 2))
        
        return {
            'labels': labels,
            'income': income,
            'expenses': expenses,
            'balance': balance
        }
    
    def get_period_comparison(
        self,
        account_id: int,
        period1_start: date,
        period1_end: date,
        period2_start: date,
        period2_end: date,
        top_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Compare two time periods with comprehensive statistics
        
        Args:
            account_id: Account ID to compare
            period1_start: Start date of first period
            period1_end: End date of first period
            period2_start: Start date of second period
            period2_end: End date of second period
            top_limit: Number of top recipients to include
            
        Returns:
            Dictionary with comparison data for both periods
        """
        # Get data for period 1
        period1_summary = self.get_summary(
            account_id=account_id,
            from_date=period1_start,
            to_date=period1_end
        )
        
        period1_categories = self.get_category_aggregation(
            account_id=account_id,
            from_date=period1_start,
            to_date=period1_end,
            limit=20
        )
        
        period1_recipients = self.get_recipient_aggregation(
            account_id=account_id,
            from_date=period1_start,
            to_date=period1_end,
            limit=top_limit,
            transaction_type='all'
        )
        
        # Get data for period 2
        period2_summary = self.get_summary(
            account_id=account_id,
            from_date=period2_start,
            to_date=period2_end
        )
        
        period2_categories = self.get_category_aggregation(
            account_id=account_id,
            from_date=period2_start,
            to_date=period2_end,
            limit=20
        )
        
        period2_recipients = self.get_recipient_aggregation(
            account_id=account_id,
            from_date=period2_start,
            to_date=period2_end,
            limit=top_limit,
            transaction_type='all'
        )
        
        # Calculate comparison metrics
        def calculate_percent_change(old_val: float, new_val: float) -> float:
            """Calculate percentage change, handling zero values"""
            if old_val == 0:
                return 100.0 if new_val != 0 else 0.0
            return round(((new_val - old_val) / abs(old_val)) * 100, 2)
        
        comparison = {
            'income_diff': round(period2_summary['total_income'] - period1_summary['total_income'], 2),
            'income_diff_percent': calculate_percent_change(
                period1_summary['total_income'],
                period2_summary['total_income']
            ),
            'expenses_diff': round(period2_summary['total_expenses'] - period1_summary['total_expenses'], 2),
            'expenses_diff_percent': calculate_percent_change(
                abs(period1_summary['total_expenses']),
                abs(period2_summary['total_expenses'])
            ),
            # Use current_balance (opening + net in period) when available
            'balance_diff': round(
                (period2_summary.get('current_balance', period2_summary.get('net_balance', 0)) -
                 period1_summary.get('current_balance', period1_summary.get('net_balance', 0)))
            , 2),
            'balance_diff_percent': calculate_percent_change(
                period1_summary.get('current_balance', period1_summary.get('net_balance', 0)),
                period2_summary.get('current_balance', period2_summary.get('net_balance', 0))
            ),
            'transaction_count_diff': period2_summary['transaction_count'] - period1_summary['transaction_count']
        }
        
        # Format period labels
        period1_label = self._format_period_label(period1_start, period1_end)
        period2_label = self._format_period_label(period2_start, period2_end)
        
        return {
            'period1': {
                'period_label': period1_label,
                'total_income': period1_summary['total_income'],
                'total_expenses': period1_summary['total_expenses'],
                'current_balance': period1_summary.get('current_balance', period1_summary.get('net_balance', 0)),
                'transaction_count': period1_summary['transaction_count'],
                'categories': period1_categories,
                'top_recipients': period1_recipients
            },
            'period2': {
                'period_label': period2_label,
                'total_income': period2_summary['total_income'],
                'total_expenses': period2_summary['total_expenses'],
                'current_balance': period2_summary.get('current_balance', period2_summary.get('net_balance', 0)),
                'transaction_count': period2_summary['transaction_count'],
                'categories': period2_categories,
                'top_recipients': period2_recipients
            },
            'comparison': comparison
        }
    
    @staticmethod
    def _format_period_label(start_date: date, end_date: date) -> str:
        """
        Format a period label based on start and end dates
        
        Args:
            start_date: Period start date
            end_date: Period end date
            
        Returns:
            Formatted period label (e.g., "December 2024", "2024")
        """
        # Check if it's a full year
        if (start_date.month == 1 and start_date.day == 1 and
            end_date.month == 12 and end_date.day == 31 and
            start_date.year == end_date.year):
            return str(start_date.year)
        
        # Check if it's a single month
        if (start_date.year == end_date.year and 
            start_date.month == end_date.month):
            month_name = calendar.month_name[start_date.month]
            return f"{month_name} {start_date.year}"
        
        # Otherwise, show date range
        return f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"

    def get_multi_year_comparison(
        self,
        account_id: int,
        years: List[int],
        top_limit: int = 5
    ) -> Dict[str, Any]:
        """
        Compare multiple years with trend analysis
        
        Args:
            account_id: Account ID to compare
            years: List of years to compare (sorted)
            top_limit: Number of top recipients to include
            
        Returns:
            Multi-year comparison data with trends
        """
        years_data = []
        
        # Collect data for each year
        for year in years:
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            
            summary = self.get_summary(
                account_id=account_id,
                from_date=year_start,
                to_date=year_end
            )
            
            categories = self.get_category_aggregation(
                account_id=account_id,
                from_date=year_start,
                to_date=year_end,
                limit=20
            )
            
            years_data.append({
                'year': year,
                'total_income': summary['total_income'],
                'total_expenses': summary['total_expenses'],
                'net_balance': summary['total_income'] + summary['total_expenses'],  # expenses are negative
                'transaction_count': summary['transaction_count'],
                'categories': categories
            })
        
        # Calculate year-over-year changes and trends
        trends = []
        for i in range(1, len(years_data)):
            prev_year = years_data[i-1]
            curr_year = years_data[i]
            
            def calc_change(old_val: float, new_val: float) -> float:
                if old_val == 0:
                    return 100.0 if new_val != 0 else 0.0
                return round(((new_val - old_val) / abs(old_val)) * 100, 2)
            
            trends.append({
                'from_year': prev_year['year'],
                'to_year': curr_year['year'],
                'income_change': round(curr_year['total_income'] - prev_year['total_income'], 2),
                'income_change_percent': calc_change(prev_year['total_income'], curr_year['total_income']),
                'expenses_change': round(curr_year['total_expenses'] - prev_year['total_expenses'], 2),
                'expenses_change_percent': calc_change(abs(prev_year['total_expenses']), abs(curr_year['total_expenses'])),
                'balance_change': round(curr_year['net_balance'] - prev_year['net_balance'], 2),
                'balance_change_percent': calc_change(prev_year['net_balance'], curr_year['net_balance'])
            })
        
        # Calculate overall averages
        total_income = sum(y['total_income'] for y in years_data)
        total_expenses = sum(abs(y['total_expenses']) for y in years_data)
        avg_income = round(total_income / len(years_data), 2)
        avg_expenses = round(total_expenses / len(years_data), 2)
        
        return {
            'years': years_data,
            'trends': trends,
            'summary': {
                'years_compared': len(years),
                'average_income': avg_income,
                'average_expenses': avg_expenses,
                'average_net': round(avg_income - avg_expenses, 2),
                'total_income_all_years': round(total_income, 2),
                'total_expenses_all_years': round(total_expenses, 2)
            }
        }
    
    def get_quarterly_comparison(
        self,
        account_id: int,
        year: int,
        compare_to_previous_year: bool = False
    ) -> Dict[str, Any]:
        """
        Compare quarters within a year, optionally with previous year
        
        Args:
            account_id: Account ID to compare
            year: Year for quarterly comparison
            compare_to_previous_year: Compare to previous year's quarters
            
        Returns:
            Quarterly comparison data
        """
        quarters = []
        quarter_definitions = [
            (1, 3, 'Q1'),   # Jan-Mar
            (4, 6, 'Q2'),   # Apr-Jun
            (7, 9, 'Q3'),   # Jul-Sep
            (10, 12, 'Q4')  # Oct-Dec
        ]
        
        # Get data for each quarter
        for start_month, end_month, quarter_label in quarter_definitions:
            quarter_start = date(year, start_month, 1)
            # Last day of end_month
            if end_month == 12:
                quarter_end = date(year, 12, 31)
            else:
                next_month = date(year, end_month + 1, 1)
                quarter_end = next_month - relativedelta(days=1)
            
            summary = self.get_summary(
                account_id=account_id,
                from_date=quarter_start,
                to_date=quarter_end
            )
            
            categories = self.get_category_aggregation(
                account_id=account_id,
                from_date=quarter_start,
                to_date=quarter_end,
                limit=10
            )
            
            quarter_data = {
                'quarter': quarter_label,
                'year': year,
                'start_date': quarter_start.isoformat(),
                'end_date': quarter_end.isoformat(),
                'total_income': summary['total_income'],
                'total_expenses': summary['total_expenses'],
                'net_balance': summary['total_income'] + summary['total_expenses'],  # expenses are negative
                'transaction_count': summary['transaction_count'],
                'categories': categories
            }
            
            # Compare to previous year if requested
            if compare_to_previous_year:
                prev_year_start = date(year - 1, start_month, 1)
                if end_month == 12:
                    prev_year_end = date(year - 1, 12, 31)
                else:
                    prev_next_month = date(year - 1, end_month + 1, 1)
                    prev_year_end = prev_next_month - relativedelta(days=1)
                
                prev_summary = self.get_summary(
                    account_id=account_id,
                    from_date=prev_year_start,
                    to_date=prev_year_end
                )
                
                def calc_change(old_val: float, new_val: float) -> float:
                    if old_val == 0:
                        return 100.0 if new_val != 0 else 0.0
                    return round(((new_val - old_val) / abs(old_val)) * 100, 2)
                
                quarter_data['comparison_to_previous_year'] = {
                    'previous_year': year - 1,
                    'previous_income': prev_summary['total_income'],
                    'previous_expenses': prev_summary['total_expenses'],
                    'previous_net': prev_summary['total_income'] + prev_summary['total_expenses'],  # expenses are negative
                    'income_change': round(summary['total_income'] - prev_summary['total_income'], 2),
                    'income_change_percent': calc_change(prev_summary['total_income'], summary['total_income']),
                    'expenses_change': round(summary['total_expenses'] - prev_summary['total_expenses'], 2),
                    'expenses_change_percent': calc_change(abs(prev_summary['total_expenses']), abs(summary['total_expenses']))
                }
            
            quarters.append(quarter_data)
        
        # Calculate quarter-to-quarter changes within the year
        qoq_changes = []
        for i in range(1, len(quarters)):
            prev_q = quarters[i-1]
            curr_q = quarters[i]
            
            def calc_change(old_val: float, new_val: float) -> float:
                if old_val == 0:
                    return 100.0 if new_val != 0 else 0.0
                return round(((new_val - old_val) / abs(old_val)) * 100, 2)
            
            qoq_changes.append({
                'from_quarter': prev_q['quarter'],
                'to_quarter': curr_q['quarter'],
                'income_change': round(curr_q['total_income'] - prev_q['total_income'], 2),
                'income_change_percent': calc_change(prev_q['total_income'], curr_q['total_income']),
                'expenses_change': round(curr_q['total_expenses'] - prev_q['total_expenses'], 2),
                'expenses_change_percent': calc_change(abs(prev_q['total_expenses']), abs(curr_q['total_expenses']))
            })
        
        return {
            'year': year,
            'quarters': quarters,
            'quarter_to_quarter_changes': qoq_changes,
            'year_summary': {
                'total_income': sum(q['total_income'] for q in quarters),
                'total_expenses': sum(q['total_expenses'] for q in quarters),
                'avg_quarterly_income': round(sum(q['total_income'] for q in quarters) / 4, 2),
                'avg_quarterly_expenses': round(sum(abs(q['total_expenses']) for q in quarters) / 4, 2)
            }
        }
    
    def get_benchmark_analysis(
        self,
        account_id: int,
        year: int,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Compare spending to historical averages (benchmark)
        
        Args:
            account_id: Account ID to analyze
            year: Year for benchmark
            month: Optional month for more specific benchmark
            
        Returns:
            Benchmark analysis with category comparisons
        """
        from dateutil.relativedelta import relativedelta
        
        # Define the period to analyze
        if month:
            period_start = date(year, month, 1)
            period_end = (datetime(year, month, 1) + relativedelta(months=1, days=-1)).date()
            period_label = f"{calendar.month_name[month]} {year}"
        else:
            period_start = date(year, 1, 1)
            period_end = date(year, 12, 31)
            period_label = str(year)
        
        # Get current period data
        current_summary = self.get_summary(
            account_id=account_id,
            from_date=period_start,
            to_date=period_end
        )
        
        current_categories = self.get_category_aggregation(
            account_id=account_id,
            from_date=period_start,
            to_date=period_end,
            limit=50
        )
        
        # Calculate historical averages (all data excluding current period)
        # Get all transactions for this account to calculate averages
        all_transactions = self.db.query(DataRow).filter(
            DataRow.account_id == account_id,
            or_(
                DataRow.transaction_date < period_start,
                DataRow.transaction_date > period_end
            )
        ).all()
        
        # Calculate time range for historical data
        if all_transactions:
            min_date = min(t.transaction_date for t in all_transactions)
            max_date = max(t.transaction_date for t in all_transactions)
            
            # Calculate number of periods (months or years)
            if month:
                # Count months
                months_diff = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1
                num_periods = max(months_diff, 1)
            else:
                # Count years
                years_diff = max_date.year - min_date.year + 1
                num_periods = max(years_diff, 1)
            
            # Get historical averages by category
            historical_categories = self.get_category_aggregation(
                account_id=account_id,
                from_date=min_date,
                to_date=period_start - relativedelta(days=1),
                limit=50
            )
        else:
            # No historical data available
            num_periods = 1
            historical_categories = []
        
        # Calculate average per period for each category
        category_benchmarks = []
        current_cat_dict = {cat['category_id']: cat for cat in current_categories}
        
        for hist_cat in historical_categories:
            cat_id = hist_cat['category_id']
            # total_amount is negative for expenses, positive for income
            # We want to compare absolute expense amounts
            hist_amount = abs(hist_cat.get('total_amount', 0))
            avg_expenses = round(hist_amount / num_periods, 2) if num_periods > 0 else 0
            
            current_cat = current_cat_dict.get(cat_id, {})
            current_expenses = abs(current_cat.get('total_amount', 0))
            
            diff = round(current_expenses - avg_expenses, 2)
            
            if avg_expenses > 0:
                diff_percent = round((diff / avg_expenses) * 100, 2)
            else:
                diff_percent = 100.0 if current_expenses > 0 else 0.0
            
            category_benchmarks.append({
                'category_id': cat_id,
                'category_name': hist_cat.get('category_name', 'Unknown'),
                'current_expenses': current_expenses,
                'average_expenses': avg_expenses,
                'difference': diff,
                'difference_percent': diff_percent,
                'status': 'above' if diff > 0 else 'below' if diff < 0 else 'equal'
            })
        
        # Sort by absolute difference
        category_benchmarks.sort(key=lambda x: abs(x['difference']), reverse=True)
        
        # Calculate overall benchmark
        total_current_expenses = abs(current_summary['total_expenses'])
        
        # Get historical overall average
        if all_transactions:
            historical_summary = self.get_summary(
                account_id=account_id,
                from_date=min_date,
                to_date=period_start - relativedelta(days=1)
            )
            avg_total_expenses = round(abs(historical_summary['total_expenses']) / num_periods, 2) if num_periods > 0 else 0
        else:
            avg_total_expenses = 0
        
        overall_diff = round(total_current_expenses - avg_total_expenses, 2)
        
        if avg_total_expenses > 0:
            overall_diff_percent = round((overall_diff / avg_total_expenses) * 100, 2)
        else:
            overall_diff_percent = 100.0 if total_current_expenses > 0 else 0.0
        
        return {
            'period': period_label,
            'period_start': period_start.isoformat(),
            'period_end': period_end.isoformat(),
            'current': {
                'total_income': current_summary['total_income'],
                'total_expenses': total_current_expenses,
                'net_balance': current_summary['total_income'] + current_summary['total_expenses'],  # expenses are negative
                'transaction_count': current_summary['transaction_count']
            },
            'benchmark': {
                'average_expenses': avg_total_expenses,
                'difference': overall_diff,
                'difference_percent': overall_diff_percent,
                'status': 'above' if overall_diff > 0 else 'below' if overall_diff < 0 else 'equal',
                'num_periods_analyzed': num_periods
            },
            'categories': category_benchmarks[:20]  # Top 20 categories by difference
        }

