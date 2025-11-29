from django.contrib import admin
from .models import Account, Transaction, Valuation, Balance, Category, Tag, Merchant

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'accountable_type', 'balance', 'currency', 'status')
    list_filter = ('accountable_type', 'status', 'currency')
    search_fields = ('name', 'user__email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'date', 'amount', 'currency', 'kind')
    list_filter = ('kind', 'currency', 'date')
    search_fields = ('name', 'account__name')

@admin.register(Valuation)
class ValuationAdmin(admin.ModelAdmin):
    list_display = ('name', 'account', 'date', 'amount', 'currency', 'kind')
    list_filter = ('kind', 'currency', 'date')

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    list_display = ('account', 'date', 'balance', 'currency')
    list_filter = ('date', 'currency')
    date_hierarchy = 'date'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'classification', 'color')
    list_filter = ('classification',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')

@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'color')

