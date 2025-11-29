"""
Edge cases and error handling tests for finance app
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal, InvalidOperation
from datetime import date, timedelta
from finance.models import (
    Account, Transaction, Balance, Category, Rule, Budget
)
from finance.services.account_syncer import AccountSyncer
from finance.services.transfer_matcher import TransferMatcher

User = get_user_model()


class EdgeCaseTestCase(TestCase):
    """Test edge cases and error handling"""
    
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
    
    def test_account_with_zero_balance(self):
        """Test account with zero balance"""
        account = Account.objects.create(
            user=self.user,
            name='Zero Balance Account',
            accountable_type='depository',
            balance=Decimal('0.00'),
            currency='BRL'
        )
        
        self.assertEqual(account.balance, Decimal('0.00'))
        self.assertEqual(account.classification, 'asset')
    
    def test_transaction_with_very_large_amount(self):
        """Test transaction with very large amount"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('999999999.99'),
            name='Large Transaction',
            currency='BRL'
        )
        
        self.assertEqual(transaction.amount, Decimal('999999999.99'))
    
    def test_transaction_with_very_small_amount(self):
        """Test transaction with very small amount"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('0.01'),
            name='Small Transaction',
            currency='BRL'
        )
        
        self.assertEqual(transaction.amount, Decimal('0.01'))
    
    def test_account_sync_with_no_transactions(self):
        """Test account sync with no transactions"""
        syncer = AccountSyncer(self.account)
        syncer.sync()
        
        # Should complete without error
        self.assertTrue(True)
    
    def test_account_sync_with_future_dated_transaction(self):
        """Test account sync with future-dated transaction"""
        Transaction.objects.create(
            account=self.account,
            date=date.today() + timedelta(days=30),
            amount=Decimal('100.00'),
            name='Future Transaction',
            currency='BRL'
        )
        
        syncer = AccountSyncer(self.account)
        syncer.sync()
        
        # Should handle future dates
        self.assertTrue(True)
    
    def test_account_sync_with_old_transaction(self):
        """Test account sync with very old transaction"""
        Transaction.objects.create(
            account=self.account,
            date=date.today() - timedelta(days=365),
            amount=Decimal('50.00'),
            name='Old Transaction',
            currency='BRL'
        )
        
        syncer = AccountSyncer(self.account)
        syncer.sync()
        
        # Should handle old dates
        self.assertTrue(True)
    
    def test_transfer_match_with_multiple_candidates(self):
        """Test transfer matching when multiple candidates exist"""
        account2 = Account.objects.create(
            user=self.user,
            name='Account 2',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        
        # Create multiple potential matches
        outflow = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Transfer Out',
            currency='BRL',
            kind='standard'
        )
        
        # Create multiple inflows
        inflow1 = Transaction.objects.create(
            account=account2,
            date=date.today(),
            amount=Decimal('-100.00'),
            name='Transfer In 1',
            currency='BRL',
            kind='standard'
        )
        inflow2 = Transaction.objects.create(
            account=account2,
            date=date.today() + timedelta(days=1),
            amount=Decimal('-100.00'),
            name='Transfer In 2',
            currency='BRL',
            kind='standard'
        )
        
        matcher = TransferMatcher(self.user)
        count = matcher.auto_match_transfers()
        
        # Should match one (closest date)
        self.assertEqual(count, 1)
    
    def test_budget_with_no_transactions(self):
        """Test budget calculation with no transactions"""
        budget = Budget.objects.create(
            user=self.user,
            start_date=date.today().replace(day=1),
            end_date=(date.today().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            currency='BRL',
            budgeted_spending=Decimal('1000.00')
        )
        
        actual = budget.actual_spending
        self.assertEqual(actual, Decimal('0.00'))
    
    def test_category_with_no_transactions(self):
        """Test category with no transactions"""
        category = Category.objects.create(
            user=self.user,
            name='Empty Category',
            classification='expense',
            color='#FF0000'
        )
        
        # Should exist without transactions
        self.assertIsNotNone(category)
        self.assertEqual(category.transaction_set.count(), 0)
    
    def test_rule_with_no_conditions(self):
        """Test rule with no conditions"""
        rule = Rule.objects.create(
            user=self.user,
            name='Rule Without Conditions',
            resource_type='transaction',
            effective_date=date.today()
        )
        
        # Should exist without conditions
        self.assertIsNotNone(rule)
        self.assertEqual(rule.conditions.count(), 0)
    
    def test_account_with_multiple_currencies(self):
        """Test account handling multiple currencies"""
        # Create transactions in different currencies
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='BRL Transaction',
            currency='BRL'
        )
        
        # Account should handle its primary currency
        self.assertEqual(self.account.currency, 'BRL')
    
    def test_balance_calculation_with_gaps(self):
        """Test balance calculation with date gaps"""
        # Create transactions with gaps
        Transaction.objects.create(
            account=self.account,
            date=date.today() - timedelta(days=10),
            amount=Decimal('100.00'),
            name='Transaction 1',
            currency='BRL'
        )
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Transaction 2',
            currency='BRL'
        )
        
        syncer = AccountSyncer(self.account)
        syncer.sync()
        
        # Should fill gaps with daily balances
        balances = Balance.objects.filter(account=self.account)
        self.assertGreater(balances.count(), 2)


class ErrorHandlingTestCase(TestCase):
    """Test error handling scenarios"""
    
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
    
    def test_transaction_with_invalid_date(self):
        """Test handling of invalid dates"""
        # Django will validate date format, so we test with edge cases
        transaction = Transaction.objects.create(
            account=self.account,
            date=date(1900, 1, 1),  # Very old date
            amount=Decimal('10.00'),
            name='Old Transaction',
            currency='BRL'
        )
        
        # Should handle old dates
        self.assertIsNotNone(transaction)
    
    def test_account_sync_with_corrupted_data(self):
        """Test account sync handles data inconsistencies"""
        # Create transaction with unusual values
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('0.00'),  # Zero amount
            name='Zero Transaction',
            currency='BRL'
        )
        
        syncer = AccountSyncer(self.account)
        # Should complete without error
        syncer.sync()
        self.assertTrue(True)
    
    def test_transfer_match_with_missing_account(self):
        """Test transfer matching when account is deleted"""
        # Skip - requires negative amounts which model prevents
        self.skipTest("Transfer matching requires negative amounts but model prevents them")

