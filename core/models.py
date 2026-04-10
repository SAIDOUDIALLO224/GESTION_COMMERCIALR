from django.db import models
from django.utils.translation import gettext_lazy as _


class Configuration(models.Model):
    """Configuration globale de l'application"""
    nom_magasin = models.CharField(max_length=200, default="Magasin Madina", verbose_name=_("Nom du magasin"))
    adresse_magasin = models.TextField(blank=True, verbose_name=_("Adresse du magasin"))
    telephone_magasin = models.CharField(max_length=20, blank=True, verbose_name=_("Téléphone"))
    email_magasin = models.EmailField(blank=True, verbose_name=_("Email"))
    devise = models.CharField(max_length=10, default="GNF", verbose_name=_("Devise"))
    
    class Meta:
        verbose_name = _("Configuration")
        verbose_name_plural = _("Configurations")

    def __str__(self):
        return self.nom_magasin
