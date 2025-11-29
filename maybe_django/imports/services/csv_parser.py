"""
CSV file parser using pandas
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional
import pandas as pd
from imports.models import Import, ImportRow


class CSVParser:
    """Parser for CSV files"""
    
    def __init__(self, import_obj: Import):
        self.import_obj = import_obj
        self.column_mappings = {
            'date': 'date',
            'amount': 'amount',
            'name': 'name',
            'description': 'name',
            'currency': 'currency',
            'category': 'category',
            'tags': 'tags',
            'notes': 'notes',
        }
    
    def parse(self, column_mappings: Optional[Dict[str, str]] = None) -> List[ImportRow]:
        """
        Parse CSV file and create ImportRow objects
        
        Args:
            column_mappings: Optional dict mapping CSV columns to ImportRow fields
        
        Returns:
            List of ImportRow objects
        """
        if column_mappings:
            self.column_mappings.update(column_mappings)
        
        rows = []
        
        try:
            # Read CSV file
            df = pd.read_csv(self.import_obj.file)
            
            # Process each row
            for idx, row_data in df.iterrows():
                row = ImportRow(
                    import_obj=self.import_obj,
                    raw_data=row_data.to_dict(),
                    date=self._parse_date(row_data),
                    amount=self._parse_amount(row_data),
                    name=self._parse_name(row_data),
                    currency=self._parse_currency(row_data),
                    category=self._parse_category(row_data),
                    tags=self._parse_tags(row_data),
                    notes=self._parse_notes(row_data),
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
    
    def _get_column_value(self, row_data: pd.Series, field_name: str) -> Optional[str]:
        """Get value from CSV row using column mapping"""
        column_name = self.column_mappings.get(field_name)
        if column_name and column_name in row_data:
            value = row_data[column_name]
            if pd.notna(value):
                return str(value).strip()
        return None
    
    def _parse_date(self, row_data: pd.Series) -> Optional[datetime.date]:
        """Parse date from CSV row"""
        date_str = self._get_column_value(row_data, 'date')
        if not date_str:
            return None
        
        # Try multiple date formats
        date_formats = [
            self.import_obj.date_format,
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%d-%m-%Y',
            '%m-%d-%Y',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, row_data: pd.Series) -> Optional[Decimal]:
        """Parse amount from CSV row"""
        amount_str = self._get_column_value(row_data, 'amount')
        if not amount_str:
            return None
        
        # Remove currency symbols and whitespace
        amount_str = amount_str.replace('R$', '').replace('$', '').replace(',', '').strip()
        
        try:
            return Decimal(amount_str)
        except (ValueError, InvalidOperation):
            return None
    
    def _parse_name(self, row_data: pd.Series) -> str:
        """Parse transaction name from CSV row"""
        name = self._get_column_value(row_data, 'name')
        if not name:
            # Try description as fallback
            name = self._get_column_value(row_data, 'description')
        return name or 'Unknown Transaction'
    
    def _parse_currency(self, row_data: pd.Series) -> str:
        """Parse currency from CSV row"""
        currency = self._get_column_value(row_data, 'currency')
        return currency or self.import_obj.currency
    
    def _parse_category(self, row_data: pd.Series) -> str:
        """Parse category from CSV row"""
        return self._get_column_value(row_data, 'category') or ''
    
    def _parse_tags(self, row_data: pd.Series) -> str:
        """Parse tags from CSV row"""
        return self._get_column_value(row_data, 'tags') or ''
    
    def _parse_notes(self, row_data: pd.Series) -> str:
        """Parse notes from CSV row"""
        return self._get_column_value(row_data, 'notes') or ''

