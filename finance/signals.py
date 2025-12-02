import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Transaction, Valuation, Account, Balance
from .services.account_syncer import AccountSyncer

logger = logging.getLogger(__name__)

def invalidate_dashboard_cache(user_id):
    """Invalidate all dashboard cache keys for a user"""
    periods = ['1Y', 'YTD', 'ALL']
    for period in periods:
        cache_key = f'dashboard_stats:{user_id}:{period}'
        cache.delete(cache_key)

# Import Trade and Holding for signal handlers (avoid circular import)
try:
    from investments.models import Trade, Holding
except ImportError:
    Trade = None
    Holding = None

@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=Valuation)
@receiver(post_delete, sender=Transaction)
@receiver(post_delete, sender=Valuation)
def sync_account_on_entry_change(sender, instance, **kwargs):
    """Trigger account sync when transaction or valuation is created/updated/deleted"""
    # Only sync if not raw save (bulk operations)
    if kwargs.get('raw', False):
        return
    
    try:
        account = instance.account
        syncer = AccountSyncer(account)
        syncer.sync()
        invalidate_dashboard_cache(account.user.id)
    except Exception as e:
        logger.error(
            f"Failed to sync account {instance.account.id} after {sender.__name__} change: {e}",
            exc_info=True
        )
        # Don't re-raise - signal handlers shouldn't break the main operation

@receiver(post_save, sender=Account)
@receiver(post_delete, sender=Account)
def invalidate_cache_on_account_change(sender, instance, **kwargs):
    """Invalidate dashboard cache when account is created/updated/deleted"""
    if kwargs.get('raw', False):
        return
    invalidate_dashboard_cache(instance.user.id)

@receiver(post_save, sender=Balance)
@receiver(post_delete, sender=Balance)
def invalidate_cache_on_balance_change(sender, instance, **kwargs):
    """Invalidate dashboard cache when balance is created/updated/deleted"""
    if kwargs.get('raw', False):
        return
    invalidate_dashboard_cache(instance.account.user.id)

# Handle Trade and Holding signals if investments app is available
if Trade:
    @receiver(post_save, sender=Trade)
    @receiver(post_delete, sender=Trade)
    def invalidate_cache_on_trade_change(sender, instance, **kwargs):
        """Invalidate dashboard cache when trade is created/updated/deleted"""
        if kwargs.get('raw', False):
            return
        invalidate_dashboard_cache(instance.account.user.id)

if Holding:
    @receiver(post_save, sender=Holding)
    @receiver(post_delete, sender=Holding)
    def invalidate_cache_on_holding_change(sender, instance, **kwargs):
        """Invalidate dashboard cache when holding is created/updated/deleted"""
        if kwargs.get('raw', False):
            return
        invalidate_dashboard_cache(instance.account.user.id)

