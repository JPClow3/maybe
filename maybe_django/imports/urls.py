from django.urls import path
from . import views

urlpatterns = [
    path('imports/', views.import_list, name='import_list'),
    path('imports/new/', views.import_new, name='import_new'),
    path('imports/<uuid:pk>/', views.import_detail, name='import_detail'),
]

