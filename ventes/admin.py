from django.contrib import admin
from .models import Vente, LigneVente


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    fields = ['produit', 'quantite', 'prix_unitaire', 'sous_total']
    readonly_fields = ['sous_total']


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'montant_total', 'montant_paye', 'statut', 'date_vente']
    list_filter = ['statut', 'date_vente']
    search_fields = ['numero', 'client__nom']
    inlines = [LigneVenteInline]
    readonly_fields = ['numero', 'date_vente', 'created_at']
