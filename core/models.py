import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Financial settings
    currency = models.CharField(max_length=3, default='BRL', help_text='Default currency (ISO 4217)')
    date_format = models.CharField(max_length=20, default='%d/%m/%Y', help_text='Date format string')
    timezone = models.CharField(max_length=50, default='America/Sao_Paulo', help_text='Timezone')
    
    # Localization
    locale = models.CharField(max_length=10, default='pt-BR', help_text='Locale code')
    
    # UI preferences
    theme = models.CharField(max_length=20, default='system', choices=[
        ('system', 'System'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    ])
    show_sidebar = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'user'
        verbose_name_plural = 'users'

