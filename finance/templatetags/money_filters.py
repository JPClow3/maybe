"""
Template filters for Brazilian money formatting
"""
from decimal import Decimal
from django import template
from django.utils.safestring import mark_safe
from ..money import Money, Currency

register = template.Library()


@register.filter(name='real_br')
def real_br(value, currency='BRL'):
    """
    Format a decimal value as Brazilian Real (R$ 1.234,56)
    
    Usage:
        {{ account.balance|real_br }}
        {{ transaction.amount|real_br }}
    """
    if value is None:
        return mark_safe('<span class="text-gray-500">—</span>')
    
    try:
        # Convert to Decimal if not already
        if isinstance(value, (int, float, str)):
            amount = Decimal(str(value))
        elif isinstance(value, Decimal):
            amount = value
        else:
            return str(value)
        
        # Use Money class for formatting
        money = Money(amount, currency)
        formatted = money.format()
        
        # Apply font-tabular-nums for proper number alignment
        return mark_safe(f'<span class="font-tabular-nums">{formatted}</span>')
    except (ValueError, TypeError):
        return str(value)
    except Exception:
        # Catch all other exceptions (like InvalidOperation from Decimal)
        return str(value)


@register.filter(name='real_br_plain')
def real_br_plain(value, currency='BRL'):
    """
    Format a decimal value as Brazilian Real without HTML tags (R$ 1.234,56)
    Useful for form values, attributes, etc.
    
    Usage:
        {{ account.balance|real_br_plain }}
    """
    if value is None:
        return "—"
    
    try:
        if isinstance(value, (int, float, str)):
            amount = Decimal(str(value))
        elif isinstance(value, Decimal):
            amount = value
        else:
            return str(value)
        
        money = Money(amount, currency)
        return money.format()
    except (ValueError, TypeError):
        return str(value)

