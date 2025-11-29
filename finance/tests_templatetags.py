"""
Unit tests for template filters
"""
from django.test import TestCase, RequestFactory
from django.template import Template, Context
from decimal import Decimal
from finance.templatetags.money_filters import real_br, real_br_plain


class MoneyFiltersTestCase(TestCase):
    """Test money template filters"""
    
    def test_real_br_decimal(self):
        """Test real_br filter with Decimal"""
        value = Decimal('1234.56')
        result = real_br(value)
        self.assertIn('R$', result)
        self.assertIn('1.234,56', result)
        self.assertIn('font-tabular-nums', result)
    
    def test_real_br_integer(self):
        """Test real_br filter with integer"""
        value = 1000
        result = real_br(value)
        self.assertIn('R$', result)
        self.assertIn('1.000,00', result)
    
    def test_real_br_float(self):
        """Test real_br filter with float"""
        value = 50.75
        result = real_br(value)
        self.assertIn('R$', result)
    
    def test_real_br_string(self):
        """Test real_br filter with string"""
        value = '99.99'
        result = real_br(value)
        self.assertIn('R$', result)
    
    def test_real_br_none(self):
        """Test real_br filter with None"""
        result = real_br(None)
        self.assertIn('—', result)
        self.assertIn('text-gray-500', result)
    
    def test_real_br_large_number(self):
        """Test real_br filter with large number"""
        value = Decimal('1234567.89')
        result = real_br(value)
        self.assertIn('R$', result)
        # Should format with thousands separator
        self.assertIn('1.234.567,89', result)
    
    def test_real_br_negative(self):
        """Test real_br filter with negative number"""
        value = Decimal('-100.50')
        result = real_br(value)
        self.assertIn('R$', result)
        # Money class should handle negative sign
    
    def test_real_br_zero(self):
        """Test real_br filter with zero"""
        value = Decimal('0')
        result = real_br(value)
        self.assertIn('R$', result)
        self.assertIn('0,00', result)
    
    def test_real_br_plain_decimal(self):
        """Test real_br_plain filter with Decimal"""
        value = Decimal('1234.56')
        result = real_br_plain(value)
        self.assertIn('R$', result)
        self.assertIn('1.234,56', result)
        # Should not contain HTML tags
        self.assertNotIn('<span', result)
        self.assertNotIn('font-tabular-nums', result)
    
    def test_real_br_plain_integer(self):
        """Test real_br_plain filter with integer"""
        value = 500
        result = real_br_plain(value)
        self.assertIn('R$', result)
        self.assertIn('500,00', result)
    
    def test_real_br_plain_none(self):
        """Test real_br_plain filter with None"""
        result = real_br_plain(None)
        self.assertEqual(result, '—')
        # Should not contain HTML
        self.assertNotIn('<', result)
    
    def test_real_br_invalid_value(self):
        """Test real_br filter with invalid value"""
        # Should return string representation
        result = real_br('invalid')
        self.assertIsInstance(result, str)
    
    def test_real_br_currency_parameter(self):
        """Test real_br filter with custom currency"""
        value = Decimal('100.00')
        result = real_br(value, 'USD')
        # Should format according to currency
        self.assertIsInstance(result, str)
    
    def test_real_br_in_template(self):
        """Test real_br filter in template context"""
        template = Template('{% load money_filters %}{{ value|real_br }}')
        context = Context({'value': Decimal('1234.56')})
        result = template.render(context)
        self.assertIn('R$', result)
        self.assertIn('1.234,56', result)
    
    def test_real_br_plain_in_template(self):
        """Test real_br_plain filter in template context"""
        template = Template('{% load money_filters %}{{ value|real_br_plain }}')
        context = Context({'value': Decimal('567.89')})
        result = template.render(context)
        self.assertIn('R$', result)
        self.assertIn('567,89', result)
        self.assertNotIn('<span', result)

