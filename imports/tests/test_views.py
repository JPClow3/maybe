"""
Tests for imports.views module
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from datetime import date
from imports.models import Import, ImportRow
from finance.models import Account, Transaction, Category, Tag

User = get_user_model()


class ImportViewsTestCase(TestCase):
    """Test import views"""
    
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
    
    def test_import_list_requires_login(self):
        """Test that import list requires authentication"""
        response = self.client.get(reverse('import_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_import_list_authenticated(self):
        """Test import list view for authenticated user"""
        self.login()
        response = self.client.get(reverse('import_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Imports')
    
    def test_import_new_get(self):
        """Test GET request to new import form"""
        self.login()
        response = self.client.get(reverse('import_new'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'New Import')
    
    def test_import_new_post_ofx(self):
        """Test POST request to create OFX import"""
        self.login()
        ofx_content = b"""
OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<STMTRS>
<CURDEF>BRL</CURDEF>
<BANKACCTFROM>
<BANKID>123</BANKID>
<ACCTID>456</ACCTID>
<ACCTTYPE>CHECKING</ACCTTYPE>
</BANKACCTFROM>
<BANKTRANLIST>
<DTSTART>20230101000000</DTSTART>
<DTEND>20230131000000</DTEND>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20230115000000</DTPOSTED>
<TRNAMT>-100.00</TRNAMT>
<FITID>20230115001</FITID>
<MEMO>Grocery Store</MEMO>
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""
        data = {
            'type': 'ofx',
            'account': self.account.pk,
            'currency': 'BRL',
            'file': SimpleUploadedFile("test.ofx", ofx_content)
        }
        response = self.client.post(reverse('import_new'), data)
        # Should redirect to preview or detail
        self.assertIn(response.status_code, [200, 302])
    
    def test_import_new_post_csv(self):
        """Test POST request to create CSV import"""
        self.login()
        csv_content = 'data,valor,descricao\n2024-01-15,100.00,Transaction Test'.encode('utf-8')
        data = {
            'type': 'csv',
            'account': self.account.pk,
            'currency': 'BRL',
            'file': SimpleUploadedFile("test.csv", csv_content)
        }
        response = self.client.post(reverse('import_new'), data)
        # Should redirect to detail
        self.assertIn(response.status_code, [200, 302])
    
    def test_import_preview_requires_login(self):
        """Test that import preview requires authentication"""
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        response = self.client.get(reverse('import_preview', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_import_preview_authenticated(self):
        """Test import preview view"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        ImportRow.objects.create(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        response = self.client.get(reverse('import_preview', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Transaction')
    
    def test_import_preview_other_user(self):
        """Test that users can only view their own imports"""
        self.login()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        import_obj = Import.objects.create(
            user=other_user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        
        response = self.client.get(reverse('import_preview', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 404)  # Not found for other user
    
    def test_import_confirm_requires_login(self):
        """Test that import confirm requires authentication"""
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        response = self.client.post(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_import_confirm_get_redirects(self):
        """Test that GET request to confirm redirects to preview"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        response = self.client.get(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn('preview', response.url)
    
    def test_import_confirm_post_no_rows(self):
        """Test confirming import with no rows"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        response = self.client.post(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
        # Should redirect back to preview with error message
    
    def test_import_confirm_post_success(self):
        """Test confirming import successfully"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        ImportRow.objects.create(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        response = self.client.post(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
        # Should redirect to transaction list
        
        import_obj.refresh_from_db()
        self.assertEqual(import_obj.status, 'completed')
        self.assertTrue(Transaction.objects.filter(name='Test Transaction').exists())
    
    def test_import_confirm_with_category(self):
        """Test confirming import with category"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        ImportRow.objects.create(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            category='Food',
            currency='BRL'
        )
        
        response = self.client.post(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
        
        transaction = Transaction.objects.get(name='Test Transaction')
        self.assertIsNotNone(transaction.category)
        self.assertEqual(transaction.category.name, 'Food')
    
    def test_import_confirm_with_tags(self):
        """Test confirming import with tags"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        ImportRow.objects.create(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            tags='important, work',
            currency='BRL'
        )
        
        response = self.client.post(reverse('import_confirm', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
        
        transaction = Transaction.objects.get(name='Test Transaction')
        tags = Tag.objects.filter(transaction_tags__transaction=transaction)
        self.assertEqual(tags.count(), 2)
    
    def test_import_detail_requires_login(self):
        """Test that import detail requires authentication"""
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        response = self.client.get(reverse('import_detail', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_import_detail_authenticated(self):
        """Test import detail view"""
        self.login()
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        ImportRow.objects.create(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('100.00'),
            name='Test Transaction',
            currency='BRL'
        )
        
        response = self.client.get(reverse('import_detail', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Transaction')
    
    def test_import_detail_other_user(self):
        """Test that users can only view their own imports"""
        self.login()
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        import_obj = Import.objects.create(
            user=other_user,
            account=self.account,
            type='ofx',
            file=SimpleUploadedFile("test.ofx", b"dummy"),
            currency='BRL'
        )
        
        response = self.client.get(reverse('import_detail', args=[import_obj.pk]))
        self.assertEqual(response.status_code, 404)

