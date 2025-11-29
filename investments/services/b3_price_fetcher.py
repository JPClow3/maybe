"""
B3 (Brazilian stock market) price fetcher using yfinance
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
import yfinance as yf
from investments.models import Security, SecurityPrice


class B3PriceFetcher:
    """Fetches security prices from B3 using yfinance"""
    
    def __init__(self, security: Security):
        self.security = security
    
    def fetch_price(self, target_date: Optional[date] = None) -> Optional[Decimal]:
        """
        Fetch price for a specific date
        
        Args:
            target_date: Date to fetch price for (defaults to today)
        
        Returns:
            Price as Decimal, or None if not found
        """
        if target_date is None:
            target_date = date.today()
        
        try:
            ticker = yf.Ticker(self.security.ticker)
            
            # Get historical data
            hist = ticker.history(start=target_date, end=target_date + timedelta(days=1))
            
            if hist.empty:
                return None
            
            # Get closing price
            close_price = hist['Close'].iloc[0]
            return Decimal(str(close_price))
            
        except Exception as e:
            print(f"Error fetching price for {self.security.ticker}: {e}")
            return None
    
    def fetch_price_range(self, start_date: date, end_date: date) -> List[SecurityPrice]:
        """
        Fetch prices for a date range
        
        Args:
            start_date: Start date
            end_date: End date
        
        Returns:
            List of SecurityPrice objects
        """
        prices = []
        
        try:
            ticker = yf.Ticker(self.security.ticker)
            
            # Get historical data
            hist = ticker.history(start=start_date, end=end_date + timedelta(days=1))
            
            if hist.empty:
                return prices
            
            # Create SecurityPrice objects for each date
            for idx, row in hist.iterrows():
                price_date = idx.date()
                close_price = Decimal(str(row['Close']))
                
                # Get or create SecurityPrice
                price_obj, created = SecurityPrice.objects.get_or_create(
                    security=self.security,
                    date=price_date,
                    currency=self.security.country_code == 'BR' and 'BRL' or 'USD',
                    defaults={'price': close_price}
                )
                
                if not created:
                    price_obj.price = close_price
                    price_obj.save(update_fields=['price'])
                
                prices.append(price_obj)
            
        except Exception as e:
            print(f"Error fetching price range for {self.security.ticker}: {e}")
        
        return prices
    
    @staticmethod
    def update_all_securities_prices():
        """Update prices for all Brazilian securities"""
        securities = Security.objects.filter(country_code='BR')
        
        updated_count = 0
        for security in securities:
            try:
                fetcher = B3PriceFetcher(security)
                price = fetcher.fetch_price()
                
                if price:
                    # Update today's price
                    price_obj, created = SecurityPrice.objects.get_or_create(
                        security=security,
                        date=date.today(),
                        currency='BRL',
                        defaults={'price': price}
                    )
                    
                    if not created:
                        price_obj.price = price
                        price_obj.save(update_fields=['price'])
                    
                    updated_count += 1
            except Exception as e:
                print(f"Error updating {security.ticker}: {e}")
        
        return updated_count

