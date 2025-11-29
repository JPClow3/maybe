"""Tests for finance app"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta
from finance.models import (
    Account, Transaction, Balance, Category, Tag, Merchant,
    Rule, RuleCondition, RuleAction, Budget, BudgetCategory
)

User = get_user_model()


class AccountTestCase(TestCase):
    """Test Account model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_account(self):
        """Test creating an account"""
        account = Account.objects.create(
            user=self.user,
            name='Test Checking',
            accountable_type='depository',
            balance=Decimal('1000.00'),
            currency='BRL'
        )
        self.assertEqual(account.name, 'Test Checking')
        self.assertEqual(account.accountable_type, 'depository')
        self.assertEqual(account.classification, 'asset')
    
    def test_account_classification(self):
        """Test account classification (asset vs liability)"""
        asset_account = Account.objects.create(
            user=self.user,
            name='Savings',
            accountable_type='depository',
            currency='BRL'
        )
        liability_account = Account.objects.create(
            user=self.user,
            name='Credit Card',
            accountable_type='credit_card',
            currency='BRL'
        )
        self.assertEqual(asset_account.classification, 'asset')
        self.assertEqual(liability_account.classification, 'liability')


class TransactionTestCase(TestCase):
    """Test Transaction model"""
    
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
            currency='BRL'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
    
    def test_create_transaction(self):
        """Test creating a transaction"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Grocery Store',
            category=self.category,
            currency='BRL'
        )
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.category, self.category)
        self.assertFalse(transaction.is_installment)
    
    def test_installment_transaction(self):
        """Test installment transaction"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Installment Purchase',
            installment_current=1,
            installment_total=10,
            currency='BRL'
        )
        self.assertTrue(transaction.is_installment)
        self.assertEqual(transaction.installment_current, 1)
        self.assertEqual(transaction.installment_total, 10)


class BalanceTestCase(TestCase):
    """Test Balance model and calculation"""
    
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
            balance=Decimal('1000.00'),
            currency='BRL'
        )
    
    def test_create_balance(self):
        """Test creating a balance record"""
        balance = Balance.objects.create(
            account=self.account,
            date=date.today(),
            balance=Decimal('1000.00'),
            cash_balance=Decimal('1000.00'),
            currency='BRL'
        )
        self.assertEqual(balance.balance, Decimal('1000.00'))
        self.assertEqual(balance.end_balance, Decimal('1000.00'))


class RuleTestCase(TestCase):
    """Test Rules engine"""
    
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
            currency='BRL'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
        self.tag = Tag.objects.create(
            user=self.user,
            name='Groceries',
            color='#00FF00'
        )
    
    def test_create_rule(self):
        """Test creating a rule"""
        rule = Rule.objects.create(
            user=self.user,
            name='Auto-categorize groceries',
            resource_type='transaction',
            effective_date=date.today()
        )
        self.assertEqual(rule.resource_type, 'transaction')
        self.assertIsNotNone(rule.registry)
    
    def test_rule_with_condition_and_action(self):
        """Test rule with condition and action"""
        rule = Rule.objects.create(
            user=self.user,
            name='Test Rule',
            resource_type='transaction',
            effective_date=date.today()
        )
        
        # Create condition
        condition = RuleCondition.objects.create(
            rule=rule,
            condition_type='transaction_name',
            operator='like',
            value='Uber'
        )
        
        # Create action
        action = RuleAction.objects.create(
            rule=rule,
            action_type='set_transaction_category',
            value=str(self.category.id)
        )
        
        # Create matching transaction
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('25.00'),
            name='Uber Ride',
            currency='BRL'
        )
        
        # Apply rule
        rule.apply()
        
        # Refresh transaction
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, self.category)


class BudgetTestCase(TestCase):
    """Test Budget model"""
    
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
            currency='BRL'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
        today = date.today()
        self.budget = Budget.objects.create(
            user=self.user,
            start_date=today.replace(day=1),
            end_date=(today.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
            currency='BRL',
            budgeted_spending=Decimal('1000.00')
        )
    
    def test_create_budget(self):
        """Test creating a budget"""
        self.assertEqual(self.budget.budgeted_spending, Decimal('1000.00'))
        self.assertTrue(self.budget.initialized)  # Should be True if budgeted_spending is set
    
    def test_budget_actual_spending(self):
        """Test calculating actual spending"""
        # Create expense transaction
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Grocery',
            category=self.category,
            currency='BRL'
        )
        
        actual = self.budget.actual_spending
        self.assertGreater(actual, Decimal('0'))
    
    def test_budget_category(self):
        """Test budget category"""
        budget_category = BudgetCategory.objects.create(
            budget=self.budget,
            category=self.category,
            budgeted_spending=Decimal('200.00'),
            currency='BRL'
        )
        self.assertEqual(budget_category.budgeted_spending, Decimal('200.00'))
        self.assertEqual(budget_category.available_to_spend, Decimal('200.00'))


class CategoryTestCase(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
        self.assertEqual(category.name, 'Food')
        self.assertEqual(category.classification, 'expense')
    
    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        parent = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
        child = Category.objects.create(
            user=self.user,
            name='Groceries',
            classification='expense',
            color='#FF0000',
            parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.children.all())

