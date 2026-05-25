from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('accounts/login/', views.login_view, name='accounts_login'),
    path('logout/', views.logout_view, name='logout'),
    path('changer-magasin/', views.changer_magasin, name='changer_magasin'),
    path('migrer-donnees/', views.migrer_donnees, name='migrer_donnees'),
    path('accounts/logout/', views.logout_view, name='accounts_logout'),
    path('magasins/', views.liste_magasins, name='liste_magasins'),
    path('magasins/creer/', views.creer_magasin, name='creer_magasin'),
    path('magasins/<int:pk>/modifier/', views.modifier_magasin, name='modifier_magasin'),
    path('magasins/<int:pk>/supprimer/', views.supprimer_magasin, name='supprimer_magasin'),
    path('magasins/<int:pk>/', views.detail_magasin, name='detail_magasin'),
]
