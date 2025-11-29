from django.contrib import admin
from .models import Security, SecurityPrice, Holding, Trade

@admin.register(Security)
class SecurityAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'country_code', 'exchange_mic')
    list_filter = ('country_code', 'exchange_mic')
    search_fields = ('ticker', 'name')

@admin.register(SecurityPrice)
class SecurityPriceAdmin(admin.ModelAdmin):
    list_display = ('security', 'date', 'price', 'currency')
    list_filter = ('date', 'currency')
    date_hierarchy = 'date'

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('account', 'security', 'date', 'qty', 'price', 'amount')
    list_filter = ('date', 'currency')

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('account', 'security', 'date', 'qty', 'price', 'amount')
    list_filter = ('date', 'currency')

