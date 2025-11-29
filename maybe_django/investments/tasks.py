"""
Celery tasks for investments
"""
from celery import shared_task
from investments.services.b3_price_fetcher import B3PriceFetcher


@shared_task
def update_b3_prices():
    """
    Daily task to update B3 security prices
    """
    updated_count = B3PriceFetcher.update_all_securities_prices()
    return f"Updated {updated_count} security prices"
