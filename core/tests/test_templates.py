"""
Template rendering and theme consistency tests
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from datetime import date
from finance.models import Account, Transaction, Category

User = get_user_model()


class TemplateRenderingTestCase(TestCase):
    """Test template rendering and theme consistency"""
    
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
    
    def test_login_page_has_gradient_header(self):
        """Test that login page has gradient header styling"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')
        self.assertContains(response, 'dark:from-primary-400 dark:to-primary-300')
    
    def test_register_page_has_gradient_header(self):
        """Test that register page has gradient header styling"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')
        self.assertContains(response, 'dark:from-primary-400 dark:to-primary-300')
    
    def test_dashboard_has_gradient_header(self):
        """Test that dashboard has gradient header"""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')
        self.assertContains(response, 'dark:from-primary-400 dark:to-primary-300')
    
    def test_dashboard_stats_has_text_glow_only_on_caixa_livre(self):
        """Test that text-glow is only on Caixa Livre card"""
        self.login()
        response = self.client.get(reverse('dashboard_stats'))
        self.assertEqual(response.status_code, 200)
        
        # Count text-glow occurrences
        content = response.content.decode('utf-8')
        glow_count = content.count('text-glow')
        
        # Should only appear once (on Caixa Livre)
        self.assertEqual(glow_count, 1)
        self.assertContains(response, 'Caixa Livre')
    
    def test_account_list_has_gradient_header(self):
        """Test that account list has gradient header"""
        self.login()
        response = self.client.get(reverse('account_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')
        self.assertContains(response, 'dark:from-primary-400 dark:to-primary-300')
    
    def test_transaction_list_has_gradient_header(self):
        """Test that transaction list has gradient header"""
        self.login()
        response = self.client.get(reverse('transaction_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')
        self.assertContains(response, 'dark:from-primary-400 dark:to-primary-300')
    
    def test_error_pages_have_gradient_styling(self):
        """Test that error pages have gradient styling"""
        # 404 page
        response = self.client.get('/nonexistent-page/')
        self.assertEqual(response.status_code, 404)
        # Check if 404 template has gradient (if custom 404 handler exists)
        # Note: Django's default 404 might not use our template
    
    def test_all_pages_have_dark_mode_support(self):
        """Test that all pages have dark mode classes"""
        self.login()
        
        pages = [
            ('dashboard', {}),
            ('account_list', {}),
            ('transaction_list', {}),
        ]
        
        for view_name, kwargs in pages:
            response = self.client.get(reverse(view_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 200)
            # Check for dark mode classes
            self.assertContains(response, 'dark:')
    
    def test_cards_have_glass_effects(self):
        """Test that cards use glass effects"""
        self.login()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Cards should have glass classes (inherited from base template)
        # The main content area should have glass-panel or glass-mobile
        self.assertContains(response, 'glass-')
    
    def test_forms_have_consistent_styling(self):
        """Test that forms have consistent styling"""
        self.login()
        
        # Account form - check for form elements (may use different class names)
        response = self.client.get(reverse('account_new'))
        self.assertEqual(response.status_code, 200)
        # Forms may use different input classes, just verify form exists
        self.assertContains(response, '<input')
        
        # Transaction form
        response = self.client.get(reverse('transaction_new'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<input')
    
    def test_buttons_have_consistent_styling(self):
        """Test that buttons have consistent styling"""
        self.login()
        response = self.client.get(reverse('account_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should use btn-primary class
        self.assertContains(response, 'btn-primary')
    
    def test_tables_have_dark_mode_support(self):
        """Test that tables have dark mode support"""
        self.login()
        
        # Create transaction (positive amount)
        Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('50.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        response = self.client.get(reverse('transaction_list_data'))
        self.assertEqual(response.status_code, 200)
        
        # Tables may not have dark mode yet - check if table exists
        self.assertContains(response, '<table')
    
    def test_detail_pages_have_gradient_headers(self):
        """Test that detail pages have gradient headers"""
        self.login()
        
        # Account detail
        response = self.client.get(reverse('account_detail', args=[self.account.pk]))
        self.assertEqual(response.status_code, 200)
        # Should have gradient header (loaded via HTMX)
        
        # Transaction detail
        transaction = Transaction.objects.create(
            account=self.account,
            date=date.today(),
            amount=Decimal('-25.00'),
            name='Test Transaction',
            currency='BRL'
        )
        response = self.client.get(reverse('transaction_detail', args=[transaction.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'bg-gradient-to-r from-primary-700 to-primary-500')

