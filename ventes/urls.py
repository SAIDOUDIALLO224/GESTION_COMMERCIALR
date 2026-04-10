from django.urls import path
from . import views

app_name = 'ventes'

urlpatterns = [
    path('', views.liste_ventes, name='liste'),
    path('nouvelle/', views.nouvelle_vente, name='nouvelle'),
    path('<int:pk>/', views.detail_vente, name='detail'),
    path('<int:pk>/encaisser/', views.encaisser_paiement, name='encaisser'),
]
