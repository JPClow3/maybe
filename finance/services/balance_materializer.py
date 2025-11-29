"""
Balance materializer - ported from app/models/balance/materializer.rb
Materializes (calculates and persists) balances for an account
"""
from datetime import date
from decimal import Decimal
from typing import List
from django.db import transaction
from django.utils import timezone
from finance.models import Account, Balance
from .balance_calculator import ForwardBalanceCalculator


class BalanceMaterializer:
    """Materializes balances for an account"""
    
    def __init__(self, account: Account, strategy: str = 'forward'):
        """
        Initialize materializer
        
        Args:
            account: Account to materialize balances for
            strategy: 'forward' for manual accounts, 'reverse' for imported accounts
        """
        self.account = account
        self.strategy = strategy
        self._balances: List[Balance] = []
    
    def materialize_balances(self):
        """Calculate and persist balances"""
        with transaction.atomic():
            self._calculate_balances()
            self._persist_balances()
            self._purge_stale_balances()
            
            if self.strategy == 'forward':
                self._update_account_info()
    
    def _calculate_balances(self):
        """Calculate balances using appropriate calculator"""
        if self.strategy == 'forward':
            calculator = ForwardBalanceCalculator(self.account)
        else:
            # For now, use forward calculator for reverse too
            # Can be enhanced with ReverseBalanceCalculator later
            calculator = ForwardBalanceCalculator(self.account)
        
        self._balances = calculator.calculate()
    
    def _persist_balances(self):
        """Persist calculated balances to database"""
        if not self._balances:
            return
        
        # Use bulk_update for existing, bulk_create for new
        current_time = timezone.now()
        balance_data = []
        
        for balance in self._balances:
            balance_data.append({
                'account_id': self.account.id,
                'date': balance.date,
                'currency': balance.currency,
                'balance': balance.balance,
                'cash_balance': balance.cash_balance,
                'start_cash_balance': balance.start_cash_balance,
                'start_non_cash_balance': balance.start_non_cash_balance,
                'cash_inflows': balance.cash_inflows,
                'cash_outflows': balance.cash_outflows,
                'non_cash_inflows': balance.non_cash_inflows,
                'non_cash_outflows': balance.non_cash_outflows,
                'net_market_flows': balance.net_market_flows,
                'cash_adjustments': balance.cash_adjustments,
                'non_cash_adjustments': balance.non_cash_adjustments,
                'flows_factor': balance.flows_factor,
                'updated_at': current_time,
            })
        
        # Delete existing balances in date range
        if self._balances:
            min_date = min(b.date for b in self._balances)
            max_date = max(b.date for b in self._balances)
            Balance.objects.filter(
                account=self.account,
                date__gte=min_date,
                date__lte=max_date,
                currency=self.account.currency
            ).delete()
        
        # Bulk create new balances
        Balance.objects.bulk_create([
            Balance(**data) for data in balance_data
        ])
    
    def _purge_stale_balances(self):
        """Remove balances outside calculated range"""
        if not self._balances:
            return
        
        sorted_balances = sorted(self._balances, key=lambda b: b.date)
        oldest_date = sorted_balances[0].date
        newest_date = sorted_balances[-1].date
        
        deleted_count = Balance.objects.filter(
            account=self.account,
            currency=self.account.currency
        ).exclude(
            date__gte=oldest_date,
            date__lte=newest_date
        ).delete()[0]
        
        if deleted_count > 0:
            print(f"Purged {deleted_count} stale balances")
    
    def _update_account_info(self):
        """Update account balance cache from latest calculated balance"""
        if not self._balances:
            return
        
        # Get the most recent balance
        latest_balance = max(self._balances, key=lambda b: b.date)
        
        # Update account cache
        self.account.balance = latest_balance.balance
        self.account.cash_balance = latest_balance.cash_balance
        self.account.save(update_fields=['balance', 'cash_balance'])

