from django.urls import path
from . import views

urlpatterns = [
    path('securities/', views.security_list, name='security_list'),
    path('holdings/', views.holding_list, name='holding_list'),
    path('trades/', views.trade_list, name='trade_list'),
]

