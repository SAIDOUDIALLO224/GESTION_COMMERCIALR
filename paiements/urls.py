from django.urls import path
from . import views

app_name = 'paiements'

urlpatterns = [
    path('<int:pk>/recu/', views.imprimer_recu, name='recu'),
]
