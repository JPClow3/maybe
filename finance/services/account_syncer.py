"""
Account syncer - ported from app/models/account/syncer.rb
Orchestrates account synchronization (balance calculation)
"""
from finance.models import Account
from .balance_materializer import BalanceMaterializer


class AccountSyncer:
    """Syncs account data (balances, holdings, etc.)"""
    
    def __init__(self, account: Account):
        self.account = account
    
    def sync(self, strategy: str = None):
        """
        Perform account sync
        
        Args:
            strategy: 'forward' for manual accounts, 'reverse' for imported accounts.
                     If None, determines automatically based on account type.
        """
        if strategy is None:
            # For now, all accounts use forward strategy
            # In original Rails app, linked accounts (Plaid) use reverse
            strategy = 'forward'
        
        materializer = BalanceMaterializer(self.account, strategy=strategy)
        materializer.materialize_balances()
    
    def sync_later(self, strategy: str = None):
        """
        Schedule sync for later (async) via Celery task
        
        Args:
            strategy: 'forward' or 'reverse' (optional, defaults to None for auto-detection)
        """
        from finance.tasks import sync_account_balance
        
        # Enqueue async task
        sync_account_balance.delay(self.account.id, strategy=strategy)

