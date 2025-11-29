"""
Money utility class for handling currency amounts and formatting.
Ported from lib/money.rb
"""
from decimal import Decimal
from datetime import date
from typing import Optional, Union
from django.conf import settings
from .models import ExchangeRate


class ConversionError(Exception):
    """Raised when currency conversion fails"""
    def __init__(self, from_currency: str, to_currency: str, conversion_date: date):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.date = conversion_date
        super().__init__(
            f"Couldn't find exchange rate from {from_currency} to {to_currency} on {conversion_date}"
        )


class Currency:
    """Currency information and formatting"""
    
    # Common currency data (simplified - can be extended with full currencies.yml)
    CURRENCIES = {
        'BRL': {
            'name': 'Brazilian Real',
            'symbol': 'R$',
            'iso_code': 'BRL',
            'separator': ',',
            'delimiter': '.',
            'default_format': '%u %n',
            'default_precision': 2,
        },
        'USD': {
            'name': 'US Dollar',
            'symbol': '$',
            'iso_code': 'USD',
            'separator': '.',
            'delimiter': ',',
            'default_format': '%u%n',
            'default_precision': 2,
        },
        'EUR': {
            'name': 'Euro',
            'symbol': '€',
            'iso_code': 'EUR',
            'separator': ',',
            'delimiter': '.',
            'default_format': '%u %n',
            'default_precision': 2,
        },
    }
    
    _instances = {}
    
    def __init__(self, iso_code: str):
        iso_code = iso_code.upper()
        if iso_code not in self.CURRENCIES:
            raise ValueError(f"Unknown currency: {iso_code}")
        
        currency_data = self.CURRENCIES[iso_code]
        self.iso_code = currency_data['iso_code']
        self.name = currency_data['name']
        self.symbol = currency_data['symbol']
        self.separator = currency_data['separator']
        self.delimiter = currency_data['delimiter']
        self.default_format = currency_data['default_format']
        self.default_precision = currency_data['default_precision']
    
    @classmethod
    def new(cls, iso_code: Union[str, 'Currency']) -> 'Currency':
        """Get or create Currency instance"""
        if isinstance(iso_code, Currency):
            iso_code = iso_code.iso_code
        iso_code = str(iso_code).upper()
        
        if iso_code not in cls._instances:
            cls._instances[iso_code] = cls(iso_code)
        return cls._instances[iso_code]
    
    def step(self) -> Decimal:
        """Step value for number inputs"""
        return Decimal(1) / (10 ** self.default_precision)
    
    def __eq__(self, other):
        if not isinstance(other, Currency):
            return False
        return self.iso_code == other.iso_code
    
    def __hash__(self):
        return hash(self.iso_code)
    
    def __repr__(self):
        return f"Currency({self.iso_code})"


class Money:
    """Money class for handling currency amounts"""
    
    _default_currency = None
    
    def __init__(
        self, 
        amount: Union[Decimal, float, int, 'Money'], 
        currency: Union[str, Currency] = None,
        store=None
    ):
        if isinstance(amount, Money):
            self.amount = amount.amount
            self.currency = amount.currency
        else:
            self.amount = Decimal(str(amount))
            if currency is None:
                currency = self.default_currency()
            self.currency = Currency.new(currency) if isinstance(currency, str) else currency
        
        self.store = store or ExchangeRate
    
    @classmethod
    def default_currency(cls) -> Currency:
        """Get default currency (BRL for Brazil)"""
        if cls._default_currency is None:
            default_iso = getattr(settings, 'DEFAULT_CURRENCY', 'BRL')
            cls._default_currency = Currency.new(default_iso)
        return cls._default_currency
    
    @classmethod
    def set_default_currency(cls, currency: Union[str, Currency]):
        """Set default currency"""
        cls._default_currency = Currency.new(currency)
    
    def exchange_to(
        self, 
        other_currency: Union[str, Currency], 
        conversion_date: date = None,
        fallback_rate: Optional[Decimal] = None
    ) -> 'Money':
        """Exchange to another currency"""
        if conversion_date is None:
            from django.utils import timezone
            conversion_date = timezone.now().date()
        
        other_currency = Currency.new(other_currency) if isinstance(other_currency, str) else other_currency
        
        if self.currency.iso_code == other_currency.iso_code:
            return self
        
        # Try to get exchange rate
        exchange_rate = None
        try:
            rate_obj = self.store.objects.filter(
                from_currency=self.currency.iso_code,
                to_currency=other_currency.iso_code,
                date=conversion_date
            ).first()
            if rate_obj:
                exchange_rate = rate_obj.rate
        except Exception:
            pass
        
        if exchange_rate is None:
            exchange_rate = fallback_rate
        
        if exchange_rate is None:
            raise ConversionError(
                self.currency.iso_code,
                other_currency.iso_code,
                conversion_date
            )
        
        new_amount = self.amount * exchange_rate
        return Money(new_amount, other_currency, store=self.store)
    
    def format(self, locale: str = None) -> str:
        """Format money as currency string"""
        # Simplified formatting - can be enhanced with locale support
        amount_str = f"{self.amount:,.{self.currency.default_precision}f}"
        
        # Apply delimiter and separator
        parts = amount_str.split('.')
        integer_part = parts[0].replace(',', self.currency.delimiter)
        decimal_part = parts[1] if len(parts) > 1 else '00'
        
        formatted_amount = f"{integer_part}{self.currency.separator}{decimal_part}"
        
        # Apply format
        if '%u' in self.currency.default_format and '%n' in self.currency.default_format:
            return self.currency.default_format.replace('%u', self.currency.symbol).replace('%n', formatted_amount)
        else:
            return f"{self.currency.symbol} {formatted_amount}"
    
    def __str__(self):
        return self.format()
    
    def __repr__(self):
        return f"Money({self.amount}, {self.currency.iso_code})"
    
    # Arithmetic operations
    def __add__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot add Money with different currencies")
            return Money(self.amount + other.amount, self.currency, store=self.store)
        return Money(self.amount + Decimal(str(other)), self.currency, store=self.store)
    
    def __sub__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot subtract Money with different currencies")
            return Money(self.amount - other.amount, self.currency, store=self.store)
        return Money(self.amount - Decimal(str(other)), self.currency, store=self.store)
    
    def __mul__(self, other):
        if isinstance(other, Money):
            raise TypeError("Cannot multiply Money by Money")
        return Money(self.amount * Decimal(str(other)), self.currency, store=self.store)
    
    def __truediv__(self, other):
        if isinstance(other, Money):
            return self.amount / other.amount
        return Money(self.amount / Decimal(str(other)), self.currency, store=self.store)
    
    def __neg__(self):
        return Money(-self.amount, self.currency, store=self.store)
    
    def __abs__(self):
        return Money(abs(self.amount), self.currency, store=self.store)
    
    def __eq__(self, other):
        if isinstance(other, Money):
            return self.amount == other.amount and self.currency == other.currency
        return False
    
    def __lt__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot compare Money with different currencies")
            return self.amount < other.amount
        return self.amount < Decimal(str(other))
    
    def __le__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot compare Money with different currencies")
            return self.amount <= other.amount
        return self.amount <= Decimal(str(other))
    
    def __gt__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot compare Money with different currencies")
            return self.amount > other.amount
        return self.amount > Decimal(str(other))
    
    def __ge__(self, other):
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise ValueError("Cannot compare Money with different currencies")
            return self.amount >= other.amount
        return self.amount >= Decimal(str(other))
    
    def __bool__(self):
        return self.amount != 0
    
    def as_json(self):
        """Return JSON representation"""
        return {
            'amount': str(self.amount),
            'currency': self.currency.iso_code,
            'formatted': str(self)
        }

