from django.urls import path
from . import views

urlpatterns = [
    path('imports/', views.import_list, name='import_list'),
    path('imports/new/', views.import_new, name='import_new'),
    path('imports/<uuid:pk>/preview/', views.import_preview, name='import_preview'),
    path('imports/<uuid:pk>/confirm/', views.import_confirm, name='import_confirm'),
    path('imports/<uuid:pk>/', views.import_detail, name='import_detail'),
]

