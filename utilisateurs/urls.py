from django.urls import path
from . import views

app_name = 'utilisateurs'

urlpatterns = [
    path('', views.liste_utilisateurs, name='liste'),
    path('creer/', views.creer_utilisateur, name='creer'),
    path('<int:pk>/modifier/', views.modifier_utilisateur, name='modifier'),
    path('<int:pk>/toggle-actif/', views.toggle_actif_utilisateur, name='toggle_actif'),
    path('<int:pk>/supprimer/', views.supprimer_utilisateur, name='supprimer'),
]
