"""
Sync cache for balance calculations - caches entries and holdings for a date range
"""
from datetime import date
from decimal import Decimal
from typing import List, Dict, Optional
from finance.models import Account, Transaction, Valuation
from investments.models import Holding, Trade


class SyncCache:
    """Cache for entries and holdings during balance calculation"""
    
    def __init__(self, account: Account):
        self.account = account
        self._entries_cache: Dict[date, List] = {}
        self._holdings_cache: Dict[date, List[Holding]] = {}
        self._valuations_cache: Dict[date, Optional[Valuation]] = {}
    
    def get_entries(self, target_date: date) -> List:
        """Get all entries (transactions and trades) for a date"""
        if target_date not in self._entries_cache:
            transactions = list(
                Transaction.objects.filter(account=self.account, date=target_date)
                .select_related('category', 'merchant')
            )
            trades = list(
                Trade.objects.filter(account=self.account, date=target_date)
                .select_related('security')
            )
            # Combine transactions and trades
            self._entries_cache[target_date] = transactions + trades
        return self._entries_cache[target_date]
    
    def get_valuation(self, target_date: date) -> Optional[Valuation]:
        """Get valuation for a date if exists"""
        if target_date not in self._valuations_cache:
            valuation = Valuation.objects.filter(
                account=self.account,
                date=target_date
            ).first()
            self._valuations_cache[target_date] = valuation
        return self._valuations_cache[target_date]
    
    def get_holdings(self, target_date: date) -> List[Holding]:
        """Get holdings for a date"""
        if target_date not in self._holdings_cache:
            holdings = list(
                Holding.objects.filter(account=self.account, date=target_date)
                .select_related('security')
            )
            self._holdings_cache[target_date] = holdings
        return self._holdings_cache[target_date]

