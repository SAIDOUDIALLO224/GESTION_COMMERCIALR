from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'stock'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='stock:ajuster', permanent=False), name='index'),
    path('ajuster/', views.ajuster_stock, name='ajuster'),
    path('inventaire/pdf/', views.imprimer_inventaire, name='inventaire_pdf'),
]
