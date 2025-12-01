"""
Net Worth Calculator - calculates time-series net worth from Balance records
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from finance.models import Account, Balance

User = get_user_model()


class NetWorthCalculator:
    """Calculate net worth time series from Balance records"""
    
    def __init__(self, user: User):
        self.user = user
    
    def get_time_series(self, period: str = '1Y') -> List[Dict[str, any]]:
        """
        Get net worth time series for a period
        
        Args:
            period: '1Y' (1 year), 'YTD' (year to date), 'ALL' (all time)
        
        Returns:
            List of dicts with 'date' and 'value' keys, sorted by date ascending
        """
        start_date = self._get_start_date(period)
        
        # Get all active accounts for user
        accounts = Account.objects.filter(user=self.user, status='active')
        
        if not accounts.exists():
            return []
        
        # Get all balance records within date range, grouped by date
        from django.db.models import Sum as DjangoSum
        from django.db.models import Q
        
        # Get unique dates with balances
        balance_dates = Balance.objects.filter(
            account__user=self.user,
            date__gte=start_date
        ).values('date').distinct().order_by('date')
        
        if not balance_dates.exists():
            # Fallback: use current account balances as single point
            current_net_worth = accounts.aggregate(DjangoSum('balance'))['balance__sum'] or Decimal('0')
            return [{'date': date.today(), 'value': float(current_net_worth)}]
        
        # Aggregate balances by date
        date_values = {}
        for date_obj in balance_dates:
            balance_date = date_obj['date']
            # Sum all account balances for this specific date
            daily_total = Balance.objects.filter(
                account__user=self.user,
                date=balance_date
            ).aggregate(DjangoSum('balance'))['balance__sum'] or Decimal('0')
            
            date_values[balance_date] = daily_total
        
        # Convert to sorted list of dicts
        series = [
            {'date': d, 'value': float(v)}
            for d, v in sorted(date_values.items())
        ]
        
        # If no data points, use current account balances
        if not series:
            current_net_worth = accounts.aggregate(Sum('balance'))['balance__sum'] or Decimal('0')
            series = [{'date': date.today(), 'value': float(current_net_worth)}]
        
        return series
    
    def get_chart_path(self, period: str = '1Y', width: int = 100, height: int = 40) -> Optional[str]:
        """
        Generate SVG path string for net worth chart
        
        Args:
            period: '1Y', 'YTD', 'ALL'
            width: SVG viewBox width (default 100)
            height: SVG viewBox height (default 40)
        
        Returns:
            SVG path string for the line, or None if insufficient data
        """
        series = self.get_time_series(period)
        
        if len(series) < 2:
            return None
        
        # Find min and max values for scaling
        values = [point['value'] for point in series]
        min_value = min(values)
        max_value = max(values)
        value_range = max_value - min_value
        
        if value_range == 0:
            # Flat line
            y = height / 2
            return f"M 0,{y} L {width},{y}"
        
        # Generate path points
        path_parts = []
        point_count = len(series)
        
        for i, point in enumerate(series):
            x = (i / (point_count - 1)) * width if point_count > 1 else 0
            # Normalize value to 0-1, then scale to height (inverted: higher values at top)
            normalized = (point['value'] - min_value) / value_range
            y = height - (normalized * height)
            
            if i == 0:
                path_parts.append(f"M {x:.1f},{y:.1f}")
            else:
                path_parts.append(f"L {x:.1f},{y:.1f}")
        
        return " ".join(path_parts)
    
    def get_current_net_worth(self) -> Decimal:
        """Get current net worth (sum of all active account balances)"""
        accounts = Account.objects.filter(user=self.user, status='active')
        result = accounts.aggregate(Sum('balance'))['balance__sum']
        return result or Decimal('0')
    
    def get_period_change(self, period: str = '1Y') -> Optional[Decimal]:
        """
        Get net worth change percentage for a period
        
        Args:
            period: '1Y', 'YTD', 'ALL'
        
        Returns:
            Percentage change as Decimal, or None if insufficient data
        """
        series = self.get_time_series(period)
        
        if len(series) < 2:
            return None
        
        start_value = Decimal(str(series[0]['value']))
        end_value = Decimal(str(series[-1]['value']))
        
        if start_value == 0:
            return None
        
        change_pct = ((end_value - start_value) / start_value) * 100
        return change_pct
    
    def _get_start_date(self, period: str) -> date:
        """Get start date for period"""
        today = date.today()
        
        if period == 'YTD':
            return date(today.year, 1, 1)
        elif period == '1Y':
            return today - timedelta(days=365)
        elif period == 'ALL':
            # Get earliest balance date or account creation date
            earliest_balance = Balance.objects.filter(
                account__user=self.user
            ).order_by('date').first()
            
            if earliest_balance:
                return earliest_balance.date
            
            # Fallback to 1 year ago if no balances
            return today - timedelta(days=365)
        else:
            # Default to 1 year
            return today - timedelta(days=365)

