"""
OFX file parser using ofxparse library
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
import ofxparse
from imports.models import Import, ImportRow


class OFXParser:
    """Parser for OFX files"""
    
    def __init__(self, import_obj: Import):
        self.import_obj = import_obj
    
    def parse(self) -> List[ImportRow]:
        """
        Parse OFX file and create ImportRow objects
        
        Returns:
            List of ImportRow objects
        """
        rows = []
        
        try:
            # Read and parse OFX file
            with self.import_obj.file.open('rb') as f:
                ofx = ofxparse.OfxParser.parse(f)
            
            # Get account from OFX
            account = ofx.account
            
            # Process transactions
            for txn in ofx.account.statement.transactions:
                row = ImportRow(
                    import_obj=self.import_obj,
                    raw_data={
                        'fitid': txn.id,
                        'type': txn.type,
                        'date': txn.date.isoformat() if txn.date else None,
                        'amount': str(txn.amount) if txn.amount else None,
                        'memo': txn.memo or '',
                        'payee': txn.payee or '',
                    },
                    date=self._parse_date(txn.date),
                    amount=self._parse_amount(txn.amount),
                    name=self._parse_name(txn),
                    currency=self.import_obj.currency,
                )
                row.save()
                rows.append(row)
            
            self.import_obj.total_rows = len(rows)
            self.import_obj.save(update_fields=['total_rows'])
            
        except Exception as e:
            self.import_obj.status = 'failed'
            self.import_obj.error = str(e)
            self.import_obj.save(update_fields=['status', 'error'])
            raise
        
        return rows
    
    def _parse_date(self, date_value) -> Optional[datetime.date]:
        """Parse date from OFX transaction"""
        if date_value:
            if isinstance(date_value, datetime):
                return date_value.date()
            elif isinstance(date_value, str):
                try:
                    return datetime.strptime(date_value, '%Y%m%d').date()
                except ValueError:
                    return None
        return None
    
    def _parse_amount(self, amount_value) -> Optional[Decimal]:
        """Parse amount from OFX transaction"""
        if amount_value is not None:
            try:
                return Decimal(str(amount_value))
            except (ValueError, TypeError):
                return None
        return None
    
    def _parse_name(self, txn) -> str:
        """Parse transaction name from OFX transaction"""
        # Prefer payee, fallback to memo
        if txn.payee:
            return txn.payee
        elif txn.memo:
            return txn.memo
        else:
            return f"Transaction {txn.id}"

