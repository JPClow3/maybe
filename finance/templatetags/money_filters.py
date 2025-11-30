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
        
        # Apply tabular-nums tracking-tight font-mono for proper number alignment
        return mark_safe(f'<span class="tabular-nums tracking-tight font-mono">{formatted}</span>')
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


@register.filter(name='div')
def div(value, arg):
    """Divide the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter(name='mul')
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
