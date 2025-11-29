from django import forms
from .models import Import
from finance.models import Account

class ImportForm(forms.ModelForm):
    class Meta:
        model = Import
        fields = ['type', 'account', 'file', 'date_format', 'currency']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
            'account': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-input', 'accept': '.ofx,.csv'}),
            'date_format': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '%d/%m/%Y'}),
            'currency': forms.TextInput(attrs={'class': 'form-input', 'maxlength': 3, 'placeholder': 'BRL'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(user=user, status='active')
            self.fields['account'].required = False

