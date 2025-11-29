"""Condition filters for transaction rules"""
from django.db.models import Q, F
from django.db.models.functions import Abs
from .base import ConditionFilter


class TransactionNameFilter(ConditionFilter):
    """Filter transactions by name"""
    
    @property
    def type(self):
        return "text"
    
    def apply(self, queryset, operator, value):
        """Apply name filter to queryset"""
        if operator == "like":
            return queryset.filter(name__icontains=value)
        elif operator == "=":
            return queryset.filter(name__iexact=value)
        else:
            raise ValueError(f"Unsupported operator: {operator}")


class TransactionAmountFilter(ConditionFilter):
    """Filter transactions by amount"""
    
    @property
    def type(self):
        return "number"
    
    def apply(self, queryset, operator, value):
        """Apply amount filter to queryset"""
        from decimal import Decimal
        
        amount_value = Decimal(str(value))
        
        # Use absolute value for comparison
        if operator == ">":
            return queryset.filter(amount__gt=amount_value)
        elif operator == ">=":
            return queryset.filter(amount__gte=amount_value)
        elif operator == "<":
            return queryset.filter(amount__lt=amount_value)
        elif operator == "<=":
            return queryset.filter(amount__lte=amount_value)
        elif operator == "=":
            return queryset.filter(amount=amount_value)
        else:
            raise ValueError(f"Unsupported operator: {operator}")


class TransactionMerchantFilter(ConditionFilter):
    """Filter transactions by merchant"""
    
    @property
    def type(self):
        return "select"
    
    @property
    def options(self):
        """Return list of merchants for the user"""
        from finance.models import Merchant
        merchants = Merchant.objects.filter(user=self.rule.user)
        return [(merchant.name, str(merchant.id)) for merchant in merchants]
    
    def apply(self, queryset, operator, value):
        """Apply merchant filter to queryset"""
        if operator == "=":
            return queryset.filter(merchant_id=value)
        else:
            raise ValueError(f"Unsupported operator: {operator}")

