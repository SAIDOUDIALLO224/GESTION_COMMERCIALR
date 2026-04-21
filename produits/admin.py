from django.contrib import admin
from .models import Categorie, Produit


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ['nom']
    search_fields = ['nom']


@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'categorie', 'stock_actuel', 'seuil_alerte', 'en_alerte', 'actif']
    list_filter = ['categorie', 'actif']
    search_fields = ['code', 'nom']
    fieldsets = (
        ('Informations', {'fields': ('code', 'nom', 'categorie', 'unite_mesure')}),
        ('Prix', {'fields': ('prix_achat', 'prix_vente_gros')}),
        ('Stock', {'fields': ('stock_actuel', 'seuil_alerte')}),
        ('Autres', {'fields': ('photo', 'actif')}),
    )
    readonly_fields = ['created_at', 'updated_at']
