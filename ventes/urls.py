from django.urls import path
from . import views

app_name = 'ventes'

urlpatterns = [
    path('', views.liste_ventes, name='liste'),
    path('nouvelle/', views.nouvelle_vente, name='nouvelle'),
    path('encaisser-client/', views.encaisser_client, name='encaisser_client'),
    path('<int:pk>/', views.detail_vente, name='detail'),
    path('<int:pk>/encaisser/', views.encaisser_paiement, name='encaisser'),
    path('<int:pk>/supprimer/', views.supprimer_vente, name='supprimer'),
    path('paiement/<int:pk>/modifier/', views.modifier_paiement, name='modifier_paiement'),
    path('paiement/<int:pk>/supprimer/', views.supprimer_paiement, name='supprimer_paiement'),
]
