from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'telephone', 'type_client', 'solde_du', 'actif']
    list_filter = ['type_client', 'actif']
    search_fields = ['nom', 'telephone']
    fieldsets = (
        ('Informations', {'fields': ('nom', 'telephone', 'telephone2', 'quartier')}),
        ('Classification', {'fields': ('type_client',)}),
        ('Crédit', {'fields': ('solde_du',)}),
        ('Autres', {'fields': ('notes', 'actif')}),
    )
