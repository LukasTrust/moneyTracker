"""
Data Aggregator - Aggregate transaction data for statistics and charts
"""
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from datetime import datetime, date
from collections import defaultdict
import calendar

from app.models.data_row import DataRow
from app.models.category import Category
from app.models.transfer import Transfer


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
        transaction_type: Optional[str] = None
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
        
        # Apply category filter (support both single and multiple)
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
        
        # Execute query
        result = query.first()
        
        return {
            'total_income': round(float(result.total_income or 0), 2),
            'total_expenses': round(float(result.total_expenses or 0), 2),
            'net_balance': round(float(result.net_balance or 0), 2),
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
        transaction_type: Optional[str] = None
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
        
        # Apply category filter
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
        
        # Group by period and order chronologically
        query = query.group_by('period').order_by('period')
        
        # Execute query
        results = query.all()
        
        # Build response arrays
        labels = []
        income = []
        expenses = []
        balance = []
        cumulative = 0.0
        
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
            'balance_diff': round(period2_summary['net_balance'] - period1_summary['net_balance'], 2),
            'balance_diff_percent': calculate_percent_change(
                period1_summary['net_balance'],
                period2_summary['net_balance']
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
                'net_balance': period1_summary['net_balance'],
                'transaction_count': period1_summary['transaction_count'],
                'categories': period1_categories,
                'top_recipients': period1_recipients
            },
            'period2': {
                'period_label': period2_label,
                'total_income': period2_summary['total_income'],
                'total_expenses': period2_summary['total_expenses'],
                'net_balance': period2_summary['net_balance'],
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
