"""
Unit tests for finance forms
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date
from finance.forms import AccountForm, TransactionForm
from finance.models import Account, Transaction, Category

User = get_user_model()


class AccountFormTestCase(TestCase):
    """Test AccountForm"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_account_form_valid(self):
        """Test valid account form"""
        form_data = {
            'name': 'Test Account',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        form = AccountForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_account_form_invalid_missing_name(self):
        """Test account form without required name"""
        form_data = {
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        form = AccountForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_account_form_save(self):
        """Test saving account form"""
        form_data = {
            'name': 'Savings Account',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        form = AccountForm(data=form_data)
        self.assertTrue(form.is_valid())
        account = form.save(commit=False)
        account.user = self.user
        account.save()
        self.assertEqual(account.name, 'Savings Account')


class TransactionFormTestCase(TestCase):
    """Test TransactionForm with Brazilian formatting"""
    
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
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
    
    def test_transaction_form_valid_brazilian_format(self):
        """Test transaction form with Brazilian amount format"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'Test Transaction',
            'amount_display': 'R$ 1.234,56',
            'currency': 'BRL',
            'category': self.category.pk,
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        cleaned_amount = form.cleaned_data['amount_display']
        self.assertEqual(cleaned_amount, Decimal('1234.56'))
    
    def test_transaction_form_amount_without_prefix(self):
        """Test transaction form with amount without R$ prefix"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'Test Transaction',
            'amount_display': '1.234,56',
            'currency': 'BRL',
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        cleaned_amount = form.cleaned_data['amount_display']
        self.assertEqual(cleaned_amount, Decimal('1234.56'))
    
    def test_transaction_form_amount_simple_format(self):
        """Test transaction form with simple amount format"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'Test Transaction',
            'amount_display': '50,00',
            'currency': 'BRL',
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        cleaned_amount = form.cleaned_data['amount_display']
        self.assertEqual(cleaned_amount, Decimal('50.00'))
    
    def test_transaction_form_invalid_amount(self):
        """Test transaction form with invalid amount"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'Test Transaction',
            'amount_display': 'invalid',
            'currency': 'BRL',
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        # Form should catch exception and raise ValidationError
        try:
            is_valid = form.is_valid()
            self.assertFalse(is_valid)
            if not is_valid:
                self.assertIn('amount_display', form.errors)
        except Exception as e:
            # If exception is raised, it should be ValidationError
            from django.core.exceptions import ValidationError
            self.assertIsInstance(e, ValidationError)
    
    def test_transaction_form_missing_amount(self):
        """Test transaction form without amount"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'Test Transaction',
            'currency': 'BRL',
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('amount_display', form.errors)
    
    def test_transaction_form_filters_accounts_by_user(self):
        """Test that form filters accounts by user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_account = Account.objects.create(
            user=other_user,
            name='Other Account',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        
        form = TransactionForm(user=self.user)
        account_queryset = form.fields['account'].queryset
        self.assertIn(self.account, account_queryset)
        self.assertNotIn(other_account, account_queryset)
    
    def test_transaction_form_filters_categories_by_user(self):
        """Test that form filters categories by user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_category = Category.objects.create(
            user=other_user,
            name='Other Category',
            classification='expense',
            color='#0000FF'
        )
        
        form = TransactionForm(user=self.user)
        category_queryset = form.fields['category'].queryset
        self.assertIn(self.category, category_queryset)
        self.assertNotIn(other_category, category_queryset)
    
    def test_transaction_form_with_existing_instance(self):
        """Test transaction form with existing transaction instance"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Existing Transaction',
            currency='BRL'
        )
        form = TransactionForm(instance=transaction, user=self.user)
        # amount_display should be populated
        self.assertIsNotNone(form.fields['amount_display'].initial)
    
    def test_transaction_form_preserves_non_brl_currency_on_edit(self):
        """Editing a non-BRL transaction should show and preserve its currency"""
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('200.00'),
            name='USD Transaction',
            currency='USD'
        )
        form = TransactionForm(instance=transaction, user=self.user)
        # The currency field should reflect the instance currency, not a hard-coded default
        self.assertEqual(form['currency'].value(), 'USD')
    
    def test_transaction_form_save(self):
        """Test saving transaction form"""
        form_data = {
            'account': self.account.pk,
            'date': date.today(),
            'name': 'New Transaction',
            'amount_display': 'R$ 75,50',
            'currency': 'BRL',
            'category': self.category.pk,
            'kind': 'standard'
        }
        form = TransactionForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        transaction = form.save()
        self.assertEqual(transaction.amount, Decimal('75.50'))
        self.assertEqual(transaction.name, 'New Transaction')

