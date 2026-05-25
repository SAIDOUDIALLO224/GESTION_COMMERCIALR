from django.core.management.base import BaseCommand
from produits.models import Produit
from ventes.models import Vente
from stock.models import MouvementStock
from core.models import Magasin


class Command(BaseCommand):
    help = 'Migre les données sans magasin (NULL) vers un magasin existant'

    def add_arguments(self, parser):
        parser.add_argument('magasin_id', type=int, help='ID du magasin de destination')
        parser.add_argument('--dry-run', action='store_true', help='Simule sans appliquer')

    def handle(self, *args, **options):
        magasin_id = options['magasin_id']
        dry_run = options['dry_run']

        try:
            magasin = Magasin.objects.get(pk=magasin_id)
        except Magasin.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Aucun magasin avec l\'ID {magasin_id}'))
            return

        produits = Produit.objects.filter(magasin__isnull=True)
        ventes = Vente.objects.filter(magasin__isnull=True)
        mouvements = MouvementStock.objects.filter(magasin__isnull=True)

        self.stdout.write(f'Magasin de destination : {magasin.nom} (ID={magasin.pk})')
        self.stdout.write(f'  Produits sans magasin  : {produits.count()}')
        self.stdout.write(f'  Ventes sans magasin    : {ventes.count()}')
        self.stdout.write(f'  Mouvements sans magasin: {mouvements.count()}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY-RUN : rien n\'a été modifié'))
            return

        p = produits.update(magasin=magasin)
        v = ventes.update(magasin=magasin)
        m = mouvements.update(magasin=magasin)

        self.stdout.write(self.style.SUCCESS(
            f'{p} produit(s), {v} vente(s) et {m} mouvement(s) '
            f'rattaché(s) à "{magasin.nom}".'
        ))
