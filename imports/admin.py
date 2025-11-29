from django.contrib import admin
from .models import Import

@admin.register(Import)
class ImportAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    date_hierarchy = 'created_at'

