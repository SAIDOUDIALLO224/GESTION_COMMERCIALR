from django.db import models
from django.utils.translation import gettext_lazy as _


class Fournisseur(models.Model):
    """Fournisseurs"""
    nom = models.CharField(max_length=150, verbose_name=_("Nom"))
    telephone = models.CharField(max_length=20, blank=True, verbose_name=_("Téléphone"))
    adresse = models.TextField(blank=True, verbose_name=_("Adresse"))
    solde_du = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name=_("Solde dû")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Fournisseur")
        verbose_name_plural = _("Fournisseurs")
        ordering = ['nom']

    def __str__(self):
        return self.nom
