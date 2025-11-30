import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


class Account(models.Model):
    """Financial account (bank account, credit card, investment, etc.)"""
    
    ACCOUNTABLE_TYPES = [
        ('depository', 'Depository'),
        ('investment', 'Investment'),
        ('credit_card', 'Credit Card'),
        ('loan', 'Loan'),
        ('property', 'Property'),
        ('vehicle', 'Vehicle'),
        ('crypto', 'Crypto'),
        ('other_asset', 'Other Asset'),
        ('other_liability', 'Other Liability'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('disabled', 'Disabled'),
        ('pending_deletion', 'Pending Deletion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=255)
    accountable_type = models.CharField(max_length=20, choices=ACCOUNTABLE_TYPES)
    accountable_data = models.JSONField(default=dict, blank=True, help_text='Accountable-specific data')
    
    balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    cash_balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    currency = models.CharField(max_length=3, default='BRL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'accounts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'accountable_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_accountable_type_display()})"
    
    @property
    def classification(self):
        """Returns 'asset' or 'liability' based on accountable_type"""
        liability_types = ['credit_card', 'loan', 'other_liability']
        return 'liability' if self.accountable_type in liability_types else 'asset'


class Category(models.Model):
    """Transaction category"""
    
    CLASSIFICATION_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#6172F3')
    classification = models.CharField(max_length=10, choices=CLASSIFICATION_CHOICES, default='expense')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    lucide_icon = models.CharField(max_length=50, default='shapes')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Transaction tag"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tags')
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, default='#e99537')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tags'
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return self.name


class Merchant(models.Model):
    """Merchant/merchant for transactions"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='merchants', null=True, blank=True)
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=7, null=True, blank=True)
    logo_url = models.URLField(null=True, blank=True)
    website_url = models.URLField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'merchants'
        unique_together = [['user', 'name']]
    
    def __str__(self):
        return self.name


class Transaction(models.Model):
    """Financial transaction"""
    
    KIND_CHOICES = [
        ('standard', 'Standard'),
        ('funds_movement', 'Funds Movement'),
        ('cc_payment', 'Credit Card Payment'),
        ('loan_payment', 'Loan Payment'),
        ('one_time', 'One Time'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency = models.CharField(max_length=3, default='BRL')
    name = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    excluded = models.BooleanField(default=False)
    
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.SET_NULL, null=True, blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='standard')
    
    # Brazil-specific: Installment support
    installment_current = models.IntegerField(null=True, blank=True, help_text='Current installment number')
    installment_total = models.IntegerField(null=True, blank=True, help_text='Total number of installments')
    original_purchase = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='installments')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['account', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['kind']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.date} ({self.amount} {self.currency})"
    
    @property
    def is_installment(self):
        return self.installment_total is not None and self.installment_total > 1
    
    @property
    def is_transfer(self):
        """Check if transaction is a transfer type"""
        return self.kind in ['funds_movement', 'cc_payment', 'loan_payment']


class TransactionTag(models.Model):
    """Many-to-many relationship between Transaction and Tag"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='transaction_tags')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='transaction_tags')
    
    class Meta:
        db_table = 'taggings'
        unique_together = [['transaction', 'tag']]


class Valuation(models.Model):
    """Account valuation (reconciliation or current anchor)"""
    
    KIND_CHOICES = [
        ('reconciliation', 'Reconciliation'),
        ('current_anchor', 'Current Anchor'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='valuations')
    date = models.DateField()
    amount = models.DecimalField(max_digits=19, decimal_places=4)
    currency = models.CharField(max_length=3, default='BRL')
    name = models.CharField(max_length=255)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='reconciliation')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'valuations'
        unique_together = [['account', 'date', 'kind']]
        indexes = [
            models.Index(fields=['account', 'date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.date} ({self.amount} {self.currency})"


class Balance(models.Model):
    """Daily balance record for an account"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='balances')
    date = models.DateField()
    balance = models.DecimalField(max_digits=19, decimal_places=4)
    cash_balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    currency = models.CharField(max_length=3, default='BRL')
    
    # Flow fields
    start_cash_balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    start_non_cash_balance = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    cash_inflows = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    cash_outflows = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    non_cash_inflows = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    non_cash_outflows = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    net_market_flows = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    cash_adjustments = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    non_cash_adjustments = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    flows_factor = models.IntegerField(default=1, help_text='1 for assets, -1 for liabilities')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'balances'
        unique_together = [['account', 'date', 'currency']]
        indexes = [
            models.Index(fields=['account', 'date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.account.name} - {self.date} ({self.balance} {self.currency})"
    
    @property
    def start_balance(self):
        """Calculated: start_cash_balance + start_non_cash_balance"""
        return self.start_cash_balance + self.start_non_cash_balance
    
    @property
    def end_cash_balance(self):
        """Calculated: start_cash_balance + (cash_inflows - cash_outflows) * flows_factor + cash_adjustments"""
        return self.start_cash_balance + (self.cash_inflows - self.cash_outflows) * self.flows_factor + self.cash_adjustments
    
    @property
    def end_non_cash_balance(self):
        """Calculated: start_non_cash_balance + (non_cash_inflows - non_cash_outflows) * flows_factor + net_market_flows + non_cash_adjustments"""
        return (self.start_non_cash_balance + 
                (self.non_cash_inflows - self.non_cash_outflows) * self.flows_factor + 
                self.net_market_flows + 
                self.non_cash_adjustments)
    
    @property
    def end_balance(self):
        """Calculated: end_cash_balance + end_non_cash_balance"""
        return self.end_cash_balance + self.end_non_cash_balance


class Transfer(models.Model):
    """Transfer between two accounts"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('matched', 'Matched'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    inflow_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='inflow_transfers')
    outflow_transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='outflow_transfers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transfers'
        unique_together = [['inflow_transaction', 'outflow_transaction']]
    
    def __str__(self):
        return f"Transfer: {self.outflow_transaction.account.name} -> {self.inflow_transaction.account.name}"


class ExchangeRate(models.Model):
    """Exchange rate between currencies"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=19, decimal_places=6)
    date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exchange_rates'
        unique_together = [['from_currency', 'to_currency', 'date']]
        indexes = [
            models.Index(fields=['from_currency']),
            models.Index(fields=['to_currency']),
        ]
    
    def __str__(self):
        return f"{self.from_currency}/{self.to_currency} @ {self.date}: {self.rate}"


class Rule(models.Model):
    """Rule for automatically categorizing and tagging transactions"""
    
    RESOURCE_TYPE_CHOICES = [
        ('transaction', 'Transaction'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rules')
    name = models.CharField(max_length=255, blank=True, null=True)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, default='transaction')
    effective_date = models.DateField(null=True, blank=True, help_text='Date from which rule applies (null = all dates)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rules'
        ordering = ['name', 'created_at']
        indexes = [
            models.Index(fields=['user', 'resource_type']),
        ]
    
    def __str__(self):
        return self.name or f"Rule #{self.id}"
    
    def clean(self):
        """Validate rule has at least one action"""
        from django.core.exceptions import ValidationError
        if self.pk and self.actions.count() == 0:
            raise ValidationError("Rule must have at least one action")
    
    @property
    def registry(self):
        """Get the registry for this rule's resource type"""
        from .rules.registry import TransactionResourceRegistry
        
        if self.resource_type == 'transaction':
            return TransactionResourceRegistry(self)
        else:
            raise ValueError(f"Unsupported resource type: {self.resource_type}")
    
    def matching_resources_scope(self):
        """Get queryset of resources matching this rule's conditions"""
        scope = self.registry.resource_scope
        
        # Prepare queries with necessary joins
        for condition in self.conditions.filter(parent__isnull=True):
            scope = condition.prepare(scope)
        
        # Apply conditions
        for condition in self.conditions.filter(parent__isnull=True):
            scope = condition.apply(scope)
        
        return scope
    
    def affected_resource_count(self):
        """Count of resources that match this rule"""
        return self.matching_resources_scope().count()
    
    def apply(self, ignore_attribute_locks=False):
        """Apply this rule to matching resources"""
        scope = self.matching_resources_scope()
        
        for action in self.actions.all():
            action.apply(scope, ignore_attribute_locks=ignore_attribute_locks)
    
    @property
    def primary_condition_title(self):
        """Get a human-readable title for the primary condition"""
        first_condition = self.conditions.filter(parent__isnull=True).first()
        if not first_condition:
            return "No conditions"
        
        try:
            if first_condition.compound and first_condition.sub_conditions.exists():
                first_sub = first_condition.sub_conditions.first()
                filter_obj = first_sub.filter
                return f"If {filter_obj.label.lower()} {first_sub.operator} {first_sub.value_display}"
            else:
                filter_obj = first_condition.filter
                return f"If {filter_obj.label.lower()} {first_condition.operator} {first_condition.value_display}"
        except Exception:
            return "Invalid condition"


class RuleCondition(models.Model):
    """Condition for a rule"""
    
    CONDITION_TYPE_CHOICES = [
        ('transaction_name', 'Transaction Name'),
        ('transaction_amount', 'Transaction Amount'),
        ('transaction_merchant', 'Transaction Merchant'),
        ('compound', 'Compound'),
    ]
    
    # Map condition_type to filter key
    CONDITION_TYPE_TO_FILTER_KEY = {
        'transaction_name': 'transaction_name',
        'transaction_amount': 'transaction_amount',
        'transaction_merchant': 'transaction_merchant',
    }
    
    OPERATOR_CHOICES = [
        ('like', 'Contains'),
        ('=', 'Equal to'),
        ('regex', 'Matches pattern (regex)'),
        ('>', 'Greater than'),
        ('>=', 'Greater or equal to'),
        ('<', 'Less than'),
        ('<=', 'Less than or equal to'),
        ('or', 'OR'),
        ('and', 'AND'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='conditions', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='sub_conditions', null=True, blank=True)
    condition_type = models.CharField(max_length=50, choices=CONDITION_TYPE_CHOICES)
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES)
    value = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rule_conditions'
        ordering = ['created_at']
    
    def __str__(self):
        if self.compound:
            return f"{self.get_operator_display()} condition"
        return f"{self.get_condition_type_display()} {self.get_operator_display()} {self.value}"
    
    @property
    def compound(self):
        """Check if this is a compound condition"""
        return self.condition_type == 'compound'
    
    @property
    def filter(self):
        """Get the filter for this condition"""
        if self.compound:
            return None
        # Map condition_type to filter key
        filter_key = self.CONDITION_TYPE_TO_FILTER_KEY.get(self.condition_type, self.condition_type)
        return self.rule.registry.get_filter(filter_key)
    
    @property
    def value_display(self):
        """Get display value for this condition"""
        if not self.value:
            return ""
        
        if self.compound:
            return ""
        
        filter_obj = self.filter
        if filter_obj and filter_obj.options:
            option = next((opt for opt in filter_obj.options if opt[1] == self.value), None)
            if option:
                return option[0]
        
        return self.value
    
    def prepare(self, queryset):
        """Prepare queryset with necessary joins"""
        if self.compound:
            # Prepare all sub-conditions
            for sub_condition in self.sub_conditions.all():
                queryset = sub_condition.prepare(queryset)
            return queryset
        else:
            return self.filter.prepare(queryset)
    
    def apply(self, queryset):
        """Apply this condition to the queryset"""
        if self.compound:
            return self._build_compound_scope(queryset)
        else:
            return self.filter.apply(queryset, self.operator, self.value)
    
    def _build_compound_scope(self, queryset):
        """Build compound scope from sub-conditions"""
        from django.db.models import Q
        
        if self.operator == 'or':
            # OR: combine all sub-condition scopes
            q_objects = Q()
            for sub_condition in self.sub_conditions.all():
                sub_scope = sub_condition.apply(queryset)
                # Extract the Q object from the filtered queryset
                # This is a simplified approach - in practice, we'd need to build Q objects
                q_objects |= Q(pk__in=sub_scope.values_list('pk', flat=True))
            return queryset.filter(q_objects) if q_objects else queryset
        else:
            # AND: apply all sub-conditions sequentially
            for sub_condition in self.sub_conditions.all():
                queryset = sub_condition.apply(queryset)
            return queryset


class RuleAction(models.Model):
    """Action to perform when a rule matches"""
    
    ACTION_TYPE_CHOICES = [
        ('set_transaction_category', 'Set Transaction Category'),
        ('set_transaction_tags', 'Set Transaction Tags'),
        ('set_transaction_merchant', 'Set Transaction Merchant'),
        ('set_transaction_name', 'Set Transaction Name'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    value = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rule_actions'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()}: {self.value_display}"
    
    @property
    def executor(self):
        """Get the executor for this action"""
        return self.rule.registry.get_executor(self.action_type)
    
    @property
    def value_display(self):
        """Get display value for this action"""
        if not self.value:
            return ""
        
        options = self.executor.options
        if options:
            option = next((opt for opt in options if opt[1] == self.value), None)
            if option:
                return option[0]
        
        return self.value
    
    def apply(self, queryset, ignore_attribute_locks=False):
        """Apply this action to the queryset"""
        self.executor.execute(queryset, value=self.value, ignore_attribute_locks=ignore_attribute_locks)


class Budget(models.Model):
    """Monthly budget for tracking spending"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgets')
    start_date = models.DateField()
    end_date = models.DateField()
    currency = models.CharField(max_length=3, default='BRL')
    budgeted_spending = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, help_text='Total budgeted spending for the month')
    expected_income = models.DecimalField(max_digits=19, decimal_places=4, null=True, blank=True, help_text='Expected income for the month')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'budgets'
        unique_together = [['user', 'start_date', 'end_date']]
        indexes = [
            models.Index(fields=['user', 'start_date']),
        ]
        ordering = ['-start_date']
    
    def __str__(self):
        return f"Budget {self.start_date.strftime('%B %Y')}"
    
    @classmethod
    def date_to_param(cls, date):
        """Convert date to URL parameter format (e.g., 'jan-2024')"""
        return date.strftime('%b-%Y').lower()
    
    @classmethod
    def param_to_date(cls, param):
        """Convert URL parameter to date (beginning of month)"""
        from datetime import datetime
        return datetime.strptime(param, '%b-%Y').date().replace(day=1)
    
    def sync_budget_categories(self):
        """Sync budget categories with user's expense categories"""
        expense_categories = Category.objects.filter(
            user=self.user,
            classification='expense'
        )
        existing_category_ids = set(self.budget_categories.values_list('category_id', flat=True))
        current_category_ids = set(expense_categories.values_list('id', flat=True))
        
        # Add missing categories
        for category_id in current_category_ids - existing_category_ids:
            BudgetCategory.objects.create(
                budget=self,
                category_id=category_id,
                budgeted_spending=Decimal('0.0000'),
                currency=self.currency
            )
        
        # Remove old categories
        self.budget_categories.filter(category_id__in=existing_category_ids - current_category_ids).delete()
    
    @property
    def actual_spending(self):
        """Calculate actual spending from transactions in this period"""
        from django.db.models import Sum
        transactions = Transaction.objects.filter(
            account__user=self.user,
            date__gte=self.start_date,
            date__lte=self.end_date,
            excluded=False,
            category__classification='expense'
        )
        result = transactions.aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.0000')
    
    @property
    def actual_income(self):
        """Calculate actual income from transactions in this period"""
        from django.db.models import Sum
        transactions = Transaction.objects.filter(
            account__user=self.user,
            date__gte=self.start_date,
            date__lte=self.end_date,
            excluded=False,
            category__classification='income'
        )
        result = transactions.aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.0000')
    
    @property
    def allocated_spending(self):
        """Calculate total allocated spending (sum of parent category budgets)"""
        parent_budget_categories = self.budget_categories.filter(category__parent__isnull=True)
        return sum(bc.budgeted_spending for bc in parent_budget_categories if bc.budgeted_spending) or Decimal('0.0000')
    
    @property
    def available_to_spend(self):
        """Calculate available to spend (budgeted - actual)"""
        budgeted = self.budgeted_spending or Decimal('0.0000')
        return budgeted - self.actual_spending
    
    @property
    def available_to_allocate(self):
        """Calculate available to allocate (budgeted - allocated)"""
        budgeted = self.budgeted_spending or Decimal('0.0000')
        return budgeted - self.allocated_spending
    
    @property
    def initialized(self):
        """Check if budget is initialized (has budgeted_spending set)"""
        return self.budgeted_spending is not None
    
    def budget_category_actual_spending(self, budget_category):
        """Calculate actual spending for a specific budget category"""
        if not budget_category.category:
            # Uncategorized spending
            from django.db.models import Sum
            transactions = Transaction.objects.filter(
                account__user=self.user,
                date__gte=self.start_date,
                date__lte=self.end_date,
                excluded=False,
                category__isnull=True
            )
            result = transactions.aggregate(total=Sum('amount'))
            return result['total'] or Decimal('0.0000')
        
        from django.db.models import Sum
        transactions = Transaction.objects.filter(
            account__user=self.user,
            date__gte=self.start_date,
            date__lte=self.end_date,
            excluded=False,
            category=budget_category.category
        )
        result = transactions.aggregate(total=Sum('amount'))
        return result['total'] or Decimal('0.0000')


class BudgetCategory(models.Model):
    """Budget allocation for a specific category"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='budget_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budget_categories', null=True, blank=True)
    budgeted_spending = models.DecimalField(max_digits=19, decimal_places=4, default=Decimal('0.0000'))
    currency = models.CharField(max_length=3, default='BRL')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'budget_categories'
        unique_together = [['budget', 'category']]
        indexes = [
            models.Index(fields=['budget', 'category']),
        ]
    
    def __str__(self):
        category_name = self.category.name if self.category else "Uncategorized"
        return f"{category_name}: {self.budgeted_spending} {self.currency}"
    
    @property
    def actual_spending(self):
        """Calculate actual spending for this category"""
        return self.budget.budget_category_actual_spending(self)
    
    @property
    def available_to_spend(self):
        """Calculate available to spend for this category"""
        return (self.budgeted_spending or Decimal('0.0000')) - self.actual_spending
    
    @property
    def percent_of_budget_spent(self):
        """Calculate percentage of budget spent"""
        if not self.budgeted_spending or self.budgeted_spending <= 0:
            return 0
        return float((self.actual_spending / self.budgeted_spending) * 100)
    
    @property
    def subcategory(self):
        """Check if this is a subcategory"""
        return self.category and self.category.parent is not None