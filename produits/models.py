from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Categorie(models.Model):
    """Catégories de produits"""
    nom = models.CharField(max_length=100, unique=True, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))

    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Produit(models.Model):
    """Fiche produit"""
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Code interne"))
    nom = models.CharField(max_length=200, verbose_name=_("Nom du produit"))
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, verbose_name=_("Catégorie"))
    unite_mesure = models.CharField(max_length=50, verbose_name=_("Unité de mesure"))
    
    prix_achat = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Prix d'achat")
    )
    prix_vente_gros = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Prix de vente gros")
    )
    prix_vente_detail = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)],
        verbose_name=_("Prix de vente détail")
    )
    
    stock_actuel = models.DecimalField(
        max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)],
        verbose_name=_("Stock actuel")
    )
    seuil_alerte = models.DecimalField(
        max_digits=12, decimal_places=3, default=0, validators=[MinValueValidator(0)],
        verbose_name=_("Seuil d'alerte")
    )
    
    photo = models.ImageField(upload_to='produits/', blank=True, null=True, verbose_name=_("Photo"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Créé le"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Modifié le"))

    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['categorie']),
            models.Index(fields=['actif']),
        ]

    def __str__(self):
        return f"{self.code} - {self.nom}"

    @property
    def en_alerte(self):
        """Vérifie si le produit est en alerte de stock"""
        return self.stock_actuel <= self.seuil_alerte

    @property
    def marge_brute(self):
        """Calcule la marge brute"""
        return self.prix_vente_gros - self.prix_achat

    @property
    def pourcentage_marge(self):
        """Calcule le pourcentage de marge"""
        if self.prix_achat > 0:
            return ((self.prix_vente_gros - self.prix_achat) / self.prix_achat) * 100
        return 0
