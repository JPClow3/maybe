"""
Transfer matcher - automatically matches transactions between accounts
Ported from app/models/family/auto_transfer_matchable.rb
"""
from datetime import timedelta
from decimal import Decimal
from typing import List, Set, Tuple
from django.db import transaction
from django.db.models import Q, F, OuterRef, Subquery
from django.utils import timezone
from finance.models import Transaction, Transfer, ExchangeRate, Account


class TransferMatcher:
    """Automatically matches transactions to create transfers"""
    
    def __init__(self, user):
        """
        Initialize transfer matcher
        
        Args:
            user: User whose transactions to match
        """
        self.user = user
    
    def auto_match_transfers(self) -> int:
        """
        Automatically match transactions and create transfers
        
        Returns:
            Number of transfers created
        """
        candidates = self._find_match_candidates()
        
        created_count = 0
        used_transaction_ids: Set[str] = set()
        
        with transaction.atomic():
            for inflow_id, outflow_id in candidates:
                # Skip if already used
                if inflow_id in used_transaction_ids or outflow_id in used_transaction_ids:
                    continue
                
                # Create transfer
                try:
                    inflow_txn = Transaction.objects.get(id=inflow_id, account__user=self.user)
                    outflow_txn = Transaction.objects.get(id=outflow_id, account__user=self.user)
                    
                    transfer = Transfer.objects.create(
                        inflow_transaction=inflow_txn,
                        outflow_transaction=outflow_txn,
                        status='matched'
                    )
                    
                    # Update transaction kinds
                    inflow_txn.kind = 'funds_movement'
                    inflow_txn.save(update_fields=['kind'])
                    
                    # Determine outflow kind based on account type
                    outflow_kind = self._get_transfer_kind_for_account(outflow_txn.account)
                    outflow_txn.kind = outflow_kind
                    outflow_txn.save(update_fields=['kind'])
                    
                    used_transaction_ids.add(inflow_id)
                    used_transaction_ids.add(outflow_id)
                    created_count += 1
                except Exception as e:
                    # Skip if creation fails (e.g., validation error)
                    print(f"Failed to create transfer: {e}")
                    continue
        
        return created_count
    
    def _find_match_candidates(self) -> List[Tuple[str, str]]:
        """
        Find transaction pairs that could be transfers
        
        Returns:
            List of (inflow_transaction_id, outflow_transaction_id) tuples
        """
        # Get all active accounts for user
        accounts = Account.objects.filter(user=self.user, status='active')
        account_ids = list(accounts.values_list('id', flat=True))
        
        if not account_ids:
            return []
        
        # Find inflow candidates (negative amount = money coming in)
        inflow_candidates = Transaction.objects.filter(
            account_id__in=account_ids,
            amount__lt=0,  # Negative = inflow
            kind='standard'  # Only match standard transactions
        ).exclude(
            id__in=Subquery(
                Transfer.objects.values_list('inflow_transaction_id', flat=True)
            )
        )
        
        # Find outflow candidates (positive amount = money going out)
        outflow_candidates = Transaction.objects.filter(
            account_id__in=account_ids,
            amount__gt=0,  # Positive = outflow
            kind='standard'  # Only match standard transactions
        ).exclude(
            id__in=Subquery(
                Transfer.objects.values_list('outflow_transaction_id', flat=True)
            )
        )
        
        matches = []
        
        # For each inflow, try to find matching outflow
        for inflow in inflow_candidates.select_related('account'):
            # Find outflows from different accounts, within 4 days
            date_range_start = inflow.date - timedelta(days=4)
            date_range_end = inflow.date + timedelta(days=4)
            
            potential_outflows = outflow_candidates.filter(
                account__user=self.user,
                account__status='active',
                date__gte=date_range_start,
                date__lte=date_range_end
            ).exclude(
                account_id=inflow.account_id
            ).select_related('account')
            
            for outflow in potential_outflows:
                if self._amounts_match(inflow, outflow):
                    matches.append((str(inflow.id), str(outflow.id)))
                    break  # Only match first candidate
        
        # Sort by date difference (closest matches first)
        matches.sort(key=lambda m: self._get_date_diff(m[0], m[1]))
        
        return matches
    
    def _amounts_match(self, inflow: Transaction, outflow: Transaction) -> bool:
        """
        Check if transaction amounts match (considering currency conversion)
        
        Args:
            inflow: Inflow transaction (negative amount)
            outflow: Outflow transaction (positive amount)
        
        Returns:
            True if amounts match
        """
        if inflow.currency == outflow.currency:
            # Same currency: amounts must be exactly opposite
            return inflow.amount + outflow.amount == Decimal('0')
        else:
            # Different currencies: use exchange rate with 5% tolerance
            try:
                # Try to get exchange rate for outflow date
                exchange_rate = ExchangeRate.objects.filter(
                    from_currency=outflow.currency,
                    to_currency=inflow.currency,
                    date=outflow.date
                ).first()
                
                if not exchange_rate:
                    return False
                
                # Convert outflow amount to inflow currency
                converted_outflow = abs(outflow.amount) * exchange_rate.rate
                inflow_abs = abs(inflow.amount)
                
                # Check if within 5% tolerance
                ratio = converted_outflow / inflow_abs if inflow_abs > 0 else 0
                return Decimal('0.95') <= ratio <= Decimal('1.05')
            except Exception:
                return False
    
    def _get_date_diff(self, inflow_id: str, outflow_id: str) -> int:
        """Get absolute date difference between two transactions"""
        try:
            inflow = Transaction.objects.get(id=inflow_id)
            outflow = Transaction.objects.get(id=outflow_id)
            return abs((inflow.date - outflow.date).days)
        except Transaction.DoesNotExist:
            return 999
    
    def _get_transfer_kind_for_account(self, account: Account) -> str:
        """Get appropriate transaction kind for transfer based on account type"""
        if account.accountable_type == 'loan':
            return 'loan_payment'
        elif account.accountable_type == 'credit_card':
            return 'cc_payment'
        else:
            return 'funds_movement'

