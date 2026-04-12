from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    path('', views.liste_clients, name='liste'),
    path('<int:pk>/', views.detail_client, name='detail'),
    path('creer/', views.creer_client, name='creer'),
    path('<int:pk>/modifier/', views.modifier_client, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_client, name='supprimer'),
]
