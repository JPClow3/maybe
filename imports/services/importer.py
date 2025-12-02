"""
Main importer service that orchestrates parsing and importing
"""
from typing import List
from django.db import transaction
from imports.models import Import, ImportRow
from imports.services.ofx_parser import OFXParser
from imports.services.csv_parser import CSVParser
from imports.services.duplicate_detector import DuplicateDetector
from finance.models import Transaction, Category, Tag


class Importer:
    """Main importer service"""
    
    def __init__(self, import_obj: Import):
        self.import_obj = import_obj
    
    def process(self) -> int:
        """
        Process import: parse file, detect duplicates, import transactions
        
        Returns:
            Number of transactions imported
        """
        self.import_obj.status = 'processing'
        self.import_obj.save(update_fields=['status'])
        
        try:
            # Parse file
            if self.import_obj.type == 'ofx':
                parser = OFXParser(self.import_obj)
            else:
                parser = CSVParser(self.import_obj)
            
            rows = parser.parse()
            
            # Detect duplicates
            detector = DuplicateDetector(self.import_obj.user, self.import_obj.account)
            duplicates = detector.detect_duplicates(rows)
            
            self.import_obj.duplicate_rows = len(duplicates)
            self.import_obj.save(update_fields=['duplicate_rows'])
            
            # Import non-duplicate rows
            imported_count = self._import_rows(rows)
            
            self.import_obj.status = 'completed'
            self.import_obj.imported_rows = imported_count
            self.import_obj.save(update_fields=['status', 'imported_rows'])
            
            return imported_count
            
        except Exception as e:
            self.import_obj.status = 'failed'
            self.import_obj.error = str(e)
            self.import_obj.save(update_fields=['status', 'error'])
            raise
    
    def _import_rows(self, rows: List[ImportRow]) -> int:
        """Import rows as transactions"""
        imported_count = 0
        
        with transaction.atomic():
            for row in rows:
                if row.status == 'duplicate':
                    continue
                
                if not row.date or not row.amount:
                    row.status = 'error'
                    row.error_message = 'Missing date or amount'
                    row.save(update_fields=['status', 'error_message'])
                    continue
                
                try:
                    # Create transaction
                    txn = Transaction.objects.create(
                        account=self.import_obj.account or self._get_default_account(),
                        date=row.date,
                        amount=row.amount,
                        currency=row.currency or self.import_obj.currency,
                        name=row.name,
                        notes=row.notes,
                    )
                    
                    # Set category if provided
                    if row.category:
                        category = self._get_or_create_category(row.category)
                        txn.category = category
                        txn.save(update_fields=['category'])
                    
                    # Set tags if provided
                    if row.tags:
                        self._set_tags(txn, row.tags)
                    
                    row.status = 'imported'
                    row.save(update_fields=['status'])
                    imported_count += 1
                    
                except Exception as e:
                    row.status = 'error'
                    row.error_message = str(e)
                    row.save(update_fields=['status', 'error_message'])
        
        return imported_count
    
    def _get_default_account(self):
        """Get default account for user"""
        from finance.models import Account
        account = Account.objects.filter(user=self.import_obj.user).first()
        if not account:
            raise ValueError(
                f"No accounts found for user {self.import_obj.user.id}. "
                "Please create an account first before importing transactions."
            )
        return account
    
    def _get_or_create_category(self, category_name: str) -> Category:
        """Get or create category"""
        category, _ = Category.objects.get_or_create(
            user=self.import_obj.user,
            name=category_name,
            defaults={'classification': 'expense'}
        )
        return category
    
    def _set_tags(self, transaction: Transaction, tags_str: str):
        """Set tags on transaction"""
        from finance.models import TransactionTag
        
        tag_names = [t.strip() for t in tags_str.split(',')]
        for tag_name in tag_names:
            if tag_name:
                tag, _ = Tag.objects.get_or_create(
                    user=self.import_obj.user,
                    name=tag_name
                )
                TransactionTag.objects.get_or_create(
                    transaction=transaction,
                    tag=tag
                )

