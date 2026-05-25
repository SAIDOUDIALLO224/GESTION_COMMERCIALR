from django.db import models
from django.utils.translation import gettext_lazy as _


class Magasin(models.Model):
    """Magasin / dépôt"""
    nom = models.CharField(max_length=100, unique=True, verbose_name=_("Nom"))
    adresse = models.TextField(blank=True, verbose_name=_("Adresse"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    est_principal = models.BooleanField(default=False, verbose_name=_("Magasin principal"))
    magasins_visibles = models.ManyToManyField(
        'self', symmetrical=False, blank=True,
        verbose_name=_("Magasins dont les données sont visibles")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Magasin")
        verbose_name_plural = _("Magasins")
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Configuration(models.Model):
    """Configuration globale de l'application"""
    nom_magasin = models.CharField(max_length=200, default="Magasin Madina", verbose_name=_("Nom du magasin"))
    adresse_magasin = models.TextField(blank=True, verbose_name=_("Adresse du magasin"))
    telephone_magasin = models.CharField(max_length=20, blank=True, verbose_name=_("Téléphone"))
    email_magasin = models.EmailField(blank=True, verbose_name=_("Email"))
    devise = models.CharField(max_length=10, default="GNF", verbose_name=_("Devise"))
    solde_compte_bancaire = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        verbose_name=_("Solde du compte bancaire")
    )
    
    class Meta:
        verbose_name = _("Configuration")
        verbose_name_plural = _("Configurations")

    def __str__(self):
        return self.nom_magasin
