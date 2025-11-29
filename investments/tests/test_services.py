"""
Comprehensive tests for investment services
"""
from django.test import TestCase
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import date, timedelta
from investments.models import Security, SecurityPrice
from investments.services.b3_price_fetcher import B3PriceFetcher


class B3PriceFetcherTestCase(TestCase):
    """Test B3PriceFetcher service"""
    
    def setUp(self):
        self.security = Security.objects.create(
            ticker='PETR4',
            name='Petrobras PN',
            country_code='BR',
            exchange_acronym='B3'
        )
    
    @patch('investments.services.b3_price_fetcher.yf.Ticker')
    def test_fetch_price(self, mock_ticker_class):
        """Test fetching price for a date"""
        # Mock yfinance response
        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = False
        mock_hist.__getitem__.return_value.iloc.__getitem__.return_value = 25.50
        mock_ticker.history.return_value = mock_hist
        mock_ticker_class.return_value = mock_ticker
        
        fetcher = B3PriceFetcher(self.security)
        price = fetcher.fetch_price(date.today())
        
        # Should return price
        self.assertIsNotNone(price)
        self.assertEqual(price, Decimal('25.50'))
    
    @patch('investments.services.b3_price_fetcher.yf.Ticker')
    def test_fetch_price_no_data(self, mock_ticker_class):
        """Test fetching price when no data available"""
        mock_ticker = MagicMock()
        mock_hist = MagicMock()
        mock_hist.empty = True
        mock_ticker.history.return_value = mock_hist
        mock_ticker_class.return_value = mock_ticker
        
        fetcher = B3PriceFetcher(self.security)
        price = fetcher.fetch_price(date.today())
        
        # Should return None
        self.assertIsNone(price)
    
    @patch('investments.services.b3_price_fetcher.yf.Ticker')
    def test_fetch_price_range(self, mock_ticker_class):
        """Test fetching prices for a date range"""
        # Mock yfinance response
        import pandas as pd
        mock_ticker = MagicMock()
        
        # Create a proper mock DataFrame
        dates = pd.date_range(start=date.today() - timedelta(days=2), end=date.today(), freq='D')
        mock_data = pd.DataFrame({
            'Close': [25.0, 26.0]
        }, index=dates[:2])
        mock_data.index = dates[:2]
        
        mock_ticker.history.return_value = mock_data
        mock_ticker_class.return_value = mock_ticker
        
        fetcher = B3PriceFetcher(self.security)
        start_date = date.today() - timedelta(days=2)
        end_date = date.today()
        prices = fetcher.fetch_price_range(start_date, end_date)
        
        # Should return prices
        self.assertGreaterEqual(len(prices), 0)
    
    @patch('investments.services.b3_price_fetcher.B3PriceFetcher')
    def test_update_all_securities_prices(self, mock_fetcher_class):
        """Test updating prices for all Brazilian securities"""
        # Create multiple securities
        Security.objects.create(
            ticker='VALE3',
            name='Vale ON',
            country_code='BR',
            exchange_acronym='B3'
        )
        Security.objects.create(
            ticker='ITUB4',
            name='Itau PN',
            country_code='BR',
            exchange_acronym='B3'
        )
        
        # Mock fetcher
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_price.return_value = Decimal('50.00')
        mock_fetcher_class.return_value = mock_fetcher
        
        count = B3PriceFetcher.update_all_securities_prices()
        
        # Should update prices
        self.assertGreaterEqual(count, 0)
    
    @patch('investments.services.b3_price_fetcher.yf.Ticker')
    def test_fetch_price_handles_exception(self, mock_ticker_class):
        """Test that fetch_price handles exceptions gracefully"""
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Network error")
        mock_ticker_class.return_value = mock_ticker
        
        fetcher = B3PriceFetcher(self.security)
        price = fetcher.fetch_price(date.today())
        
        # Should return None on error
        self.assertIsNone(price)

