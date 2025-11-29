from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    """Custom user creation form that uses the project's custom User model"""
    
    class Meta:
        model = User
        fields = ('username',)

