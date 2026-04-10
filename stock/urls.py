from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('ajuster/', views.ajuster_stock, name='ajuster'),
]
