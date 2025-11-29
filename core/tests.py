"""
Tests for core app
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date
from finance.models import Account, Transaction

User = get_user_model()


class DashboardTestCase(TestCase):
    """Test dashboard view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def login(self):
        """Helper to login the test user"""
        self.client.login(username='testuser', password='testpass123')
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_dashboard_with_no_accounts(self):
        """Test dashboard with no accounts"""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_dashboard_free_cash_calculation(self):
        """Test dashboard calculates free cash correctly"""
        self.login()
        # Create depository account
        Account.objects.create(
            user=self.user,
            name='Checking',
            accountable_type='depository',
            balance=Decimal('2000.00'),
            currency='BRL',
            status='active'
        )
        # Test the stats endpoint directly since main dashboard shows skeleton
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        # Should show free cash
        self.assertContains(response, 'Caixa Livre')
    
    def test_dashboard_credit_card_debt(self):
        """Test dashboard calculates credit card debt"""
        self.login()
        Account.objects.create(
            user=self.user,
            name='Credit Card',
            accountable_type='credit_card',
            balance=Decimal('-1000.00'),  # Debt
            currency='BRL',
            status='active'
        )
        # Test the stats endpoint directly since main dashboard shows skeleton
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fatura Atual')
    
    def test_dashboard_investments(self):
        """Test dashboard shows investments"""
        self.login()
        Account.objects.create(
            user=self.user,
            name='Investments',
            accountable_type='investment',
            balance=Decimal('10000.00'),
            currency='BRL',
            status='active'
        )
        # Test the stats endpoint directly since main dashboard shows skeleton
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Investimentos')

    def test_dashboard_contains_skeleton_and_htmx(self):
        """Dashboard HTML should include skeleton container and HTMX attributes"""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Skeleton loading container
        self.assertContains(response, 'animate-pulse')
        # HTMX call to stats endpoint
        self.assertContains(response, 'hx-get="/dashboard/stats/"')
    
    def test_dashboard_recent_transactions(self):
        """Test dashboard shows recent transactions"""
        self.login()
        account = Account.objects.create(
            user=self.user,
            name='Test Account',
            accountable_type='depository',
            currency='BRL',
            status='active'
        )
        Transaction.objects.create(
            account=account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Test Transaction',
            currency='BRL'
        )
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transações Recentes')

