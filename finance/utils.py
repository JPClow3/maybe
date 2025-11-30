"""
Utility functions for finance views
"""
import json
from decimal import Decimal, InvalidOperation
from django.http import HttpResponse


def add_htmx_trigger(response, event_name, data=None):
    """
    Add HX-Trigger header to response for HTMX events
    
    Args:
        response: HttpResponse object
        event_name: Name of the event to trigger
        data: Optional data to pass with the event
    
    Returns:
        HttpResponse with HX-Trigger header added
    """
    trigger_data = {event_name: data if data is not None else {}}
    
    # Check if HX-Trigger already exists
    existing_trigger = response.get('HX-Trigger', None)
    if existing_trigger:
        try:
            existing_data = json.loads(existing_trigger)
            existing_data.update(trigger_data)
            trigger_data = existing_data
        except (json.JSONDecodeError, TypeError):
            pass
    
    response['HX-Trigger'] = json.dumps(trigger_data)
    return response


def add_toast_trigger(response, message, toast_type='success'):
    """
    Add toast notification trigger to HTMX response
    
    Args:
        response: HttpResponse object
        message: Toast message text
        toast_type: Type of toast ('success', 'error', 'info')
    
    Returns:
        HttpResponse with toast trigger added
    """
    return add_htmx_trigger(response, 'show-toast', {
        'message': message,
        'type': toast_type
    })


def parse_brazilian_currency(value):
    """
    Parse Brazilian currency format (R$ 1.234,56) to Decimal.
    
    Args:
        value: String containing Brazilian currency format (e.g., "R$ 1.234,56" or "1.234,56")
    
    Returns:
        Decimal: Parsed currency value
    
    Raises:
        ValueError: If value cannot be parsed
        InvalidOperation: If value results in invalid decimal operation
    
    Example:
        >>> parse_brazilian_currency("R$ 1.234,56")
        Decimal('1234.56')
        >>> parse_brazilian_currency("1.234,56")
        Decimal('1234.56')
    """
    if not value:
        raise ValueError("Empty value cannot be parsed")
    
    # Remove currency symbol and whitespace
    amount_str = str(value).replace('R$', '').strip()
    
    # Remove thousand separators (dots) first
    amount_str = amount_str.replace('.', '')
    
    # Replace comma with dot for decimal separator
    amount_str = amount_str.replace(',', '.')
    
    try:
        return Decimal(amount_str)
    except (ValueError, InvalidOperation) as e:
        raise ValueError(f"Invalid currency format: {value}") from e

