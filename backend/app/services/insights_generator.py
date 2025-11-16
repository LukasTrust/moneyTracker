"""
Insights Generator Service - Generates personalized spending insights
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import calendar

from app.models.data_row import DataRow
from app.models.category import Category
from app.models.insight import Insight, InsightGenerationLog
from app.models.transfer import Transfer


class InsightsGenerator:
    """
    Service for generating personalized spending insights.
    
    Implements algorithms for:
    - Month-over-Month (MoM) comparisons
    - Year-over-Year (YoY) comparisons
    - Top growth categories detection
    - Savings potential identification
    - Unusual expense detection
    """
    
    # Thresholds for insight generation
    MOM_THRESHOLD = 0.20  # 20% change triggers MoM insight
    YOY_THRESHOLD = 0.25  # 25% change triggers YoY insight
    CATEGORY_GROWTH_THRESHOLD = 0.30  # 30% growth + 50 EUR minimum
    CATEGORY_GROWTH_MIN_AMOUNT = 50.0
    UNUSUAL_EXPENSE_MULTIPLIER = 3.0  # 3x average transaction
    
    # Cooldown settings
    DEFAULT_COOLDOWN_HOURS = 24  # Default: show insight max once per day
    HIGH_PRIORITY_COOLDOWN_HOURS = 12  # High priority: can show twice per day
    LOW_PRIORITY_COOLDOWN_HOURS = 48  # Low priority: show every 2 days
    
    SUBSCRIPTION_KEYWORDS = [
        'netflix', 'spotify', 'amazon prime', 'disney', 'apple music',
        'youtube premium', 'hbo', 'sky', 'dazn', 'audible', 'kindle',
        'playstation', 'xbox', 'nintendo', 'steam', 'fitness', 'gym'
    ]
    
    def __init__(self, db: Session):
        """
        Initialize with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    def _get_transfer_transaction_ids(self) -> set:
        """Get set of transaction IDs that are part of transfers (to exclude from analysis)"""
        transfer_ids = set()
        
        from_ids = self.db.query(Transfer.from_transaction_id).all()
        transfer_ids.update([tid[0] for tid in from_ids if tid[0]])
        
        to_ids = self.db.query(Transfer.to_transaction_id).all()
        transfer_ids.update([tid[0] for tid in to_ids if tid[0]])
        
        return transfer_ids
    
    def _get_expenses_for_period(
        self,
        account_id: Optional[int],
        start_date: date,
        end_date: date,
        exclude_transfers: bool = True
    ) -> float:
        """
        Get total expenses for a period
        
        Args:
            account_id: Account ID (None = all accounts)
            start_date: Period start date
            end_date: Period end date
            exclude_transfers: Whether to exclude transfer transactions
            
        Returns:
            Total expenses (negative amounts)
        """
        query = self.db.query(func.sum(DataRow.amount)).filter(
            and_(
                DataRow.transaction_date >= start_date,
                DataRow.transaction_date <= end_date,
                DataRow.amount < 0  # Only expenses
            )
        )
        
        if account_id is not None:
            query = query.filter(DataRow.account_id == account_id)
        
        if exclude_transfers:
            transfer_ids = self._get_transfer_transaction_ids()
            if transfer_ids:
                query = query.filter(~DataRow.id.in_(transfer_ids))
        
        result = query.scalar()
        return abs(float(result)) if result else 0.0
    
    def _get_income_for_period(
        self,
        account_id: Optional[int],
        start_date: date,
        end_date: date,
        exclude_transfers: bool = True
    ) -> float:
        """Get total income for a period"""
        query = self.db.query(func.sum(DataRow.amount)).filter(
            and_(
                DataRow.transaction_date >= start_date,
                DataRow.transaction_date <= end_date,
                DataRow.amount > 0  # Only income
            )
        )
        
        if account_id is not None:
            query = query.filter(DataRow.account_id == account_id)
        
        if exclude_transfers:
            transfer_ids = self._get_transfer_transaction_ids()
            if transfer_ids:
                query = query.filter(~DataRow.id.in_(transfer_ids))
        
        result = query.scalar()
        return float(result) if result else 0.0
    
    def _get_category_expenses(
        self,
        account_id: Optional[int],
        start_date: date,
        end_date: date,
        exclude_transfers: bool = True
    ) -> Dict[int, Tuple[str, float]]:
        """
        Get expenses grouped by category
        
        Returns:
            Dict mapping category_id -> (category_name, total_expenses)
        """
        query = self.db.query(
            DataRow.category_id,
            Category.name,
            func.sum(DataRow.amount).label('total')
        ).outerjoin(
            Category, DataRow.category_id == Category.id
        ).filter(
            and_(
                DataRow.transaction_date >= start_date,
                DataRow.transaction_date <= end_date,
                DataRow.amount < 0  # Only expenses
            )
        ).group_by(DataRow.category_id, Category.name)
        
        if account_id is not None:
            query = query.filter(DataRow.account_id == account_id)
        
        if exclude_transfers:
            transfer_ids = self._get_transfer_transaction_ids()
            if transfer_ids:
                query = query.filter(~DataRow.id.in_(transfer_ids))
        
        results = {}
        for cat_id, cat_name, total in query.all():
            if cat_id:  # Ignore uncategorized
                results[cat_id] = (cat_name or "Unbekannt", abs(float(total)))
        
        return results
    
    def generate_mom_insights(
        self,
        account_id: Optional[int] = None
    ) -> List[Insight]:
        """
        Generate Month-over-Month comparison insights
        
        Compares current month with previous month.
        Triggers insights if change > MOM_THRESHOLD (20%)
        
        Args:
            account_id: Account ID (None = all accounts)
            
        Returns:
            List of generated insights
        """
        insights = []
        today = date.today()
        
        # Current month
        current_month_start = today.replace(day=1)
        current_month_end = today
        
        # Previous month
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        
        # Get expenses for both periods
        current_expenses = self._get_expenses_for_period(account_id, current_month_start, current_month_end)
        prev_expenses = self._get_expenses_for_period(account_id, prev_month_start, prev_month_end)
        
        # Only generate insight if we have data for previous month
        if prev_expenses > 0:
            change = current_expenses - prev_expenses
            change_percent = (change / prev_expenses) * 100
            
            if abs(change_percent) >= (self.MOM_THRESHOLD * 100):
                if change > 0:
                    # Increase
                    insight = Insight(
                        account_id=account_id,
                        insight_type='mom_increase',
                        severity='warning' if change_percent > 30 else 'info',
                        title=f"Ausgaben um {abs(change_percent):.0f}% gestiegen",
                        description=f"Du gibst diesen Monat {abs(change_percent):.0f}% mehr aus als letzten Monat. "
                                    f"Aktuelle Ausgaben: {current_expenses:.2f} EUR (Vormonat: {prev_expenses:.2f} EUR).",
                        insight_data={
                            'current_amount': current_expenses,
                            'previous_amount': prev_expenses,
                            'change_amount': change,
                            'change_percent': change_percent,
                            'current_period': current_month_start.isoformat(),
                            'previous_period': prev_month_start.isoformat()
                        },
                        priority=8 if change_percent > 40 else 6,
                        cooldown_hours=self.HIGH_PRIORITY_COOLDOWN_HOURS if change_percent > 40 else self.DEFAULT_COOLDOWN_HOURS,
                        valid_until=datetime.now() + timedelta(days=30)
                    )
                else:
                    # Decrease
                    insight = Insight(
                        account_id=account_id,
                        insight_type='mom_decrease',
                        severity='success',
                        title=f"Ausgaben um {abs(change_percent):.0f}% gesunken",
                        description=f"Gut gemacht! Du gibst diesen Monat {abs(change_percent):.0f}% weniger aus als letzten Monat. "
                                    f"Das sind {abs(change):.2f} EUR Ersparnis!",
                        insight_data={
                            'current_amount': current_expenses,
                            'previous_amount': prev_expenses,
                            'change_amount': change,
                            'change_percent': change_percent,
                            'savings': abs(change),
                            'current_period': current_month_start.isoformat(),
                            'previous_period': prev_month_start.isoformat()
                        },
                        priority=7,
                        cooldown_hours=self.DEFAULT_COOLDOWN_HOURS,
                        valid_until=datetime.now() + timedelta(days=30)
                    )
                
                insights.append(insight)
        
        return insights
    
    def generate_yoy_insights(
        self,
        account_id: Optional[int] = None
    ) -> List[Insight]:
        """
        Generate Year-over-Year comparison insights
        
        Compares current month with same month last year.
        Triggers insights if change > YOY_THRESHOLD (25%)
        
        Args:
            account_id: Account ID (None = all accounts)
            
        Returns:
            List of generated insights
        """
        insights = []
        today = date.today()
        
        # Current month
        current_month_start = today.replace(day=1)
        current_month_end = today
        
        # Same month last year
        last_year_start = (current_month_start - relativedelta(years=1))
        last_year_end = last_year_start.replace(day=calendar.monthrange(last_year_start.year, last_year_start.month)[1])
        
        # Get expenses for both periods
        current_expenses = self._get_expenses_for_period(account_id, current_month_start, current_month_end)
        last_year_expenses = self._get_expenses_for_period(account_id, last_year_start, last_year_end)
        
        # Only generate insight if we have data for last year
        if last_year_expenses > 0:
            change = current_expenses - last_year_expenses
            change_percent = (change / last_year_expenses) * 100
            
            if abs(change_percent) >= (self.YOY_THRESHOLD * 100):
                if change > 0:
                    # Increase
                    insight = Insight(
                        account_id=account_id,
                        insight_type='yoy_increase',
                        severity='warning' if change_percent > 50 else 'info',
                        title=f"Ausgaben im Jahresvergleich um {abs(change_percent):.0f}% gestiegen",
                        description=f"Im Vergleich zum Vorjahr gibst du {abs(change_percent):.0f}% mehr aus. "
                                    f"Aktuell: {current_expenses:.2f} EUR (Vorjahr: {last_year_expenses:.2f} EUR).",
                        insight_data={
                            'current_amount': current_expenses,
                            'previous_amount': last_year_expenses,
                            'change_amount': change,
                            'change_percent': change_percent,
                            'current_period': current_month_start.isoformat(),
                            'previous_period': last_year_start.isoformat()
                        },
                        priority=7 if change_percent > 50 else 5,
                        cooldown_hours=self.LOW_PRIORITY_COOLDOWN_HOURS,
                        valid_until=datetime.now() + timedelta(days=45)
                    )
                else:
                    # Decrease
                    insight = Insight(
                        account_id=account_id,
                        insight_type='yoy_decrease',
                        severity='success',
                        title=f"Ausgaben im Jahresvergleich um {abs(change_percent):.0f}% gesunken",
                        description=f"Hervorragend! Im Vergleich zum Vorjahr gibst du {abs(change_percent):.0f}% weniger aus. "
                                    f"Das entspricht einer Ersparnis von {abs(change):.2f} EUR!",
                        insight_data={
                            'current_amount': current_expenses,
                            'previous_amount': last_year_expenses,
                            'change_amount': change,
                            'change_percent': change_percent,
                            'savings': abs(change),
                            'current_period': current_month_start.isoformat(),
                            'previous_period': last_year_start.isoformat()
                        },
                        priority=6,
                        cooldown_hours=self.LOW_PRIORITY_COOLDOWN_HOURS,
                        valid_until=datetime.now() + timedelta(days=45)
                    )
                
                insights.append(insight)
        
        return insights
    
    def generate_category_growth_insights(
        self,
        account_id: Optional[int] = None
    ) -> List[Insight]:
        """
        Identify top growth categories
        
        Compares category spending: current month vs previous month
        Triggers if growth > 30% AND absolute increase > 50 EUR
        
        Args:
            account_id: Account ID (None = all accounts)
            
        Returns:
            List of generated insights
        """
        insights = []
        today = date.today()
        
        # Current month
        current_month_start = today.replace(day=1)
        current_month_end = today
        
        # Previous month
        prev_month_end = current_month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)
        
        # Get category expenses
        current_categories = self._get_category_expenses(account_id, current_month_start, current_month_end)
        prev_categories = self._get_category_expenses(account_id, prev_month_start, prev_month_end)
        
        # Find top growth categories
        growth_categories = []
        
        for cat_id, (cat_name, current_amount) in current_categories.items():
            if cat_id in prev_categories:
                prev_amount = prev_categories[cat_id][1]
                
                if prev_amount > 0:
                    change = current_amount - prev_amount
                    change_percent = (change / prev_amount) * 100
                    
                    if change_percent >= (self.CATEGORY_GROWTH_THRESHOLD * 100) and change >= self.CATEGORY_GROWTH_MIN_AMOUNT:
                        growth_categories.append({
                            'category_id': cat_id,
                            'category_name': cat_name,
                            'current_amount': current_amount,
                            'previous_amount': prev_amount,
                            'change': change,
                            'change_percent': change_percent
                        })
        
        # Sort by change percentage (descending)
        growth_categories.sort(key=lambda x: x['change_percent'], reverse=True)
        
        # Generate insights for top 3 growth categories
        for cat_data in growth_categories[:3]:
            severity = 'alert' if cat_data['change_percent'] > 100 else 'warning'
            priority = 9 if cat_data['change_percent'] > 100 else 7
            
            insight = Insight(
                account_id=account_id,
                insight_type='top_growth_category',
                severity=severity,
                title=f"{cat_data['category_name']}: +{cat_data['change_percent']:.0f}%",
                description=f"Deine Ausgaben für '{cat_data['category_name']}' sind um {cat_data['change_percent']:.0f}% gestiegen. "
                            f"Du gibst aktuell {cat_data['current_amount']:.2f} EUR aus (Vormonat: {cat_data['previous_amount']:.2f} EUR). "
                            f"Das sind {cat_data['change']:.2f} EUR mehr!",
                insight_data={
                    'category_id': cat_data['category_id'],
                    'category_name': cat_data['category_name'],
                    'current_amount': cat_data['current_amount'],
                    'previous_amount': cat_data['previous_amount'],
                    'change_amount': cat_data['change'],
                    'change_percent': cat_data['change_percent']
                },
                priority=priority,
                cooldown_hours=self.HIGH_PRIORITY_COOLDOWN_HOURS if priority >= 9 else self.DEFAULT_COOLDOWN_HOURS,
                valid_until=datetime.now() + timedelta(days=30)
            )
            
            insights.append(insight)
        
        return insights
    
    def generate_savings_potential_insights(
        self,
        account_id: Optional[int] = None
    ) -> List[Insight]:
        """
        Detect potential savings opportunities
        
        Identifies:
        - Recurring subscriptions (potential cancelations)
        - Low-value recurring transactions
        
        Args:
            account_id: Account ID (None = all accounts)
            
        Returns:
            List of generated insights
        """
        insights = []
        today = date.today()
        
        # Look back 3 months for recurring patterns
        lookback_start = today - timedelta(days=90)
        
        # Find potential subscription transactions
        query = self.db.query(DataRow).filter(
            and_(
                DataRow.transaction_date >= lookback_start,
                DataRow.amount < 0  # Only expenses
            )
        )
        
        if account_id is not None:
            query = query.filter(DataRow.account_id == account_id)
        
        # Exclude transfers
        transfer_ids = self._get_transfer_transaction_ids()
        if transfer_ids:
            query = query.filter(~DataRow.id.in_(transfer_ids))
        
        transactions = query.all()
        
        # Group by recipient to find recurring patterns
        recipient_groups = defaultdict(list)
        for txn in transactions:
            # Check if transaction matches subscription keywords
            description_lower = (txn.purpose or '').lower() + ' ' + (txn.recipient or '').lower()
            
            for keyword in self.SUBSCRIPTION_KEYWORDS:
                if keyword in description_lower:
                    recipient_groups[keyword].append({
                        'amount': abs(float(txn.amount)),
                        'date': txn.transaction_date,
                        'recipient': txn.recipient or 'Unbekannt',
                        'purpose': txn.purpose or ''
                    })
                    break
        
        # Generate insights for detected subscriptions
        for keyword, txns in recipient_groups.items():
            if len(txns) >= 2:  # At least 2 transactions in 3 months
                avg_amount = sum(t['amount'] for t in txns) / len(txns)
                total_amount = sum(t['amount'] for t in txns)
                
                # Calculate annual cost
                annual_cost = avg_amount * 12
                
                insight = Insight(
                    account_id=account_id,
                    insight_type='savings_potential',
                    severity='info',
                    title=f"Abo gefunden: {keyword.title()}",
                    description=f"Du hast {len(txns)} Abbuchungen für '{keyword.title()}' in den letzten 3 Monaten. "
                                f"Durchschnittlich {avg_amount:.2f} EUR pro Zahlung. "
                                f"Hochgerechnet auf ein Jahr: ca. {annual_cost:.2f} EUR. "
                                f"Nutzt du diesen Service noch aktiv?",
                    insight_data={
                        'keyword': keyword,
                        'transaction_count': len(txns),
                        'average_amount': avg_amount,
                        'total_amount': total_amount,
                        'annual_cost_estimate': annual_cost,
                        'first_transaction': txns[0]['date'].isoformat(),
                        'last_transaction': txns[-1]['date'].isoformat()
                    },
                    priority=6,
                    cooldown_hours=self.LOW_PRIORITY_COOLDOWN_HOURS,
                    valid_until=datetime.now() + timedelta(days=60)
                )
                
                insights.append(insight)
        
        return insights
    
    def generate_all_insights(
        self,
        account_id: Optional[int] = None,
        generation_types: Optional[List[str]] = None
    ) -> List[Insight]:
        """
        Generate all types of insights
        
        Args:
            account_id: Account ID (None = all accounts)
            generation_types: List of types to generate (None = all)
                             Options: 'mom', 'yoy', 'category_growth', 'savings_potential'
            
        Returns:
            List of all generated insights
        """
        all_insights = []
        
        # Default: generate all types
        if generation_types is None:
            generation_types = ['mom', 'yoy', 'category_growth', 'savings_potential']
        
        if 'mom' in generation_types:
            all_insights.extend(self.generate_mom_insights(account_id))
        
        if 'yoy' in generation_types:
            all_insights.extend(self.generate_yoy_insights(account_id))
        
        if 'category_growth' in generation_types:
            all_insights.extend(self.generate_category_growth_insights(account_id))
        
        if 'savings_potential' in generation_types:
            all_insights.extend(self.generate_savings_potential_insights(account_id))
        
        return all_insights
    
    def cleanup_old_insights(
        self,
        account_id: Optional[int] = None,
        days_old: int = 30
    ) -> int:
        """
        Remove old or expired insights
        
        Args:
            account_id: Account ID (None = all accounts)
            days_old: Remove insights older than this many days
            
        Returns:
            Number of insights removed
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        query = self.db.query(Insight).filter(
            or_(
                Insight.created_at < cutoff_date,
                and_(
                    Insight.valid_until.isnot(None),
                    Insight.valid_until < datetime.now()
                )
            )
        )
        
        if account_id is not None:
            query = query.filter(Insight.account_id == account_id)
        
        count = query.delete(synchronize_session=False)
        self.db.commit()
        
        return count
    
    def get_displayable_insights(
        self,
        account_id: Optional[int] = None,
        max_count: int = 1
    ) -> List[Insight]:
        """
        Get insights that are ready to be displayed (respecting cooldown)
        
        This method:
        - Filters out expired insights
        - Respects cooldown periods (last_shown_at + cooldown_hours)
        - Returns insights sorted by priority
        - Limits to max_count
        
        Args:
            account_id: Account ID (None = all accounts)
            max_count: Maximum number of insights to return (default: 1)
            
        Returns:
            List of insights ready to display
        """
        now = datetime.now()
        
        # Base query
        query = self.db.query(Insight).filter(
            Insight.is_dismissed == False
        )
        
        # Filter by account
        if account_id is not None:
            query = query.filter(or_(Insight.account_id == account_id, Insight.account_id.is_(None)))
        
        # Filter out expired insights
        query = query.filter(
            or_(
                Insight.valid_until.is_(None),
                Insight.valid_until >= now
            )
        )
        
        # Get all candidates
        all_insights = query.all()
        
        # Filter by cooldown manually (SQLite datetime arithmetic is tricky)
        displayable = []
        for insight in all_insights:
            if insight.last_shown_at is None:
                # Never shown before - always displayable
                displayable.append(insight)
            else:
                # Check if cooldown has passed
                cooldown_delta = timedelta(hours=insight.cooldown_hours)
                next_show_time = insight.last_shown_at + cooldown_delta
                
                if now >= next_show_time:
                    displayable.append(insight)
        
        # Sort by priority (desc), then by created_at (desc)
        displayable.sort(key=lambda x: (x.priority, x.created_at), reverse=True)
        
        # Limit results
        return displayable[:max_count]
    
    def mark_insight_shown(
        self,
        insight_id: int
    ) -> bool:
        """
        Mark an insight as shown (update last_shown_at and increment show_count)
        
        Args:
            insight_id: ID of insight to mark as shown
            
        Returns:
            Success status
        """
        insight = self.db.query(Insight).filter(Insight.id == insight_id).first()
        
        if not insight:
            return False
        
        insight.last_shown_at = datetime.now()
        insight.show_count += 1
        
        self.db.commit()
        
        return True
    
    def reset_insight_cooldown(
        self,
        insight_id: int
    ) -> bool:
        """
        Reset cooldown for an insight (allow it to be shown immediately)
        
        Args:
            insight_id: ID of insight to reset
            
        Returns:
            Success status
        """
        insight = self.db.query(Insight).filter(Insight.id == insight_id).first()
        
        if not insight:
            return False
        
        insight.last_shown_at = None
        insight.is_dismissed = False
        insight.dismissed_at = None
        
        self.db.commit()
        
        return True
