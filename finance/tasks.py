"""
Celery tasks for finance app
"""
import logging
from celery import shared_task
from celery.exceptions import Retry
from django.core.exceptions import ObjectDoesNotExist
from finance.models import Account
from finance.services.account_syncer import AccountSyncer

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def sync_account_balance(self, account_id, strategy=None):
    """
    Async task to sync account balance (calculate and materialize balances)
    
    Args:
        account_id: UUID of the account to sync
        strategy: 'forward' or 'reverse' (optional, defaults to None for auto-detection)
    
    Retries up to 3 times with 5-minute delays if it fails
    """
    try:
        logger.info(f"Starting account balance sync for account {account_id}")
        
        # Get account from database
        try:
            account = Account.objects.get(id=account_id)
        except ObjectDoesNotExist:
            logger.error(f"Account {account_id} not found")
            return f"Account {account_id} not found"
        
        # Sync the account
        syncer = AccountSyncer(account)
        syncer.sync(strategy=strategy)
        
        logger.info(f"Account balance sync completed for account {account_id}")
        return f"Successfully synced account {account_id}"
        
    except Exception as exc:
        logger.error(f"Account balance sync failed for {account_id}: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

