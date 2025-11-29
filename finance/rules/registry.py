"""Rule registry for managing condition filters and action executors"""
from django.core.exceptions import ImproperlyConfigured
from .base import ConditionFilter, ActionExecutor


class RuleRegistry:
    """Base registry for rules"""
    
    class UnsupportedActionError(Exception):
        pass
    
    class UnsupportedConditionError(Exception):
        pass
    
    def __init__(self, rule):
        self.rule = rule
    
    @property
    def resource_scope(self):
        """Return the base queryset for the resource type"""
        raise NotImplementedError(f"{self.__class__.__name__} must implement resource_scope")
    
    @property
    def condition_filters(self):
        """Return list of available condition filters"""
        return []
    
    @property
    def action_executors(self):
        """Return list of available action executors"""
        return []
    
    def get_filter(self, key):
        """Get a condition filter by key"""
        filter_obj = next((f for f in self.condition_filters if f.key == key), None)
        if not filter_obj:
            raise self.UnsupportedConditionError(f"Unsupported condition type: {key}")
        return filter_obj
    
    def get_executor(self, key):
        """Get an action executor by key"""
        executor = next((e for e in self.action_executors if e.key == key), None)
        if not executor:
            raise self.UnsupportedActionError(f"Unsupported action type: {key}")
        return executor
    
    def as_dict(self):
        """Return registry metadata as dictionary"""
        return {
            "filters": [f.as_dict() for f in self.condition_filters],
            "executors": [e.as_dict() for e in self.action_executors]
        }


class TransactionResourceRegistry(RuleRegistry):
    """Registry for transaction resource rules"""
    
    def __init__(self, rule):
        super().__init__(rule)
        from .filters import (
            TransactionNameFilter,
            TransactionAmountFilter,
            TransactionMerchantFilter
        )
        from .executors import (
            SetTransactionCategoryExecutor,
            SetTransactionTagsExecutor,
            SetTransactionMerchantExecutor,
            SetTransactionNameExecutor
        )
        self._filters = [
            TransactionNameFilter(rule),
            TransactionAmountFilter(rule),
            TransactionMerchantFilter(rule)
        ]
        self._executors = [
            SetTransactionCategoryExecutor(rule),
            SetTransactionTagsExecutor(rule),
            SetTransactionMerchantExecutor(rule),
            SetTransactionNameExecutor(rule)
        ]
    
    @property
    def resource_scope(self):
        """Return base queryset for transactions"""
        from finance.models import Transaction
        from django.utils import timezone
        from datetime import date
        
        # Get transactions from the rule's effective date onwards
        effective_date = self.rule.effective_date or date.today()
        return Transaction.objects.filter(
            account__user=self.rule.user,
            date__gte=effective_date,
            excluded=False
        )
    
    @property
    def condition_filters(self):
        return self._filters
    
    @property
    def action_executors(self):
        return self._executors

