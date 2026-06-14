from django.contrib import admin
from .models import Configuration, Magasin, Entrepot


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['nom_magasin', 'devise']


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif', 'created_at']
    list_filter = ['actif']
    search_fields = ['nom']


@admin.register(Entrepot)
class EntrepotAdmin(admin.ModelAdmin):
    list_display = ['nom', 'magasin']
    list_filter = ['magasin']
    search_fields = ['nom']
