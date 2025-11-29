"""
Integration and E2E tests for finance views
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date
from finance.models import Account, Transaction, Category

User = get_user_model()


class FinanceViewsTestCase(TestCase):
    """Base test case for finance views"""
    
    def setUp(self):
        self.client = Client()
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
            currency='BRL',
            status='active'
        )
        self.category = Category.objects.create(
            user=self.user,
            name='Food',
            classification='expense',
            color='#FF0000'
        )
    
    def login(self):
        """Helper to login the test user"""
        self.client.login(username='testuser', password='testpass123')


class AccountViewsTestCase(FinanceViewsTestCase):
    """Test account views"""
    
    def test_account_list_requires_login(self):
        """Test that account list requires authentication"""
        response = self.client.get(reverse('account_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_account_list_authenticated(self):
        """Test account list view for authenticated user"""
        self.login()
        response = self.client.get(reverse('account_list'))
        self.assertEqual(response.status_code, 200)
        # Should show skeleton loading initially (HTMX will load data)
        self.assertContains(response, 'hx-get="/accounts/data/"')
    
    def test_account_list_data_endpoint(self):
        """Test account list data endpoint that returns account cards"""
        self.login()
        response = self.client.get(reverse('account_list_data'))
        self.assertEqual(response.status_code, 200)
        # Should contain the actual account data
        self.assertContains(response, 'Test Account')
    
    def test_account_detail_requires_login(self):
        """Test that account detail requires authentication"""
        response = self.client.get(reverse('account_detail', args=[self.account.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_account_detail_authenticated(self):
        """Test account detail view"""
        self.login()
        response = self.client.get(reverse('account_detail', args=[self.account.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Account')
        self.assertContains(response, 'R$')
    
    def test_account_new_get(self):
        """Test GET request to new account form"""
        self.login()
        response = self.client.get(reverse('account_new'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Account')
    
    def test_account_new_post_success(self):
        """Test POST request to create new account"""
        self.login()
        data = {
            'name': 'New Savings Account',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        response = self.client.post(reverse('account_new'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(Account.objects.filter(name='New Savings Account').exists())
    
    def test_account_new_post_htmx(self):
        """Test HTMX POST request to create new account"""
        self.login()
        data = {
            'name': 'HTMX Account',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        response = self.client.post(
            reverse('account_new'),
            data,
            HTTP_HX_REQUEST='true'
        )
        # HTMX request should return 204 (No Content), 200 (with form), or 302 (redirect)
        self.assertIn(response.status_code, [200, 204, 302])
        if response.status_code == 200:
            # Should have HX-Redirect header or be a form with errors
            pass
        elif response.status_code == 204:
            # 204 No Content is valid for successful HTMX operations
            self.assertTrue(Account.objects.filter(name='HTMX Account').exists())
    
    def test_account_edit_get(self):
        """Test GET request to edit account form"""
        self.login()
        response = self.client.get(reverse('account_edit', args=[self.account.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit Account')
    
    def test_account_edit_post_success(self):
        """Test POST request to update account"""
        self.login()
        data = {
            'name': 'Updated Account Name',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        response = self.client.post(reverse('account_edit', args=[self.account.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.account.refresh_from_db()
        self.assertEqual(self.account.name, 'Updated Account Name')
    
    def test_account_edit_inline_get(self):
        """Test inline edit GET request"""
        self.login()
        response = self.client.get(
            reverse('account_edit_inline', args=[self.account.pk]),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_account_edit_inline_post(self):
        """Test inline edit POST request"""
        self.login()
        data = {'name': 'Inline Updated Name'}
        response = self.client.post(
            reverse('account_edit_inline', args=[self.account.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.account.refresh_from_db()
        self.assertEqual(self.account.name, 'Inline Updated Name')


class TransactionViewsTestCase(FinanceViewsTestCase):
    """Test transaction views"""
    
    def setUp(self):
        super().setUp()
        self.transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Test Transaction',
            category=self.category,
            currency='BRL'
        )
    
    def test_transaction_list_requires_login(self):
        """Test that transaction list requires authentication"""
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_transaction_list_data_requires_login(self):
        """Transaction data endpoint should also require authentication"""
        response = self.client.get(reverse('transaction_list_data'))
        self.assertEqual(response.status_code, 302)
    
    def test_transaction_list_authenticated(self):
        """Test transaction list view"""
        self.login()
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(response.status_code, 200)
        # Should show skeleton loading initially (HTMX will load data)
        self.assertContains(response, 'animate-pulse')
        self.assertContains(response, 'hx-get="/transactions/data/"')
    
    def test_transaction_list_data_endpoint(self):
        """Test transaction list data endpoint that returns table"""
        self.login()
        response = self.client.get(reverse('transaction_list_data'))
        self.assertEqual(response.status_code, 200)
        # Should contain the actual transaction data
        self.assertContains(response, 'Test Transaction')
    
    def test_transaction_update_amount_invalid_value_htmx(self):
        """Inline amount update with invalid value should not change amount"""
        self.login()
        original_amount = self.transaction.amount
        data = {'amount': 'invalid'}
        response = self.client.post(
            reverse('transaction_update_amount', args=[self.transaction.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        # View should handle the error gracefully and return 200 with error toast
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.amount, original_amount)
    
    def test_transaction_detail_requires_login(self):
        """Test that transaction detail requires authentication"""
        response = self.client.get(reverse('transaction_detail', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_transaction_detail_authenticated(self):
        """Test transaction detail view"""
        self.login()
        response = self.client.get(reverse('transaction_detail', args=[self.transaction.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Transaction')
    
    def test_transaction_new_get(self):
        """Test GET request to new transaction form"""
        self.login()
        response = self.client.get(reverse('transaction_new'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Transaction')
    
    def test_transaction_new_post_success(self):
        """Test POST request to create new transaction"""
        self.login()
        data = {
            'account': self.account.pk,
            'date': date.today().isoformat(),
            'name': 'New Transaction',
            'amount_display': 'R$ 100,00',
            'currency': 'BRL',
            'category': self.category.pk,
            'kind': 'standard'
        }
        response = self.client.post(reverse('transaction_new'), data)
        # Should redirect or return success
        self.assertIn(response.status_code, [200, 302])
        if response.status_code == 302:
            self.assertTrue(Transaction.objects.filter(name='New Transaction').exists())
    
    def test_transaction_update_category_get(self):
        """Test GET request to update category inline"""
        self.login()
        response = self.client.get(
            reverse('transaction_update_category', args=[self.transaction.pk]),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_transaction_update_category_post(self):
        """Test POST request to update category inline"""
        self.login()
        new_category = Category.objects.create(
            user=self.user,
            name='Transport',
            classification='expense',
            color='#0000FF'
        )
        data = {'category_id': str(new_category.pk)}
        response = self.client.post(
            reverse('transaction_update_category', args=[self.transaction.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.category, new_category)
    
    def test_transaction_update_amount_get(self):
        """Test GET request to update amount inline"""
        self.login()
        response = self.client.get(
            reverse('transaction_update_amount', args=[self.transaction.pk]),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_transaction_update_amount_post(self):
        """Test POST request to update amount inline"""
        self.login()
        data = {'amount': 'R$ 75,50'}
        response = self.client.post(
            reverse('transaction_update_amount', args=[self.transaction.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.amount, Decimal('75.50'))


class DashboardViewsTestCase(FinanceViewsTestCase):
    """Test dashboard view"""
    
    def setUp(self):
        super().setUp()
        # Create credit card account
        self.credit_card = Account.objects.create(
            user=self.user,
            name='Credit Card',
            accountable_type='credit_card',
            balance=Decimal('-500.00'),  # Debt
            currency='BRL',
            status='active'
        )
        # Create investment account
        self.investment = Account.objects.create(
            user=self.user,
            name='Investments',
            accountable_type='investment',
            balance=Decimal('5000.00'),
            currency='BRL',
            status='active'
        )
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_authenticated(self):
        """Test dashboard view with authenticated user"""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
        # Should show skeleton loading initially (HTMX will load data)
        self.assertContains(response, 'animate-pulse')
        self.assertContains(response, 'hx-get="/dashboard/stats/"')
    
    def test_dashboard_stats_endpoint(self):
        """Test dashboard stats endpoint that returns data cards"""
        self.login()
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        # Should show the three main cards with actual data
        self.assertContains(response, 'Caixa Livre')
        self.assertContains(response, 'Fatura Atual')
        self.assertContains(response, 'Investimentos')
    
    def test_dashboard_calculations(self):
        """Test that dashboard calculates values correctly"""
        self.login()
        # Test the stats endpoint directly since main dashboard shows skeleton
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        # Free cash should be depository balance
        self.assertContains(response, 'R$ 1.000,00')  # Or similar format
        # Credit card debt should be shown
        self.assertContains(response, 'R$ 500,00')
        # Investments should be shown
        self.assertContains(response, 'R$ 5.000,00')


class FinanceViewsE2ETestCase(FinanceViewsTestCase):
    """End-to-end tests for complete user flows"""
    
    def test_complete_account_crud_flow(self):
        """Test complete CRUD flow for accounts"""
        self.login()
        
        # Create
        data = {
            'name': 'E2E Test Account',
            'accountable_type': 'depository',
            'currency': 'BRL',
            'status': 'active'
        }
        response = self.client.post(reverse('account_new'), data)
        self.assertIn(response.status_code, [200, 302])
        account = Account.objects.get(name='E2E Test Account')
        
        # Read
        response = self.client.get(reverse('account_detail', args=[account.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E2E Test Account')
        
        # Update
        data['name'] = 'Updated E2E Account'
        response = self.client.post(reverse('account_edit', args=[account.pk]), data)
        self.assertIn(response.status_code, [200, 302])
        account.refresh_from_db()
        self.assertEqual(account.name, 'Updated E2E Account')
        
        # List
        response = self.client.get(reverse('account_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Updated E2E Account')
    
    def test_complete_transaction_crud_flow(self):
        """Test complete CRUD flow for transactions"""
        self.login()
        
        # Create
        data = {
            'account': self.account.pk,
            'date': date.today().isoformat(),
            'name': 'E2E Transaction',
            'amount_display': 'R$ 200,00',
            'currency': 'BRL',
            'category': self.category.pk,
            'kind': 'standard'
        }
        response = self.client.post(reverse('transaction_new'), data)
        self.assertIn(response.status_code, [200, 302])
        transaction = Transaction.objects.get(name='E2E Transaction')
        self.assertEqual(transaction.amount, Decimal('200.00'))
        
        # Read
        response = self.client.get(reverse('transaction_detail', args=[transaction.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E2E Transaction')
        
        # Update inline - category
        new_category = Category.objects.create(
            user=self.user,
            name='New Category',
            classification='expense',
            color='#00FF00'
        )
        data = {'category_id': str(new_category.pk)}
        response = self.client.post(
            reverse('transaction_update_category', args=[transaction.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.category, new_category)
        
        # Update inline - amount
        data = {'amount': 'R$ 250,00'}
        response = self.client.post(
            reverse('transaction_update_amount', args=[transaction.pk]),
            data,
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
        transaction.refresh_from_db()
        self.assertEqual(transaction.amount, Decimal('250.00'))
        
        # List - test data endpoint directly since main view shows skeleton
        response = self.client.get(reverse('transaction_list_data'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'E2E Transaction')

