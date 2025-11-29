"""
Tests for finance.rules.executors module
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from finance.models import Account, Transaction, Category, Tag, Merchant, TransactionTag, Rule, RuleAction
from finance.rules.executors import (
    SetTransactionCategoryExecutor,
    SetTransactionTagsExecutor,
    SetTransactionMerchantExecutor,
    SetTransactionNameExecutor
)

User = get_user_model()


class SetTransactionCategoryExecutorTestCase(TestCase):
    """Test SetTransactionCategoryExecutor"""
    
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
        self.category1 = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
        self.category2 = Category.objects.create(
            user=self.user,
            name='Transport',
            classification='expense',
            color='#0000FF'
        )
        self.rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.executor = SetTransactionCategoryExecutor(self.rule)
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.executor.type, 'select')
    
    def test_options_property(self):
        """Test options property returns categories"""
        options = self.executor.options
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
        # Check format: [(name, id), ...]
        self.assertIsInstance(options[0], tuple)
        self.assertEqual(len(options[0]), 2)
    
    def test_execute_with_value(self):
        """Test executing with category value"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.category1.id))
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.category1)
    
    def test_execute_without_value(self):
        """Test executing without value does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        original_category = transaction.category
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=None)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, original_category)
    
    def test_execute_with_invalid_category(self):
        """Test executing with invalid category ID does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='00000000-0000-0000-0000-000000000000')
        
        transaction.refresh_from_db()
        self.assertIsNone(transaction.category)
    
    def test_execute_ignores_existing_category(self):
        """Test that executor doesn't overwrite existing category by default"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            category=self.category1,
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.category2.id))
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.category1)  # Unchanged
    
    def test_execute_with_ignore_locks(self):
        """Test executing with ignore_attribute_locks=True"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            category=self.category1,
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.category2.id), ignore_attribute_locks=True)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.category2)  # Changed


class SetTransactionTagsExecutorTestCase(TestCase):
    """Test SetTransactionTagsExecutor"""
    
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
        self.tag1 = Tag.objects.create(
            user=self.user,
            name='Important',
            color='#FF0000'
        )
        self.tag2 = Tag.objects.create(
            user=self.user,
            name='Work',
            color='#0000FF'
        )
        self.rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.executor = SetTransactionTagsExecutor(self.rule)
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.executor.type, 'select')
    
    def test_options_property(self):
        """Test options property returns tags"""
        options = self.executor.options
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
    
    def test_execute_with_value(self):
        """Test executing with tag value"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.tag1.id))
        
        # Check tag was added
        self.assertTrue(TransactionTag.objects.filter(transaction=transaction, tag=self.tag1).exists())
    
    def test_execute_without_value(self):
        """Test executing without value does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=None)
        
        # No tags should be added
        self.assertEqual(TransactionTag.objects.filter(transaction=transaction).count(), 0)
    
    def test_execute_with_invalid_tag(self):
        """Test executing with invalid tag ID does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='00000000-0000-0000-0000-000000000000')
        
        # No tags should be added
        self.assertEqual(TransactionTag.objects.filter(transaction=transaction).count(), 0)
    
    def test_execute_doesnt_duplicate_tags(self):
        """Test that executor doesn't add duplicate tags"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        # Add tag manually first
        TransactionTag.objects.create(transaction=transaction, tag=self.tag1)
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.tag1.id))
        
        # Should still only have one tag
        self.assertEqual(TransactionTag.objects.filter(transaction=transaction, tag=self.tag1).count(), 1)
    
    def test_execute_with_ignore_locks(self):
        """Test executing with ignore_attribute_locks=True still adds tag"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.tag1.id), ignore_attribute_locks=True)
        
        # Tag should be added
        self.assertTrue(TransactionTag.objects.filter(transaction=transaction, tag=self.tag1).exists())


class SetTransactionMerchantExecutorTestCase(TestCase):
    """Test SetTransactionMerchantExecutor"""
    
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
        self.executor = SetTransactionMerchantExecutor(self.rule)
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.executor.type, 'select')
    
    def test_options_property(self):
        """Test options property returns merchants"""
        options = self.executor.options
        self.assertIsInstance(options, list)
        self.assertGreater(len(options), 0)
    
    def test_execute_with_value(self):
        """Test executing with merchant value"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.merchant1.id))
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.merchant, self.merchant1)
    
    def test_execute_without_value(self):
        """Test executing without value does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=None)
        
        transaction.refresh_from_db()
        self.assertIsNone(transaction.merchant)
    
    def test_execute_with_invalid_merchant(self):
        """Test executing with invalid merchant ID does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='00000000-0000-0000-0000-000000000000')
        
        transaction.refresh_from_db()
        self.assertIsNone(transaction.merchant)
    
    def test_execute_ignores_existing_merchant(self):
        """Test that executor doesn't overwrite existing merchant by default"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            merchant=self.merchant1,
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.merchant2.id))
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.merchant, self.merchant1)  # Unchanged
    
    def test_execute_with_ignore_locks(self):
        """Test executing with ignore_attribute_locks=True"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            merchant=self.merchant1,
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=str(self.merchant2.id), ignore_attribute_locks=True)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.merchant, self.merchant2)  # Changed


class SetTransactionNameExecutorTestCase(TestCase):
    """Test SetTransactionNameExecutor"""
    
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
        self.executor = SetTransactionNameExecutor(self.rule)
    
    def test_type_property(self):
        """Test type property"""
        self.assertEqual(self.executor.type, 'text')
    
    def test_options_property(self):
        """Test options property returns None"""
        self.assertIsNone(self.executor.options)
    
    def test_execute_with_value(self):
        """Test executing with name value"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='New Name')
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'New Name')
    
    def test_execute_without_value(self):
        """Test executing without value does nothing"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Original Name',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value=None)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'Original Name')
    
    def test_execute_ignores_existing_name(self):
        """Test that executor doesn't overwrite existing name by default"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Original Name',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='New Name')
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'Original Name')  # Unchanged
    
    def test_execute_with_null_name(self):
        """Test executing updates null name"""
        # Transaction name cannot be null, so we'll test with empty string instead
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='New Name')
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'New Name')
    
    def test_execute_with_empty_name(self):
        """Test executing updates empty name"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='New Name')
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'New Name')
    
    def test_execute_with_ignore_locks(self):
        """Test executing with ignore_attribute_locks=True"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Original Name',
            currency='BRL'
        )
        
        queryset = Transaction.objects.filter(id=transaction.id)
        self.executor.execute(queryset, value='New Name', ignore_attribute_locks=True)
        
        transaction.refresh_from_db()
        self.assertEqual(transaction.name, 'New Name')  # Changed

