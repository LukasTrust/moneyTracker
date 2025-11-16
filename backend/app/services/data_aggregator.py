"""
Data Aggregator - Aggregate transaction data for statistics and charts
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_
from datetime import datetime, date
from collections import defaultdict
import calendar

from app.models.data_row import DataRow
from app.models.category import Category


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
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics (income, expenses, balance, count)
        
        REFACTORED: Uses direct column access instead of json_extract()
        
        Args:
            account_id: Filter by account ID (None for all accounts)
            from_date: Start date filter
            to_date: End date filter
            category_id: Filter by category ID (None for all categories)
            
        Returns:
            Dictionary with summary statistics
        """
        # Use SQL aggregation for better performance
        from sqlalchemy import case, cast, Float
        
        query = self.db.query(
            func.sum(case((DataRow.amount > 0, DataRow.amount), else_=0)).label('total_income'),
            func.sum(case((DataRow.amount < 0, DataRow.amount), else_=0)).label('total_expenses'),
            func.sum(DataRow.amount).label('net_balance'),
            func.count(DataRow.id).label('transaction_count')
        )
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        if category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
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
        category_id: Optional[int] = None
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
            
        Returns:
            List of category aggregations
        """
        from sqlalchemy import case
        
        # Build aggregation query
        query = self.db.query(
            DataRow.category_id,
            func.sum(DataRow.amount).label('total_amount'),
            func.count(DataRow.id).label('count')
        )
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        if category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
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
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated data by recipient
        
        Args:
            account_id: Filter by account ID
            from_date: Start date filter
            to_date: End date filter
            limit: Maximum number of recipients to return
            transaction_type: Filter by transaction type ('all', 'income', 'expense')
            category_id: Filter by category ID
            
        Returns:
            List of recipient aggregations
        """
        query = self.db.query(DataRow)
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        # Filter by category
        if category_id is not None:
            query = query.filter(DataRow.category_id == category_id)
        
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
            recipient = transaction.data.get('recipient', 'Unbekannt')
            if not recipient or recipient.strip() == '':
                recipient = 'Unbekannt'
            
            amount_str = transaction.data.get('amount', '0')
            amount = self.parse_amount(amount_str)
            
            # Filter by transaction type
            if transaction_type == 'income' and amount <= 0:
                continue
            elif transaction_type == 'expense' and amount >= 0:
                continue
            
            recipient_data[recipient]['total_amount'] += amount
            recipient_data[recipient]['count'] += 1
            total_absolute += abs(amount)
            
            # Store category info (use first occurrence)
            if transaction.category_id and not recipient_data[recipient]['category_id']:
                category = self.db.query(Category).filter(
                    Category.id == transaction.category_id
                ).first()
                if category:
                    recipient_data[recipient]['category_id'] = category.id
                    recipient_data[recipient]['category_name'] = category.name
        
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
        category_id: Optional[int] = None
    ) -> Dict[str, List]:
        """
        Get balance history grouped by time period
        
        REFACTORED: Uses SQL strftime for date grouping (much faster!)
        
        Args:
            account_id: Filter by account ID
            from_date: Start date filter
            to_date: End date filter
            group_by: Grouping period ('day', 'month', 'year')
            category_id: Filter by specific category ID
            
        Returns:
            Dictionary with labels, income, expenses, balance arrays
        """
        from sqlalchemy import case
        
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
        
        # Apply filters
        if account_id:
            query = query.filter(DataRow.account_id == account_id)
        
        if from_date:
            query = query.filter(DataRow.transaction_date >= from_date)
        
        if to_date:
            query = query.filter(DataRow.transaction_date <= to_date)
        
        if category_id is not None:
            if category_id == -1:
                query = query.filter(DataRow.category_id.is_(None))
            else:
                query = query.filter(DataRow.category_id == category_id)
        
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
