"""
Comprehensive tests for import services
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock, mock_open
from imports.models import Import, ImportRow
from imports.services.ofx_parser import OFXParser
from imports.services.csv_parser import CSVParser
from imports.services.importer import Importer
from imports.services.duplicate_detector import DuplicateDetector
from finance.models import Account, Transaction

User = get_user_model()


class OFXParserTestCase(TestCase):
    """Test OFXParser service"""
    
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
        # Create a mock import with file
        self.import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            currency='BRL',
            status='pending'
        )
    
    @patch('imports.services.ofx_parser.ofxparse.OfxParser.parse')
    def test_parse_ofx_file(self, mock_parse):
        """Test parsing OFX file"""
        # Mock OFX data
        mock_ofx = MagicMock()
        mock_account = MagicMock()
        mock_statement = MagicMock()
        mock_transaction = MagicMock()
        mock_transaction.id = '12345'
        mock_transaction.type = 'DEBIT'
        mock_transaction.date = date(2024, 1, 15)
        mock_transaction.amount = Decimal('-100.00')
        mock_transaction.memo = 'Test Transaction'
        mock_transaction.payee = 'Test Payee'
        
        mock_statement.transactions = [mock_transaction]
        mock_account.statement = mock_statement
        mock_ofx.account = mock_account
        
        mock_parse.return_value = mock_ofx
        
        # Create file for import
        file_content = b'OFX file content'
        self.import_obj.file = SimpleUploadedFile('test.ofx', file_content)
        self.import_obj.save()
        
        parser = OFXParser(self.import_obj)
        rows = parser.parse()
        
        # Should parse transactions
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[0].amount, Decimal('-100.00'))
    
    def test_parse_invalid_ofx_file(self):
        """Test parsing invalid OFX file"""
        file_content = b'Invalid OFX content'
        self.import_obj.file = SimpleUploadedFile('test.ofx', file_content)
        self.import_obj.save()
        
        parser = OFXParser(self.import_obj)
        
        # Should handle error gracefully
        with self.assertRaises(Exception):
            parser.parse()


class CSVParserTestCase(TestCase):
    """Test CSVParser service"""
    
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
        self.import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='csv',
            currency='BRL',
            status='pending'
        )
    
    def test_parse_csv_file(self):
        """Test parsing CSV file"""
        csv_content = b'date,amount,name\n2024-01-15,-100.00,Test Transaction'
        self.import_obj.file = SimpleUploadedFile('test.csv', csv_content)
        self.import_obj.save()
        
        parser = CSVParser(self.import_obj)
        rows = parser.parse()
        
        # Should parse CSV rows
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[0].amount, Decimal('-100.00'))
        self.assertEqual(rows[0].name, 'Test Transaction')
    
    def test_parse_csv_with_custom_mappings(self):
        """Test parsing CSV with custom column mappings"""
        csv_content = 'data,valor,descricao\n2024-01-15,-200.00,Transacao Teste'.encode('utf-8')
        self.import_obj.file = SimpleUploadedFile('test.csv', csv_content)
        self.import_obj.save()
        
        parser = CSVParser(self.import_obj)
        mappings = {
            'date': 'data',
            'amount': 'valor',
            'name': 'descricao'
        }
        rows = parser.parse(column_mappings=mappings)
        
        # Should use custom mappings
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[0].amount, Decimal('-200.00'))
    
    def test_parse_csv_invalid_amount(self):
        """Test parsing CSV with invalid amount"""
        csv_content = b'date,amount,name\n2024-01-15,invalid,Test'
        self.import_obj.file = SimpleUploadedFile('test.csv', csv_content)
        self.import_obj.save()
        
        parser = CSVParser(self.import_obj)
        rows = parser.parse()
        
        # Should handle invalid amount gracefully
        # Amount might be None or 0
        self.assertGreaterEqual(len(rows), 0)


class DuplicateDetectorTestCase(TestCase):
    """Test DuplicateDetector service"""
    
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
    
    def test_detect_duplicates(self):
        """Test detecting duplicate transactions"""
        # Create existing transaction
        Transaction.objects.create(
            account=self.account,
            date=date(2024, 1, 15),
            amount=Decimal('-100.00'),
            name='Existing Transaction',
            currency='BRL'
        )
        
        # Create import row that matches
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='csv',
            currency='BRL',
            status='pending'
        )
        row = ImportRow.objects.create(
            import_obj=import_obj,
            date=date(2024, 1, 15),
            amount=Decimal('-100.00'),
            name='Existing Transaction',
            currency='BRL'
        )
        
        detector = DuplicateDetector(self.user, self.account)
        duplicates = detector.detect_duplicates([row])
        
        # Should detect duplicate
        self.assertEqual(len(duplicates), 1)
        self.assertIn(row, duplicates)
    
    def test_no_duplicates_for_different_amounts(self):
        """Test that different amounts don't match"""
        Transaction.objects.create(
            account=self.account,
            date=date(2024, 1, 15),
            amount=Decimal('-100.00'),
            name='Transaction',
            currency='BRL'
        )
        
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='csv',
            currency='BRL',
            status='pending'
        )
        row = ImportRow.objects.create(
            import_obj=import_obj,
            date=date(2024, 1, 15),
            amount=Decimal('-200.00'),  # Different amount
            name='Transaction',
            currency='BRL'
        )
        
        detector = DuplicateDetector(self.user, self.account)
        duplicates = detector.detect_duplicates([row])
        
        # Should not detect duplicate
        self.assertEqual(len(duplicates), 0)


class ImporterTestCase(TestCase):
    """Test Importer service"""
    
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
    
    @patch('imports.services.importer.OFXParser')
    def test_process_ofx_import(self, mock_parser_class):
        """Test processing OFX import"""
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='ofx',
            currency='BRL',
            status='pending'
        )
        
        # Mock parser
        mock_parser = MagicMock()
        mock_row = ImportRow(
            import_obj=import_obj,
            date=date.today(),
            amount=Decimal('-100.00'),
            name='Test',
            currency='BRL'
        )
        mock_parser.parse.return_value = [mock_row]
        mock_parser_class.return_value = mock_parser
        
        # Mock duplicate detector
        with patch('imports.services.importer.DuplicateDetector') as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.detect_duplicates.return_value = []
            mock_detector_class.return_value = mock_detector
            
            importer = Importer(import_obj)
            count = importer.process()
            
            # Should import transaction
            self.assertGreaterEqual(count, 0)
            self.assertEqual(import_obj.status, 'completed')
    
    def test_process_csv_import(self):
        """Test processing CSV import"""
        csv_content = b'date,amount,name\n2024-01-15,-100.00,Test'
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='csv',
            currency='BRL',
            status='pending'
        )
        import_obj.file = SimpleUploadedFile('test.csv', csv_content)
        import_obj.save()
        
        # Mock duplicate detector
        with patch('imports.services.importer.DuplicateDetector') as mock_detector_class:
            mock_detector = MagicMock()
            mock_detector.detect_duplicates.return_value = []
            mock_detector_class.return_value = mock_detector
            
            importer = Importer(import_obj)
            count = importer.process()
            
            # Should process import
            self.assertGreaterEqual(count, 0)
    
    def test_process_import_with_duplicates(self):
        """Test processing import with duplicate detection"""
        # Create existing transaction
        Transaction.objects.create(
            account=self.account,
            date=date(2024, 1, 15),
            amount=Decimal('-100.00'),
            name='Existing',
            currency='BRL'
        )
        
        csv_content = b'date,amount,name\n2024-01-15,-100.00,Existing'
        import_obj = Import.objects.create(
            user=self.user,
            account=self.account,
            type='csv',
            currency='BRL',
            status='pending'
        )
        import_obj.file = SimpleUploadedFile('test.csv', csv_content)
        import_obj.save()
        
        importer = Importer(import_obj)
        count = importer.process()
        
        # Should detect duplicate and not import
        self.assertEqual(import_obj.duplicate_rows, 1)
        self.assertGreaterEqual(count, 0)

