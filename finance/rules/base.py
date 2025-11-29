"""Base classes for rules engine"""
from abc import ABC, abstractmethod


class ConditionFilter(ABC):
    """Base class for condition filters"""
    
    TYPES = ["text", "number", "select"]
    
    OPERATORS_MAP = {
        "text": [
            ["Contains", "like"],
            ["Equal to", "="]
        ],
        "number": [
            ["Greater than", ">"],
            ["Greater or equal to", ">="],
            ["Less than", "<"],
            ["Less than or equal to", "<="],
            ["Is equal to", "="]
        ],
        "select": [
            ["Equal to", "="]
        ]
    }
    
    def __init__(self, rule):
        self.rule = rule
    
    @property
    def type(self):
        """Return the filter type (text, number, select)"""
        return "text"
    
    @property
    def key(self):
        """Return the filter key (class name without module)"""
        # Convert TransactionNameFilter -> transaction_name
        name = self.__class__.__name__
        if name.endswith('Filter'):
            name = name[:-6]  # Remove 'Filter' suffix
        # Convert CamelCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @property
    def label(self):
        """Return human-readable label"""
        return self.key.replace('_', ' ').title()
    
    @property
    def options(self):
        """Return options for select type filters"""
        return None
    
    @property
    def operators(self):
        """Return available operators for this filter type"""
        return self.OPERATORS_MAP.get(self.type, [])
    
    def prepare(self, queryset):
        """Prepare the queryset with necessary joins"""
        return queryset
    
    @abstractmethod
    def apply(self, queryset, operator, value):
        """Apply the condition to the queryset"""
        pass
    
    def as_dict(self):
        """Return filter metadata as dictionary"""
        return {
            "type": self.type,
            "key": self.key,
            "label": self.label,
            "operators": self.operators,
            "options": self.options,
        }


class ActionExecutor(ABC):
    """Base class for action executors"""
    
    TYPES = ["select", "function", "text"]
    
    def __init__(self, rule):
        self.rule = rule
    
    @property
    def key(self):
        """Return the executor key (class name without module)"""
        # Convert SetTransactionCategoryExecutor -> set_transaction_category
        name = self.__class__.__name__
        if name.endswith('Executor'):
            name = name[:-8]  # Remove 'Executor' suffix
        # Convert CamelCase to snake_case
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @property
    def label(self):
        """Return human-readable label"""
        return self.key.replace('_', ' ').title()
    
    @property
    def type(self):
        """Return the executor type"""
        return "function"
    
    @property
    def options(self):
        """Return options for select type executors"""
        return None
    
    @abstractmethod
    def execute(self, queryset, value=None, ignore_attribute_locks=False):
        """Execute the action on the queryset"""
        pass
    
    def as_dict(self):
        """Return executor metadata as dictionary"""
        return {
            "type": self.type,
            "key": self.key,
            "label": self.label,
            "options": self.options,
        }

