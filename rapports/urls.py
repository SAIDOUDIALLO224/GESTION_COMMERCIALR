from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('', views.rapports_index, name='index'),
    path('ventes/', views.rapport_ventes, name='ventes'),
    path('stock/', views.rapport_stock, name='stock'),
    path('paiements-journaliers/', views.paiements_journaliers, name='paiements_journaliers'),
    path('produits-vendus-journaliers/', views.produits_vendus_journaliers, name='produits_vendus_journaliers'),
    path('export/pdf/ventes/', views.export_pdf_ventes, name='export_pdf_ventes'),
    path('export/pdf/stock/', views.export_pdf_stock, name='export_pdf_stock'),
]
