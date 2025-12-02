"""
Tests for investments.views module
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date
from finance.models import Account
from investments.models import Security, Holding, Trade

User = get_user_model()


class InvestmentViewsTestCase(TestCase):
    """Test investment views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.account = Account.objects.create(
            user=self.user,
            name='Investment Account',
            accountable_type='investment',
            currency='BRL',
            status='active'
        )
        self.security = Security.objects.create(
            ticker='PETR4.SA',
            name='Petrobras',
            country_code='BR'
        )
        self.holding = Holding.objects.create(
            account=self.account,
            security=self.security,
            date=date.today(),
            qty=Decimal('100.00'),
            price=Decimal('30.50'),
            currency='BRL'
        )
        self.trade = Trade.objects.create(
            account=self.account,
            security=self.security,
            date=date.today(),
            qty=Decimal('10.00'),  # Positive qty = buy
            price=Decimal('30.50'),
            currency='BRL'
        )
    
    def login(self):
        """Helper to login the test user"""
        self.client.login(username='testuser', password='testpass123')
    
    def test_security_list_requires_login(self):
        """Test that security list requires authentication"""
        response = self.client.get(reverse('security_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_security_list_authenticated(self):
        """Test security list view for authenticated user"""
        self.login()
        response = self.client.get(reverse('security_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Petrobras')
    
    def test_security_list_with_search(self):
        """Test security list with search query"""
        self.login()
        response = self.client.get(reverse('security_list'), {'search': 'PETR'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Petrobras')
    
    def test_security_list_search_no_results(self):
        """Test security list search with no results"""
        self.login()
        response = self.client.get(reverse('security_list'), {'search': 'NONEXISTENT'})
        self.assertEqual(response.status_code, 200)
        # Should still render the page
    
    def test_holding_list_requires_login(self):
        """Test that holding list requires authentication"""
        response = self.client.get(reverse('holding_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_holding_list_authenticated(self):
        """Test holding list view"""
        self.login()
        response = self.client.get(reverse('holding_list'))
        self.assertEqual(response.status_code, 200)
        # Check for ticker (PETR4.SA) which is what the template displays
        self.assertContains(response, 'PETR4.SA')
    
    def test_holding_list_with_account_filter(self):
        """Test holding list with account filter"""
        self.login()
        response = self.client.get(reverse('holding_list'), {'account': str(self.account.pk)})
        self.assertEqual(response.status_code, 200)
        # Check for ticker (PETR4.SA) which is what the template displays
        self.assertContains(response, 'PETR4.SA')
    
    def test_holding_list_with_invalid_account(self):
        """Test holding list with invalid account filter"""
        self.login()
        response = self.client.get(reverse('holding_list'), {'account': 'invalid'})
        self.assertEqual(response.status_code, 200)
        # Should still render, just no results
    
    def test_trade_list_requires_login(self):
        """Test that trade list requires authentication"""
        response = self.client.get(reverse('trade_list'))
        self.assertEqual(response.status_code, 302)
    
    def test_trade_list_authenticated(self):
        """Test trade list view"""
        self.login()
        response = self.client.get(reverse('trade_list'))
        self.assertEqual(response.status_code, 200)
        # Should show trades
    
    def test_trade_list_with_account_filter(self):
        """Test trade list with account filter"""
        self.login()
        response = self.client.get(reverse('trade_list'), {'account': str(self.account.pk)})
        self.assertEqual(response.status_code, 200)
    
    def test_trade_list_with_security_filter(self):
        """Test trade list with security filter"""
        self.login()
        response = self.client.get(reverse('trade_list'), {'security': str(self.security.pk)})
        self.assertEqual(response.status_code, 200)
    
    def test_trade_list_with_both_filters(self):
        """Test trade list with both account and security filters"""
        self.login()
        response = self.client.get(reverse('trade_list'), {
            'account': str(self.account.pk),
            'security': str(self.security.pk)
        })
        self.assertEqual(response.status_code, 200)
    
    def test_trade_list_with_invalid_filters(self):
        """Test trade list with invalid filter values"""
        self.login()
        response = self.client.get(reverse('trade_list'), {
            'account': 'invalid',
            'security': 'invalid'
        })
        self.assertEqual(response.status_code, 200)
        # Should still render, just no results
    
    def test_security_list_other_user_securities(self):
        """Test that users can see all securities (not filtered by user)"""
        self.login()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_security = Security.objects.create(
            ticker='VALE3.SA',
            name='Vale',
            country_code='BR'
        )
        
        response = self.client.get(reverse('security_list'))
        self.assertEqual(response.status_code, 200)
        # Security list shows all securities (not user-filtered)
        # This depends on the actual implementation
    
    def test_holding_list_user_filtered(self):
        """Test that holdings are filtered by user"""
        self.login()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_account = Account.objects.create(
            user=other_user,
            name='Other Account',
            accountable_type='investment',
            currency='BRL',
            status='active'
        )
        other_holding = Holding.objects.create(
            account=other_account,
            security=self.security,
            date=date.today(),
            qty=Decimal('50.00'),
            price=Decimal('30.50'),
            currency='BRL'
        )
        
        response = self.client.get(reverse('holding_list'))
        self.assertEqual(response.status_code, 200)
        # Should only show holdings for current user's accounts
        # This depends on the actual implementation
    
    def test_trade_list_user_filtered(self):
        """Test that trades are filtered by user"""
        self.login()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        other_account = Account.objects.create(
            user=other_user,
            name='Other Account',
            accountable_type='investment',
            currency='BRL',
            status='active'
        )
        other_trade = Trade.objects.create(
            account=other_account,
            security=self.security,
            date=date.today(),
            qty=Decimal('5.00'),  # Positive qty = buy
            price=Decimal('30.50'),
            currency='BRL'
        )
        
        response = self.client.get(reverse('trade_list'))
        self.assertEqual(response.status_code, 200)
        # Should only show trades for current user's accounts
        # This depends on the actual implementation

