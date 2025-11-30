"""
Celery tasks for investments
"""
import logging
from celery import shared_task
from celery.exceptions import Retry
from investments.services.b3_price_fetcher import B3PriceFetcher

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_b3_prices(self):
    """
    Daily task to update B3 security prices
    
    Retries up to 3 times with 5-minute delays if it fails
    """
    try:
        logger.info("Starting B3 price update task")
        updated_count = B3PriceFetcher.update_all_securities_prices()
        logger.info(f"B3 price update completed: {updated_count} securities updated")
        return f"Updated {updated_count} security prices"
    except Exception as exc:
        logger.error(f"B3 price update failed: {exc}", exc_info=True)
        # Retry the task
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes
