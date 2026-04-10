from django.urls import path
from . import views

app_name = 'produits'

urlpatterns = [
    path('', views.liste_produits, name='liste'),
    path('<int:pk>/', views.detail_produit, name='detail'),
    path('creer/', views.creer_produit, name='creer'),
    path('<int:pk>/modifier/', views.modifier_produit, name='modifier'),
]
