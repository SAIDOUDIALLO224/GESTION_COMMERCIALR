from django.contrib import admin
from .models import Configuration, Magasin


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['nom_magasin', 'devise']


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ['nom', 'actif', 'created_at']
    list_filter = ['actif']
    search_fields = ['nom']
