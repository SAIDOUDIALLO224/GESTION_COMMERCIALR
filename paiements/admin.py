from django.contrib import admin
from .models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['vente', 'client', 'montant', 'mode_paiement', 'date_paiement']
    list_filter = ['mode_paiement', 'date_paiement']
    search_fields = ['vente__numero', 'client__nom']
    readonly_fields = ['date_paiement']
