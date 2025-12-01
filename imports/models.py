"""
Import models for OFX/CSV file imports
"""
import uuid
import hashlib
from django.db import models
from django.conf import settings


class Import(models.Model):
    """File import (OFX or CSV)"""
    
    TYPE_CHOICES = [
        ('ofx', 'OFX'),
        ('csv', 'CSV'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='imports')
    account = models.ForeignKey('finance.Account', on_delete=models.SET_NULL, null=True, blank=True, related_name='imports')
    
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    file = models.FileField(upload_to='imports/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error = models.TextField(blank=True)
    
    # Import configuration
    date_format = models.CharField(max_length=20, default='%d/%m/%Y')
    currency = models.CharField(max_length=3, default='BRL')
    
    # Statistics
    total_rows = models.IntegerField(default=0)
    imported_rows = models.IntegerField(default=0)
    duplicate_rows = models.IntegerField(default=0)
    error_rows = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'imports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_type_display()} Import - {self.user.email} - {self.created_at}"


class ImportRow(models.Model):
    """Individual row from an import file"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    import_obj = models.ForeignKey(Import, on_delete=models.CASCADE, related_name='rows')
    
    # Raw data
    raw_data = models.JSONField(default=dict)
    
    # Parsed data
    date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    currency = models.CharField(max_length=3, blank=True)
    category = models.CharField(max_length=255, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('imported', 'Imported'),
        ('duplicate', 'Duplicate'),
        ('error', 'Error'),
    ], default='pending')
    error_message = models.TextField(blank=True)
    
    # Duplicate detection
    duplicate_hash = models.CharField(max_length=64, blank=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'import_rows'
    
    def __str__(self):
        return f"Row {self.id} - {self.name} - {self.date}"
    
    def calculate_duplicate_hash(self):
        """Calculate hash for duplicate detection"""
        if not self.date or self.amount is None or not self.name:
            return None
        
        # Hash: date + amount + name (lowercase, stripped)
        # Normalize amount to remove trailing zeros for consistent hashing
        amount_str = str(self.amount).rstrip('0').rstrip('.') if self.amount else '0'
        hash_string = f"{self.date}|{amount_str}|{self.name.lower().strip()}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def save(self, *args, **kwargs):
        if not self.duplicate_hash:
            self.duplicate_hash = self.calculate_duplicate_hash() or ''
        super().save(*args, **kwargs)

