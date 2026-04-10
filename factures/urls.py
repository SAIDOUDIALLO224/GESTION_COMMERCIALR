from django.urls import path
from . import views

app_name = 'factures'

urlpatterns = [
    path('vente/<int:pk>/pdf/', views.generer_facture_pdf, name='pdf'),
]
