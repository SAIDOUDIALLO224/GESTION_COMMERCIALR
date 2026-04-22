from django.contrib import admin
from .models import CompteEcobanque, EcobanqueOperation, Paiement, CompteEcoBanqueClient


@admin.register(CompteEcobanque)
class CompteEcobanqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'numero_compte', 'solde_courant', 'actif', 'created_at']
    list_filter = ['actif']
    search_fields = ['nom', 'numero_compte']
    readonly_fields = ['created_at']


@admin.register(EcobanqueOperation)
class EcobanqueOperationAdmin(admin.ModelAdmin):
    list_display = ['compte', 'type_operation', 'montant', 'solde_avant', 'solde_apres', 'date_operation']
    list_filter = ['type_operation', 'date_operation', 'compte']
    search_fields = ['compte__nom', 'reference', 'motif']
    readonly_fields = ['solde_avant', 'solde_apres', 'date_operation']


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['vente', 'client', 'montant', 'mode_paiement', 'date_paiement']
    list_filter = ['mode_paiement', 'date_paiement']
    search_fields = ['vente__numero', 'client__nom']
    readonly_fields = ['date_paiement']


@admin.register(CompteEcoBanqueClient)
class CompteEcoBanqueClientAdmin(admin.ModelAdmin):
    list_display = ['client', 'montant_verset', 'montant_initial', 'montant_restant', 'montant_sorti', 'date_operation', 'date_creation']
    list_filter = ['date_operation', 'date_creation']
    search_fields = ['client__nom', 'motif']
    readonly_fields = ['date_creation', 'date_modification']
