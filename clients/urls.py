from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.liste_clients, name='liste'),
    path('imprimer-debiteurs/', views.imprimer_clients_debiteurs, name='imprimer_debiteurs'),
    path('dette-initiale/', views.dette_initiale, name='dette_initiale'),
    path('credit-disponible-initial/', views.credit_disponible_initial, name='credit_initial'),
    path('<int:pk>/', views.detail_client, name='detail'),
    path('<int:pk>/remboursement-surplus/', views.remboursement_surplus, name='remboursement_surplus'),
    path('creer/', views.creer_client, name='creer'),
    path('<int:pk>/modifier/', views.modifier_client, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_client, name='supprimer'),
]
