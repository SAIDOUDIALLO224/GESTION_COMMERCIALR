from django.contrib import admin
from .models import Configuration


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['nom_magasin', 'devise']
