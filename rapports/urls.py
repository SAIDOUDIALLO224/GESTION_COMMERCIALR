from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('', views.rapports_index, name='index'),
    path('ventes/', views.rapport_ventes, name='ventes'),
    path('stock/', views.rapport_stock, name='stock'),
    path('export/excel/', views.export_excel_ventes, name='export_excel'),
]
