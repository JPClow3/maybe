from django.urls import path
from . import views

urlpatterns = [
    path('securities/', views.security_list, name='security_list'),
    path('holdings/', views.holding_list, name='holding_list'),
    path('trades/', views.trade_list, name='trade_list'),
    path('b3/status/', views.b3_update_status, name='b3_update_status'),
    path('asset-allocation/', views.asset_allocation, name='asset_allocation'),
]

