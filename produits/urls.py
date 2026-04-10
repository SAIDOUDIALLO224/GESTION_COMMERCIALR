from django.urls import path
from . import views

app_name = 'produits'

urlpatterns = [
    path('', views.liste_produits, name='liste'),
    path('<int:pk>/', views.detail_produit, name='detail'),
    path('creer/', views.creer_produit, name='creer'),
    path('<int:pk>/modifier/', views.modifier_produit, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_produit, name='supprimer'),
    # Catégories
    path('categories/creer/', views.creer_categorie, name='categorie_creer'),
    path('categories/<int:pk>/modifier/', views.modifier_categorie, name='categorie_modifier'),
    path('categories/<int:pk>/supprimer/', views.supprimer_categorie, name='categorie_supprimer'),
]
