from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from produits.models import Produit
from clients.models import Client


class Vente(models.Model):
    """Ventes"""
    STATUT_CHOICES = [
        ('EN_ATTENTE', _('En attente')),
        ('PARTIEL', _('Paiement partiel')),
        ('SOLDE', _('Soldée')),
    ]
    
    numero = models.CharField(max_length=30, unique=True, verbose_name=_("Numéro"))
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Client")
    )
    date_vente = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de vente"))
    montant_total = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Montant total")
    )
    montant_paye = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        verbose_name=_("Montant payé")
    )
    solde_restant = models.DecimalField(
        max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        verbose_name=_("Solde restant")
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE',
        verbose_name=_("Statut")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    utilisateur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Utilisateur")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Vente")
        verbose_name_plural = _("Ventes")
        ordering = ['-date_vente']
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['-date_vente']),
        ]

    def __str__(self):
        return f"{self.numero} - {self.montant_total}GNF"


class LigneVente(models.Model):
    """Lignes de vente"""
    vente = models.ForeignKey(Vente, on_delete=models.CASCADE, related_name='lignes', verbose_name=_("Vente"))
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, verbose_name=_("Produit"))
    quantite = models.DecimalField(
        max_digits=12, decimal_places=3, validators=[MinValueValidator(0)],
        verbose_name=_("Quantité")
    )
    prix_unitaire = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Prix unitaire")
    )
    sous_total = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Sous-total")
    )

    class Meta:
        verbose_name = _("Ligne de vente")
        verbose_name_plural = _("Lignes de vente")

    def __str__(self):
        return f"{self.produit.nom} x {self.quantite}"
