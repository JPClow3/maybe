"""Action executors for transaction rules"""
from .base import ActionExecutor


class SetTransactionCategoryExecutor(ActionExecutor):
    """Set category on transactions"""
    
    @property
    def type(self):
        return "select"
    
    @property
    def options(self):
        """Return list of categories for the user"""
        from finance.models import Category
        categories = Category.objects.filter(user=self.rule.user)
        return [(category.name, str(category.id)) for category in categories]
    
    def execute(self, queryset, value=None, ignore_attribute_locks=False):
        """Set category on matching transactions"""
        if not value:
            return
        
        from finance.models import Category
        try:
            category = Category.objects.get(id=value, user=self.rule.user)
        except Category.DoesNotExist:
            return
        
        # Update transactions that don't have a category or if ignoring locks
        if ignore_attribute_locks:
            queryset.update(category=category)
        else:
            queryset.filter(category__isnull=True).update(category=category)


class SetTransactionTagsExecutor(ActionExecutor):
    """Set tags on transactions"""
    
    @property
    def type(self):
        return "select"
    
    @property
    def options(self):
        """Return list of tags for the user"""
        from finance.models import Tag
        tags = Tag.objects.filter(user=self.rule.user)
        return [(tag.name, str(tag.id)) for tag in tags]
    
    def execute(self, queryset, value=None, ignore_attribute_locks=False):
        """Set tag on matching transactions"""
        if not value:
            return
        
        from finance.models import Tag, TransactionTag
        try:
            tag = Tag.objects.get(id=value, user=self.rule.user)
        except Tag.DoesNotExist:
            return
        
        # Add tag to transactions that don't already have it
        for transaction in queryset:
            if ignore_attribute_locks or not TransactionTag.objects.filter(transaction=transaction, tag=tag).exists():
                TransactionTag.objects.get_or_create(transaction=transaction, tag=tag)


class SetTransactionMerchantExecutor(ActionExecutor):
    """Set merchant on transactions"""
    
    @property
    def type(self):
        return "select"
    
    @property
    def options(self):
        """Return list of merchants for the user"""
        from finance.models import Merchant
        merchants = Merchant.objects.filter(user=self.rule.user)
        return [(merchant.name, str(merchant.id)) for merchant in merchants]
    
    def execute(self, queryset, value=None, ignore_attribute_locks=False):
        """Set merchant on matching transactions"""
        if not value:
            return
        
        from finance.models import Merchant
        try:
            merchant = Merchant.objects.get(id=value, user=self.rule.user)
        except Merchant.DoesNotExist:
            return
        
        # Update transactions that don't have a merchant or if ignoring locks
        if ignore_attribute_locks:
            queryset.update(merchant=merchant)
        else:
            queryset.filter(merchant__isnull=True).update(merchant=merchant)


class SetTransactionNameExecutor(ActionExecutor):
    """Set name on transactions"""
    
    @property
    def type(self):
        return "text"
    
    @property
    def options(self):
        return None
    
    def execute(self, queryset, value=None, ignore_attribute_locks=False):
        """Set name on matching transactions"""
        if not value:
            return
        
        # Update transactions that don't have a name or if ignoring locks
        if ignore_attribute_locks:
            queryset.update(name=value)
        else:
            # Only update if name is empty or matches a pattern
            queryset.filter(name__isnull=True).update(name=value)
            queryset.filter(name='').update(name=value)

