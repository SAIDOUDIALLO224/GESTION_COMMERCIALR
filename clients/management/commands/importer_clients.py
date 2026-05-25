from django.core.management.base import BaseCommand
from clients.models import Client
from core.models import Magasin


CLIENTS = [
    (["626636363", "662737341"], "ABDOURAHMANE DISPENSAIRE", "CONAKRY"),
    (["620631007"], "ALPHA OUMAR KOLOMA", "CONAKRY"),
    (["626304604"], "ELHADJI AMADOU BAMBA", "CONAKRY"),
    (["623214221"], "ELHADJI BILLO PALET", "CONAKRY"),
    (["628774296"], "ELHADJI BOUBACAR/IBRAHIMA", "COYAH"),
    (["621963395"], "ELHADJI SADOU 4 JOUR T8", "CONAKRY"),
    (["628899620"], "KOTO SAIDOU", "CONAKRY"),
    (["624377627"], "MAMADOU LAMARANA T5", "CONAKRY"),
    (["623245245", "622134241"], "THIERNO COBAYA / ABDOUL SALAM", "CONAKRY"),
    (["620397980"], "AIDARA MOHAMED", "SIGUIRY"),
    (["622027302"], "BAH ABOUBACAR SIDDY PERSO", "CONAKRY"),
    (["628332209"], "BAH ANGOLA HATABIOU", "COYAH"),
    (["629363647", "661188591"], "BAH BILLO GARAYA", "COYAH"),
    (["622146932"], "BAH ELHADJI IBRAHIMA PITA", "PITA"),
    (["628877551"], "BAH MAMADOU KEIRA", "LELOUMA"),
    (["623451384", "620116708"], "BAH MAMADOU SAIDOU", "CONAKRY"),
    (["626420325"], "BAH MAMOUDOU", "KINDIA CONAKRY"),
    (["621019003"], "BAH MARIAMA DALANDA", "CONAKRY"),
    (["626979610", "620218886"], "BAH OUSMANE SIGUIRY", "SIGUIRY"),
    (["622327204"], "BAH THIENO SADOU", "CONAKRY/KOUNDARA"),
    (["628617173"], "BAH YOUNOUSSA", "CONAKRY"),
    (["627585919"], "BARRY ABDOUL", "BONFI CONAKRY"),
    (["628238606"], "BARRY ELHADJI OUSMANE BAILLA", "CONAKRY"),
    (["628667845"], "BARRY MAMADOU FALILOU/SALIOU", "SIGUIRY"),
    (["628654185"], "BARRY MAMADOU LAMINE", "COYAH"),
    (["622295649"], "BARRY MAMADOU/KOTO DIAN KANKAN", "KANKAN"),
    (["621247851"], "BARRY THIERNO AMADOU (FOULAH BOY)", "CONAKRY"),
    (["620583331"], "BARRY THIERNO AMADOU RAHICE", "CONAKRY"),
    (["622229141"], "BARRY YOUNOUSSA", "SIGUIRY"),
    (["622251125"], "BARRY(24HEUR) AMADOU SADIO", "CIMENTERY CONAKRY"),
    (["23272977350", "23277501919"], "DIAKITE IBRAHIMA", "SIERRA LEONE"),
    (["620111707"], "DIALLO ABDOUL AZIZE / TIDIANE KOULA", "LABE"),
    (["628470304"], "DIALLO ABDOULAYE SONACOM ENCO 5", "CONAKRY"),
    (["628804871"], "DIALLO ABDOULAYE GONBONYA", "COYAH"),
    (["622189718"], "DIALLO ABOUBACAR YACIN", "CONAKRY"),
    (["628306150"], "DIALLO ALHADJI BOBO SIGUIRI", "SIGUIRY"),
    (["628647232"], "DIALLO ALHASSANE T7", "CONAKRY"),
    (["621117577"], "DIALLO ALPHA BOUBACAR / ABDOURAHIME", "CONAKRY"),
    (["628120032"], "DIALLO ALPHA OUMAR (BOUROUDJI)", "CONAKRY"),
    (["623420561"], "DIALLO ALPHA OUMAR GUERIYABHE", "CONAKRY"),
    (["628185036"], "DIALLO AMADOU TIDIANE", "CONAKRY"),
    (["622730241"], "DIALLO BAPPA ALSENY", "CONAKRY"),
    (["620166673"], "DIALLO BOUBACAR / OUMAR BAILO", "CONAKRY"),
    (["620300052"], "DIALLO ELHADJI SADOU/MOUCTAR ABDA", "LABE"),
    (["623700965"], "DIALLO IBRAHIMA SODEFA", "COYAH"),
    (["628498483", "669465052"], "DIALLO ISMAEL EN VILLE", "CONAKRY"),
    (["620062618"], "DIALLO ISMAEL/KOULAH", "SIGUIRY"),
    (["622359425"], "DIALLO MAMADOU (BAPPA)/OUMAR BAILO", "MAFERINYA"),
    (["628781031"], "DIALLO MAMADOU DIAN DIALLO", "KANKAN"),
    (["613692042", "245969045439"], "DIALLO MAMADOU OURY", "KANKAN"),
    (["621204288"], "DIALLO MAMADOU OURY KINTIGNA", "SIGUIRY"),
    (["622258188"], "DIALLO MAMADOU SALIOU DJINBALABE", "CONAKRY"),
    (["624495070"], "DIALLO MAMADOU SALIOU IBRAHIME", "MAMOU"),
    (["628260464"], "DIALLO MAMADOU SALIOU SIGUIRI", "SIGUIRY"),
    (["627956224"], "DIALLO MAMADOU ZAINOU", "SIGUIRY"),
    (["627181515"], "DIALLO MAMOUDOU BELLA", "LABE"),
    (["629479290"], "DIALLO MOUCTAR DIALLO / KOULA", "COYAH"),
    (["626322827"], "DIALLO MOUCTAR SIGUIRI", "SIGUIRY"),
    (["622408513"], "DIALLO MOUCTAR YATAYA", "CONAKRY"),
    (["628333343"], "DIALLO OUMAR BAILLO", "CONAKRY"),
    (["625706623"], "DIALLO SOULEYMANE /SAIDOU 5", "SIGUIRY"),
    (["623149658"], "DIALLO SOULEYMANE GONBOYA", "COYAH"),
    (["620229474"], "DIALLO THIERNO AMIROU", "LABE"),
    (["622174660"], "DIALLO THIERNO MARWANE/OUMAR BAILLO", "BOKE"),
    (["628955823"], "DIALLO THIERNO YOUSSOUF DIALLO", "DUBREKA"),
    (["626338800"], "DIALLO / EL IBRAHIMA PITA MAMADOU MOUSTAPHA", "CONAKRY"),
    (["627940094"], "LY IBRAHIMA", "SIGUIRY"),
    (["628333343"], "NO : 2 BOUTIQUE OUMAR BAILO JUS 2", "CONAKRY"),
    (["622380117"], "SALL ALHADJI ADAMA", "CONAKRY"),
    (["625287438"], "SOW BOUTIQUE PERSONNEL IBRAHIMA", "CONAKRY"),
    (["628017199"], "SOW IBRAHIMA (ALPADJO FADIA)", "CONAKRY"),
    (["620999909"], "SOW MAMADOU DIAN (NENE KESSEMA)", "LABE"),
    (["627550767"], "SOW MAMOUDOU SANOYA", "COYAH"),
    (["622559631"], "SOW OUSMANE PIERRE", "CONAKRY"),
]


class Command(BaseCommand):
    help = "Importe les clients dans MAGASIN GENERAL"

    def handle(self, *args, **options):
        magasin, created = Magasin.objects.get_or_create(
            nom="MAGASIN GENERAL",
            defaults={'adresse': 'Conakry, Guinée', 'est_principal': False}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Magasin '{magasin.nom}' créé (id={magasin.id})."))
        else:
            self.stdout.write(f"Magasin '{magasin.nom}' trouvé (id={magasin.id}).")

        count = 0
        for telephones, nom, ville in CLIENTS:
            telephone = telephones[0]
            telephone2 = telephones[1] if len(telephones) > 1 else ''
            notes = f"Ville: {ville}"
            if telephone2:
                notes += f" | Téléphone(s): {', '.join(telephones)}"

            _, created = Client.objects.get_or_create(
                nom=nom,
                telephone=telephone,
                magasin=magasin,
                defaults={
                    'telephone2': telephone2,
                    'notes': notes,
                    'quartier': ville,
                    'solde_du': 0,
                    'credit_disponible': 0,
                    'actif': True,
                }
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"{count} clients importés dans '{magasin.nom}'."))
