from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction, Valuation
from .services.account_syncer import AccountSyncer

@receiver(post_save, sender=Transaction)
@receiver(post_save, sender=Valuation)
@receiver(post_delete, sender=Transaction)
@receiver(post_delete, sender=Valuation)
def sync_account_on_entry_change(sender, instance, **kwargs):
    """Trigger account sync when transaction or valuation is created/updated/deleted"""
    # Only sync if not raw save (bulk operations)
    if kwargs.get('raw', False):
        return
    
    account = instance.account
    syncer = AccountSyncer(account)
    syncer.sync()

