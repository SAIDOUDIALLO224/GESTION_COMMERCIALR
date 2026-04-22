from django.urls import path
from . import views

app_name = 'paiements'

urlpatterns = [
    path('<int:pk>/recu/', views.imprimer_recu, name='recu'),
    path('comptes-ecobanque/', views.comptes_ecobanque_liste, name='comptes_ecobanque_liste'),
    path('comptes-ecobanque/nouveau/', views.comptes_ecobanque_form, name='comptes_ecobanque_nouveau'),
    path('comptes-ecobanque/<int:pk>/modifier/', views.comptes_ecobanque_form, name='comptes_ecobanque_modifier'),
]
