from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'currency', 'locale', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'currency', 'locale')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Financial Settings', {'fields': ('currency', 'date_format', 'timezone')}),
        ('Localization', {'fields': ('locale',)}),
    )

