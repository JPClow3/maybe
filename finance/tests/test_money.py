"""
Tests for finance.money module
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from finance.money import Money, Currency, ConversionError
from finance.models import ExchangeRate, Account

User = get_user_model()


class CurrencyTestCase(TestCase):
    """Test Currency class"""
    
    def setUp(self):
        # Clear currency instances cache
        Currency._instances = {}
    
    def test_currency_creation(self):
        """Test creating currency instances"""
        currency = Currency.new('BRL')
        self.assertEqual(currency.iso_code, 'BRL')
        self.assertEqual(currency.name, 'Brazilian Real')
        self.assertEqual(currency.symbol, 'R$')
        self.assertEqual(currency.separator, ',')
        self.assertEqual(currency.delimiter, '.')
    
    def test_currency_uppercase(self):
        """Test that currency codes are converted to uppercase"""
        currency = Currency.new('usd')
        self.assertEqual(currency.iso_code, 'USD')
    
    def test_currency_from_currency_instance(self):
        """Test creating currency from existing Currency instance"""
        currency1 = Currency.new('BRL')
        currency2 = Currency.new(currency1)
        self.assertIs(currency1, currency2)  # Should return same instance
    
    def test_currency_singleton(self):
        """Test that Currency instances are cached"""
        currency1 = Currency.new('BRL')
        currency2 = Currency.new('BRL')
        self.assertIs(currency1, currency2)
    
    def test_currency_unknown(self):
        """Test that unknown currency raises ValueError"""
        with self.assertRaises(ValueError):
            Currency.new('XXX')
    
    def test_currency_step(self):
        """Test step value calculation"""
        currency = Currency.new('BRL')
        self.assertEqual(currency.step(), Decimal('0.01'))
    
    def test_currency_equality(self):
        """Test currency equality"""
        currency1 = Currency.new('BRL')
        currency2 = Currency.new('BRL')
        currency3 = Currency.new('USD')
        
        self.assertEqual(currency1, currency2)
        self.assertNotEqual(currency1, currency3)
        self.assertNotEqual(currency1, 'BRL')  # Not equal to string
    
    def test_currency_hash(self):
        """Test currency hashing"""
        currency = Currency.new('BRL')
        self.assertEqual(hash(currency), hash('BRL'))
    
    def test_currency_repr(self):
        """Test currency string representation"""
        currency = Currency.new('BRL')
        self.assertEqual(repr(currency), "Currency(BRL)")


class MoneyTestCase(TestCase):
    """Test Money class"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Clear currency instances cache
        Currency._instances = {}
        Money._default_currency = None
    
    def test_money_creation_from_decimal(self):
        """Test creating Money from Decimal"""
        money = Money(Decimal('100.50'), 'BRL')
        self.assertEqual(money.amount, Decimal('100.50'))
        self.assertEqual(money.currency.iso_code, 'BRL')
    
    def test_money_creation_from_float(self):
        """Test creating Money from float"""
        money = Money(100.50, 'BRL')
        self.assertEqual(money.amount, Decimal('100.50'))
    
    def test_money_creation_from_int(self):
        """Test creating Money from int"""
        money = Money(100, 'BRL')
        self.assertEqual(money.amount, Decimal('100'))
    
    def test_money_creation_from_money(self):
        """Test creating Money from another Money instance"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(money1)
        self.assertEqual(money2.amount, Decimal('100.50'))
        self.assertEqual(money2.currency.iso_code, 'BRL')
    
    def test_money_default_currency(self):
        """Test Money uses default currency when not specified"""
        money = Money(Decimal('100.50'))
        self.assertEqual(money.currency.iso_code, 'BRL')  # Default
    
    def test_money_set_default_currency(self):
        """Test setting default currency"""
        Money.set_default_currency('USD')
        money = Money(Decimal('100.50'))
        self.assertEqual(money.currency.iso_code, 'USD')
        # Reset for other tests
        Money.set_default_currency('BRL')
    
    def test_money_exchange_same_currency(self):
        """Test exchanging to same currency returns self"""
        money = Money(Decimal('100.50'), 'BRL')
        result = money.exchange_to('BRL')
        self.assertEqual(result.amount, Decimal('100.50'))
        self.assertEqual(result.currency.iso_code, 'BRL')
    
    def test_money_exchange_with_rate(self):
        """Test exchanging with exchange rate"""
        # Create exchange rate
        ExchangeRate.objects.create(
            from_currency='BRL',
            to_currency='USD',
            date=date.today(),
            rate=Decimal('0.20')
        )
        
        money = Money(Decimal('100.00'), 'BRL')
        result = money.exchange_to('USD', conversion_date=date.today())
        self.assertEqual(result.amount, Decimal('20.00'))
        self.assertEqual(result.currency.iso_code, 'USD')
    
    def test_money_exchange_with_fallback_rate(self):
        """Test exchanging with fallback rate"""
        money = Money(Decimal('100.00'), 'BRL')
        result = money.exchange_to('USD', fallback_rate=Decimal('0.25'))
        self.assertEqual(result.amount, Decimal('25.00'))
        self.assertEqual(result.currency.iso_code, 'USD')
    
    def test_money_exchange_no_rate(self):
        """Test exchanging without rate raises ConversionError"""
        money = Money(Decimal('100.00'), 'BRL')
        with self.assertRaises(ConversionError):
            money.exchange_to('USD', conversion_date=date.today())
    
    def test_money_format_brl(self):
        """Test formatting BRL currency"""
        money = Money(Decimal('1234.56'), 'BRL')
        formatted = money.format()
        # Should contain R$ and proper formatting
        self.assertIn('R$', formatted)
        self.assertIn('1.234', formatted)  # Delimiter
        self.assertIn('56', formatted)  # Decimal part
    
    def test_money_format_usd(self):
        """Test formatting USD currency"""
        money = Money(Decimal('1234.56'), 'USD')
        formatted = money.format()
        # Should contain $ symbol
        self.assertIn('$', formatted)
    
    def test_money_str(self):
        """Test Money string representation"""
        money = Money(Decimal('100.50'), 'BRL')
        str_repr = str(money)
        self.assertIn('R$', str_repr)
    
    def test_money_repr(self):
        """Test Money repr"""
        money = Money(Decimal('100.50'), 'BRL')
        self.assertEqual(repr(money), "Money(100.50, BRL)")
    
    def test_money_add_same_currency(self):
        """Test adding Money with same currency"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'BRL')
        result = money1 + money2
        self.assertEqual(result.amount, Decimal('150.75'))
        self.assertEqual(result.currency.iso_code, 'BRL')
    
    def test_money_add_different_currency(self):
        """Test adding Money with different currency raises ValueError"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'USD')
        with self.assertRaises(ValueError):
            money1 + money2
    
    def test_money_add_number(self):
        """Test adding number to Money"""
        money = Money(Decimal('100.50'), 'BRL')
        result = money + Decimal('50.25')
        self.assertEqual(result.amount, Decimal('150.75'))
    
    def test_money_subtract_same_currency(self):
        """Test subtracting Money with same currency"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'BRL')
        result = money1 - money2
        self.assertEqual(result.amount, Decimal('50.25'))
    
    def test_money_subtract_different_currency(self):
        """Test subtracting Money with different currency raises ValueError"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'USD')
        with self.assertRaises(ValueError):
            money1 - money2
    
    def test_money_multiply(self):
        """Test multiplying Money by number"""
        money = Money(Decimal('100.50'), 'BRL')
        result = money * Decimal('2')
        self.assertEqual(result.amount, Decimal('201.00'))
    
    def test_money_multiply_by_money(self):
        """Test multiplying Money by Money raises TypeError"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'BRL')
        with self.assertRaises(TypeError):
            money1 * money2
    
    def test_money_divide_by_number(self):
        """Test dividing Money by number"""
        money = Money(Decimal('100.50'), 'BRL')
        result = money / Decimal('2')
        self.assertEqual(result.amount, Decimal('50.25'))
    
    def test_money_divide_by_money(self):
        """Test dividing Money by Money returns ratio"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('50.25'), 'BRL')
        result = money1 / money2
        self.assertEqual(result, Decimal('2.00'))
    
    def test_money_neg(self):
        """Test negating Money"""
        money = Money(Decimal('100.50'), 'BRL')
        result = -money
        self.assertEqual(result.amount, Decimal('-100.50'))
    
    def test_money_abs(self):
        """Test absolute value of Money"""
        money = Money(Decimal('-100.50'), 'BRL')
        result = abs(money)
        self.assertEqual(result.amount, Decimal('100.50'))
    
    def test_money_equality(self):
        """Test Money equality"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('100.50'), 'BRL')
        money3 = Money(Decimal('100.50'), 'USD')
        money4 = Money(Decimal('200.00'), 'BRL')
        
        self.assertEqual(money1, money2)
        self.assertNotEqual(money1, money3)  # Different currency
        self.assertNotEqual(money1, money4)  # Different amount
        self.assertNotEqual(money1, Decimal('100.50'))  # Not equal to Decimal
    
    def test_money_less_than(self):
        """Test Money less than comparison"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('200.00'), 'BRL')
        
        self.assertLess(money1, money2)
        self.assertLess(money1, Decimal('200.00'))
    
    def test_money_less_than_different_currency(self):
        """Test comparing Money with different currency raises ValueError"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('200.00'), 'USD')
        with self.assertRaises(ValueError):
            money1 < money2
    
    def test_money_less_equal(self):
        """Test Money less than or equal comparison"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('100.50'), 'BRL')
        money3 = Money(Decimal('200.00'), 'BRL')
        
        self.assertLessEqual(money1, money2)
        self.assertLessEqual(money1, money3)
    
    def test_money_greater_than(self):
        """Test Money greater than comparison"""
        money1 = Money(Decimal('200.00'), 'BRL')
        money2 = Money(Decimal('100.50'), 'BRL')
        
        self.assertGreater(money1, money2)
        self.assertGreater(money1, Decimal('100.00'))
    
    def test_money_greater_equal(self):
        """Test Money greater than or equal comparison"""
        money1 = Money(Decimal('100.50'), 'BRL')
        money2 = Money(Decimal('100.50'), 'BRL')
        money3 = Money(Decimal('50.00'), 'BRL')
        
        self.assertGreaterEqual(money1, money2)
        self.assertGreaterEqual(money1, money3)
    
    def test_money_bool_true(self):
        """Test Money boolean when non-zero"""
        money = Money(Decimal('100.50'), 'BRL')
        self.assertTrue(money)
    
    def test_money_bool_false(self):
        """Test Money boolean when zero"""
        money = Money(Decimal('0'), 'BRL')
        self.assertFalse(money)
    
    def test_money_as_json(self):
        """Test Money JSON representation"""
        money = Money(Decimal('100.50'), 'BRL')
        json_data = money.as_json()
        
        self.assertEqual(json_data['amount'], '100.50')
        self.assertEqual(json_data['currency'], 'BRL')
        self.assertIn('formatted', json_data)


class ConversionErrorTestCase(TestCase):
    """Test ConversionError exception"""
    
    def test_conversion_error_message(self):
        """Test ConversionError message"""
        error = ConversionError('BRL', 'USD', date(2023, 1, 1))
        self.assertIn('BRL', str(error))
        self.assertIn('USD', str(error))
        self.assertIn('2023-01-01', str(error))
    
    def test_conversion_error_attributes(self):
        """Test ConversionError attributes"""
        error = ConversionError('BRL', 'USD', date(2023, 1, 1))
        self.assertEqual(error.from_currency, 'BRL')
        self.assertEqual(error.to_currency, 'USD')
        self.assertEqual(error.date, date(2023, 1, 1))

