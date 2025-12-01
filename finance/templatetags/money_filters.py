"""
Template filters for Brazilian money formatting and time formatting
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django import template
from django.utils import timezone
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


@register.filter(name='time_ago')
def time_ago(value):
    """
    Format a datetime as relative time (e.g., "2m ago", "1h ago", "yesterday")
    
    Usage:
        {{ account.updated_at|time_ago }}
    """
    if value is None:
        return "never"
    
    try:
        now = timezone.now()
        if isinstance(value, datetime):
            if timezone.is_aware(value):
                diff = now - value
            else:
                diff = now - timezone.make_aware(value)
        else:
            return str(value)
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        elif seconds < 172800:  # 2 days
            return "yesterday"
        elif seconds < 604800:  # 7 days
            days = seconds // 86400
            return f"{days}d ago"
        else:
            # For older dates, just show the date
            return value.strftime("%b %d")
    except (ValueError, TypeError, AttributeError):
        return "unknown"
