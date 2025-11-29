from django.urls import path
from . import views

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/data/', views.account_list_data, name='account_list_data'),
    path('accounts/new/', views.account_new, name='account_new'),
    path('accounts/<uuid:pk>/', views.account_detail, name='account_detail'),
    path('accounts/<uuid:pk>/data/', views.account_detail_data, name='account_detail_data'),
    path('accounts/<uuid:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<uuid:pk>/edit-inline/', views.account_edit_inline, name='account_edit_inline'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/data/', views.transaction_list_data, name='transaction_list_data'),
    path('transactions/new/', views.transaction_new, name='transaction_new'),
    path('transactions/<uuid:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<uuid:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<uuid:pk>/update-category/', views.transaction_update_category, name='transaction_update_category'),
    path('transactions/<uuid:pk>/update-amount/', views.transaction_update_amount, name='transaction_update_amount'),
]

