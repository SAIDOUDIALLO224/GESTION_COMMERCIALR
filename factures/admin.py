from django.contrib import admin
from .models import Facture


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero_facture', 'vente', 'date_emission']
    search_fields = ['numero_facture']
    readonly_fields = ['date_emission', 'date_modification']
