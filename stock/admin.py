from django.contrib import admin
from .models import MouvementStock


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ['produit', 'type_mvt', 'quantite', 'created_at', 'utilisateur']
    list_filter = ['type_mvt', 'created_at']
    search_fields = ['produit__nom']
    readonly_fields = ['created_at']
