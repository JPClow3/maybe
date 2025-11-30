from django import forms
from .models import Account, Transaction, Category
from .utils import parse_brazilian_currency

class AccountForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate that account name is unique per user"""
        name = self.cleaned_data.get('name')
        if not name or not self.user:
            return name
        
        # Check if another account with same name exists for this user
        existing = Account.objects.filter(user=self.user, name=name)
        # If editing, exclude current instance
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise forms.ValidationError('Já existe uma conta com este nome. Por favor, escolha outro nome.')
        
        return name
    
    class Meta:
        model = Account
        fields = ['name', 'accountable_type', 'currency', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'accountable_type': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'currency': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'maxlength': 3}),
            'status': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
        }

class TransactionForm(forms.ModelForm):
    amount_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input'}),
        label='Amount'
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user, status='active')
            self.fields['category'].queryset = Category.objects.filter(user=user)
        
        # If editing, populate amount_display with formatted value
        if self.instance and self.instance.pk and self.instance.amount:
            from decimal import Decimal
            amount_str = str(self.instance.amount).replace('.', ',')
            self.fields['amount_display'].initial = amount_str
            # Hide the original amount field - we'll use amount_display instead
            self.fields['amount'].widget = forms.HiddenInput()
        else:
            # For new transactions, hide the original amount field
            self.fields['amount'].widget = forms.HiddenInput()
            self.fields['amount'].required = False
        
        # Currency field: Django ModelForm automatically uses instance.currency when editing,
        # so no explicit initialization needed. The widget definition (line 83) must not have
        # a hard-coded 'value': 'BRL' attribute, as that would override the instance's currency.
    
    def clean_amount(self):
        """Amount will be set from amount_display"""
        return self.cleaned_data.get('amount') or 0
    
    def clean_amount_display(self):
        """Convert Brazilian format (1.234,56) to decimal (1234.56)"""
        value = self.cleaned_data.get('amount_display', '').strip()
        if not value:
            if 'amount' in self.cleaned_data and self.cleaned_data['amount']:
                return self.cleaned_data['amount']
            raise forms.ValidationError('Amount is required.')
        
        try:
            return parse_brazilian_currency(value)
        except (ValueError, TypeError):
            raise forms.ValidationError('Please enter a valid amount.')
    
    def clean(self):
        cleaned_data = super().clean()
        # Use amount_display if provided, otherwise use amount
        amount_display = cleaned_data.get('amount_display')
        if amount_display is not None:
            cleaned_data['amount'] = amount_display
        elif not cleaned_data.get('amount'):
            raise forms.ValidationError({'amount_display': 'Amount is required.'})
        return cleaned_data
    
    class Meta:
        model = Transaction
        fields = ['account', 'date', 'name', 'amount', 'currency', 'category', 'notes', 'kind']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            # Do not hard-code a default currency value so existing transaction
            # instances with non-BRL currencies are displayed and preserved correctly.
            'currency': forms.TextInput(attrs={'class': 'form-input', 'maxlength': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'kind': forms.Select(attrs={'class': 'form-select'}),
        }


