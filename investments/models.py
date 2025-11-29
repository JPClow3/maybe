import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from finance.models import Account


class Security(models.Model):
    """Security (stock, ETF, etc.) - supports B3 tickers like PETR4.SA"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticker = models.CharField(max_length=20, unique=True, help_text='Ticker symbol (e.g., PETR4.SA for B3)')
    name = models.CharField(max_length=255, blank=True)
    country_code = models.CharField(max_length=2, default='BR', help_text='ISO country code')
    exchange_mic = models.CharField(max_length=10, blank=True, help_text='Market Identifier Code')
    exchange_acronym = models.CharField(max_length=20, blank=True)
    exchange_operating_mic = models.CharField(max_length=10, blank=True)
    logo_url = models.URLField(blank=True)
    
    # Health tracking
    offline = models.BooleanField(default=False)
    failed_fetch_at = models.DateTimeField(null=True, blank=True)
    failed_fetch_count = models.IntegerField(default=0)
    last_health_check_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'securities'
        verbose_name_plural = 'securities'
        indexes = [
            models.Index(fields=['country_code']),
            models.Index(fields=['exchange_operating_mic']),
        ]
    
    def __str__(self):
        return f"{self.ticker} - {self.name or 'Unknown'}"


class SecurityPrice(models.Model):
    """Historical price for a security"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField()
    price = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal('0'))])
    currency = models.CharField(max_length=3, default='BRL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'security_prices'
        unique_together = [['security', 'date', 'currency']]
        indexes = [
            models.Index(fields=['security', 'date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.security.ticker} @ {self.date}: {self.price} {self.currency}"


class Holding(models.Model):
    """Holding of a security in an investment account"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='holdings')
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='holdings')
    date = models.DateField()
    qty = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal('0'))])
    price = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal('0'))])
    amount = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal('0'))])
    currency = models.CharField(max_length=3, default='BRL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'holdings'
        unique_together = [['account', 'security', 'date', 'currency']]
        indexes = [
            models.Index(fields=['account', 'security', 'date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.security.ticker} x {self.qty} @ {self.price} = {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount if not provided
        if not self.amount and self.qty and self.price:
            self.amount = self.qty * self.price
        super().save(*args, **kwargs)


class Trade(models.Model):
    """Trade (buy/sell) of a security"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='trades')
    security = models.ForeignKey(Security, on_delete=models.CASCADE, related_name='trades')
    date = models.DateField()
    qty = models.DecimalField(max_digits=19, decimal_places=4, help_text='Positive for buy, negative for sell')
    price = models.DecimalField(max_digits=19, decimal_places=4, validators=[MinValueValidator(Decimal('0'))])
    amount = models.DecimalField(max_digits=19, decimal_places=4, help_text='qty * price (negative for buy, positive for sell)')
    currency = models.CharField(max_length=3, default='BRL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trades'
        indexes = [
            models.Index(fields=['account', 'security', 'date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        action = "Buy" if self.qty > 0 else "Sell"
        return f"{action} {abs(self.qty)} {self.security.ticker} @ {self.price} = {abs(self.amount)} {self.currency}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate amount if not provided
        if not self.amount and self.qty and self.price:
            self.amount = self.qty * self.price
        super().save(*args, **kwargs)
    
    @property
    def is_buy(self):
        return self.qty > 0
    
    @property
    def is_sell(self):
        return self.qty < 0

