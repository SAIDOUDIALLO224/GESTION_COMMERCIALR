from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from produits.models import Produit
from fournisseurs.models import Fournisseur


class MouvementStock(models.Model):
    """Mouvements de stock (entrées, sorties, ajustements)"""
    TYPE_CHOICES = [
        ('ENTREE', _('Entrée')),
        ('SORTIE', _('Sortie')),
        ('AJUSTEMENT', _('Ajustement')),
        ('INVENTAIRE', _('Inventaire')),
    ]
    
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, verbose_name=_("Produit"))
    type_mvt = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Type"))
    quantite = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)],
        verbose_name=_("Quantité")
    )
    motif = models.TextField(blank=True, verbose_name=_("Motif"))
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name=_("Prix unitaire")
    )
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Utilisateur")
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Fournisseur")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Mouvement de stock")
        verbose_name_plural = _("Mouvements de stock")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['produit']),
            models.Index(fields=['type_mvt']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_type_mvt_display()} - {self.produit.nom} ({self.quantite})"
