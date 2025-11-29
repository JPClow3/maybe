"""
Duplicate detection for imported transactions
"""
from typing import List, Set
from imports.models import ImportRow
from finance.models import Transaction


class DuplicateDetector:
    """Detects duplicate transactions in imports"""
    
    def __init__(self, user, account=None):
        """
        Initialize duplicate detector
        
        Args:
            user: User to check duplicates for
            account: Optional account to limit duplicate check to
        """
        self.user = user
        self.account = account
    
    def detect_duplicates(self, import_rows: List[ImportRow]) -> List[ImportRow]:
        """
        Detect duplicate rows by comparing with existing transactions
        
        Args:
            import_rows: List of ImportRow objects to check
        
        Returns:
            List of ImportRow objects marked as duplicates
        """
        duplicates = []
        
        # Get existing transaction hashes
        existing_hashes = self._get_existing_hashes()
        
        # Check each import row
        for row in import_rows:
            if not row.duplicate_hash:
                continue
            
            # Check if hash exists in database
            if row.duplicate_hash in existing_hashes:
                row.status = 'duplicate'
                row.save(update_fields=['status'])
                duplicates.append(row)
            else:
                # Also check within the same import
                for other_row in import_rows:
                    if other_row.id != row.id and other_row.duplicate_hash == row.duplicate_hash:
                        row.status = 'duplicate'
                        row.save(update_fields=['status'])
                        duplicates.append(row)
                        break
        
        return duplicates
    
    def _get_existing_hashes(self) -> Set[str]:
        """Get set of existing transaction hashes"""
        import hashlib
        
        # Query existing transactions
        transactions = Transaction.objects.filter(account__user=self.user)
        if self.account:
            transactions = transactions.filter(account=self.account)
        
        hashes = set()
        for txn in transactions:
            # Calculate hash same way as ImportRow
            if txn.date and txn.amount and txn.name:
                hash_string = f"{txn.date}|{txn.amount}|{txn.name.lower().strip()}"
                hash_value = hashlib.sha256(hash_string.encode()).hexdigest()
                hashes.add(hash_value)
        
        return hashes

