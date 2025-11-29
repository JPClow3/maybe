"""
Tests for finance.rules.filters module
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from finance.models import Account, Transaction, Merchant, Rule
from finance.rules.filters import (
    TransactionNameFilter,
    TransactionAmountFilter,
    TransactionMerchantFilter
)

User = get_user_model()


class TransactionNameFilterTestCase(TestCase):
    """Test TransactionNameFilter"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        self.rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.filter_obj = TransactionNameFilter(self.rule)
        
        # Create test transactions
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Uber Ride',
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('200.00'),
            name='Amazon Purchase',
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('300.00'),
            name='Grocery Store',
            currency='BRL'
        )
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.filter_obj.type, 'text')
    
    def test_apply_like_operator(self):
        """Test applying like operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, 'like', 'Uber')
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Uber Ride')
    
    def test_apply_like_operator_case_insensitive(self):
        """Test like operator is case insensitive"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, 'like', 'uber')
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Uber Ride')
    
    def test_apply_equal_operator(self):
        """Test applying = operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', 'Uber Ride')
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Uber Ride')
    
    def test_apply_equal_operator_case_insensitive(self):
        """Test = operator is case insensitive"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', 'uber ride')
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Uber Ride')
    
    def test_apply_unsupported_operator(self):
        """Test applying unsupported operator raises ValueError"""
        queryset = Transaction.objects.filter(account__user=self.user)
        with self.assertRaises(ValueError):
            self.filter_obj.apply(queryset, '>', 'Uber')
    
    def test_apply_no_matches(self):
        """Test applying filter with no matches"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, 'like', 'NonExistent')
        
        self.assertEqual(result.count(), 0)


class TransactionAmountFilterTestCase(TestCase):
    """Test TransactionAmountFilter"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        self.rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.filter_obj = TransactionAmountFilter(self.rule)
        
        # Create test transactions
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Small Transaction',
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Medium Transaction',
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('200.00'),
            name='Large Transaction',
            currency='BRL'
        )
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.filter_obj.type, 'number')
    
    def test_apply_greater_than(self):
        """Test applying > operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '>', Decimal('100.00'))
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Large Transaction')
    
    def test_apply_greater_equal(self):
        """Test applying >= operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '>=', Decimal('100.00'))
        
        self.assertEqual(result.count(), 2)  # 100 and 200
    
    def test_apply_less_than(self):
        """Test applying < operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '<', Decimal('100.00'))
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Small Transaction')
    
    def test_apply_less_equal(self):
        """Test applying <= operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '<=', Decimal('100.00'))
        
        self.assertEqual(result.count(), 2)  # 50 and 100
    
    def test_apply_equal(self):
        """Test applying = operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', Decimal('100.00'))
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Medium Transaction')
    
    def test_apply_with_string_value(self):
        """Test applying filter with string value converts to Decimal"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', '100.00')
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, 'Medium Transaction')
    
    def test_apply_unsupported_operator(self):
        """Test applying unsupported operator raises ValueError"""
        queryset = Transaction.objects.filter(account__user=self.user)
        with self.assertRaises(ValueError):
            self.filter_obj.apply(queryset, 'like', Decimal('100.00'))
    
    def test_apply_no_matches(self):
        """Test applying filter with no matches"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '>', Decimal('1000.00'))
        
        self.assertEqual(result.count(), 0)


class TransactionMerchantFilterTestCase(TestCase):
    """Test TransactionMerchantFilter"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Test Account',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        self.merchant1 = Merchant.objects.create(
            user=self.user,
            name='Amazon',
            color='#FF0000'
        )
        self.merchant2 = Merchant.objects.create(
            user=self.user,
            name='Uber',
            color='#0000FF'
        )
        self.rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.filter_obj = TransactionMerchantFilter(self.rule)
        
        # Create test transactions
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Amazon Purchase',
            merchant=self.merchant1,
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('200.00'),
            name='Uber Ride',
            merchant=self.merchant2,
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('300.00'),
            name='No Merchant',
            currency='BRL'
        )
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.filter_obj.type, 'select')
    
    def test_options_property(self):
        """Test options property returns merchants"""
        options = self.filter_obj.options
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
        # Check format: [(name, id), ...]
        self.assertIsInstance(options[0], tuple)
        self.assertEqual(len(options[0]), 2)
    
    def test_apply_equal_operator(self):
        """Test applying = operator"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', str(self.merchant1.id))
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().merchant, self.merchant1)
    
    def test_apply_equal_operator_merchant2(self):
        """Test applying = operator for second merchant"""
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', str(self.merchant2.id))
        
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().merchant, self.merchant2)
    
    def test_apply_unsupported_operator(self):
        """Test applying unsupported operator raises ValueError"""
        queryset = Transaction.objects.filter(account__user=self.user)
        with self.assertRaises(ValueError):
            self.filter_obj.apply(queryset, '>', str(self.merchant1.id))
    
    def test_apply_no_matches(self):
        """Test applying filter with no matches"""
        # Create merchant for different user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_merchant = Merchant.objects.create(
            user=other_user,
            name='Other Merchant',
            color='#00FF00'
        )
        
        queryset = Transaction.objects.filter(account__user=self.user)
        result = self.filter_obj.apply(queryset, '=', str(other_merchant.id))
        
        self.assertEqual(result.count(), 0)

