"""
Installment generator - creates future installment transactions
Ported for Brazil-specific credit card installment support
"""
from datetime import timedelta
from decimal import Decimal
from typing import List
from dateutil.relativedelta import relativedelta
from finance.models import Transaction, Account


class InstallmentGenerator:
    """Generates future installment transactions"""
    
    def __init__(self, transaction: Transaction):
        self.transaction = transaction
    
    def generate_installments(self) -> List[Transaction]:
        """
        Generate future installment transactions
        
        Returns:
            List of created installment transactions
        """
        if not self.transaction.installment_total or self.transaction.installment_total <= 1:
            return []
        
        if self.transaction.installment_current is None:
            self.transaction.installment_current = 1
            self.transaction.original_purchase = None
            self.transaction.save(update_fields=['installment_current', 'original_purchase'])
        
        installments = []
        installment_amount = abs(self.transaction.amount) / self.transaction.installment_total
        
        # Generate remaining installments
        for i in range(self.transaction.installment_current + 1, self.transaction.installment_total + 1):
            installment_date = self._calculate_installment_date(i)
            
            installment = Transaction.objects.create(
                account=self.transaction.account,
                date=installment_date,
                amount=-installment_amount if self.transaction.amount < 0 else installment_amount,
                currency=self.transaction.currency,
                name=f"{self.transaction.name} ({i}/{self.transaction.installment_total})",
                notes=self.transaction.notes,
                category=self.transaction.category,
                merchant=self.transaction.merchant,
                kind=self.transaction.kind,
                installment_current=i,
                installment_total=self.transaction.installment_total,
                original_purchase=self.transaction.original_purchase or self.transaction,
                excluded=False,  # Future installments are projected, not excluded
            )
            installments.append(installment)
        
        return installments
    
    def _calculate_installment_date(self, installment_number: int) -> 'datetime.date':
        """
        Calculate date for installment number
        
        Args:
            installment_number: Installment number (1-based)
        
        Returns:
            Date for the installment
        """
        # Default: monthly installments
        months_to_add = installment_number - self.transaction.installment_current
        
        # Calculate date
        if self.transaction.date:
            base_date = self.transaction.date
        else:
            from django.utils import timezone
            base_date = timezone.now().date()
        
        # Add months
        installment_date = base_date + relativedelta(months=months_to_add)
        
        return installment_date
    
    @staticmethod
    def update_installment_series(original_transaction: Transaction):
        """
        Update all installments in a series when original is modified
        
        Args:
            original_transaction: The original transaction in the installment series
        """
        # Get all installments in the series
        installments = Transaction.objects.filter(
            original_purchase=original_transaction.original_purchase or original_transaction
        ).exclude(id=original_transaction.id)
        
        # Update each installment with new data (except date and amount)
        for installment in installments:
            installment.name = f"{original_transaction.name} ({installment.installment_current}/{installment.installment_total})"
            installment.notes = original_transaction.notes
            installment.category = original_transaction.category
            installment.merchant = original_transaction.merchant
            installment.kind = original_transaction.kind
            installment.save()
    
    @staticmethod
    def delete_installment_series(original_transaction: Transaction):
        """
        Delete all future installments when original is deleted
        
        Args:
            original_transaction: The original transaction in the installment series
        """
        # Get all future installments
        installments = Transaction.objects.filter(
            original_purchase=original_transaction.original_purchase or original_transaction
        ).exclude(id=original_transaction.id)
        
        # Delete them
        installments.delete()

