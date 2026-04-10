# GesStock Madina - Application de Gestion de Stock & Commerce

Une application Django complète et professionnelle pour la gestion de stock, ventes, clients et facturation pour le Magasin Madina à Conakry, Guinée.

## Fonctionnalités Principales

### 1. Gestion des Produits
- Fiches produits avec code, nom, catégorie, unité de mesure
- Prix d'achat, prix de vente gros et détail
- Stock actuel avec seuil d'alerte
- Photos optionnelles
- Alertes visuelles en rouge quand le stock est faible

### 2. Mouvements de Stock
- Entrées de stock (réception fournisseur)
- Sorties automatiques à la vente
- Ajustements manuels avec motif obligatoire
- Outil d'inventaire physique
- Historique complet des mouvements

### 3. Gestion des Clients
- Fiches clients avec nom, téléphone, quartier, type
- Suivi du solde dû
- Historique complet des achats et paiements
- Alertes sur les dettes anciennes
- Notes libres

### 4. Gestion du Crédit Client
- Paiement partiel ou à crédit total
- Enregistrement des versements successifs
- Suivi du solde en temps réel
- Export du relevé de compte

### 5. Enregistrement des Ventes
- Sélection des produits avec recherche
- Saisie des quantités
- Choix du client (ou vente anonyme)
- Mode de règlement : espèces, virement, partiel ou crédit
- Récapitulatif avant validation
- Transaction atomique avec vérification du stock

### 6. Facturation
- Génération automatique de factures numérotées
- PDF téléchargeable
- Historique des factures
- Réimpression possible

### 7. Gestion des Fournisseurs
- Fiches fournisseurs
- Historique des achats
- Suivi des dettes
- Comparaison des prix

### 8. Tableau de Bord et Rapports
- Dashboard quotidien : CA, ventes, encaissements, crédits, alertes stock
- Rapports périodiques : ventes, stock, clients, bénéfices, fournisseurs, dettes
- Exports en PDF et Excel

### 9. Gestion des Utilisateurs
- Deux rôles : Gérant (accès complet) et Employé (accès restreint)
- Connexion par identifiant et mot de passe
- Traçabilité complète des actions

### 10. Interface Utilisateur
- Entièrement en français
- Grands boutons clairs avec icônes
- Navigation simple
- Couleurs cohérentes (vert = succès, rouge = alerte)
- Optimisée pour desktop

## Installation

### Prérequis
- Python 3.11+
- pip
- virtualenv

### Étapes d'installation

1. Créer l'environnement virtuel
```bash
python3.11 -m venv venv
source venv/bin/activate
```

2. Installer les dépendances
```bash
pip install -r requirements.txt
```

3. Appliquer les migrations
```bash
python manage.py migrate
```

4. Créer un superutilisateur
```bash
python manage.py createsuperuser
```

5. Démarrer le serveur
```bash
python manage.py runserver
```

L'application sera accessible à http://localhost:8000

## Structure du Projet

gesstock_django/
├── config/              # Configuration Django
├── core/                # App principale
├── produits/            # Gestion des produits
├── stock/               # Mouvements de stock
├── clients/             # Gestion des clients
├── fournisseurs/        # Gestion des fournisseurs
├── ventes/              # Enregistrement des ventes
├── paiements/           # Gestion des paiements
├── factures/            # Génération de factures
├── rapports/            # Rapports et exports
├── utilisateurs/        # Gestion des utilisateurs
├── templates/           # Templates HTML
├── static/              # Fichiers statiques
├── media/               # Uploads
└── requirements.txt     # Dépendances

## Identifiants par défaut

- Utilisateur : admin
- Mot de passe : admin123

À CHANGER EN PRODUCTION !

## Licence

Propriétaire - Magasin Madina, Conakry, Guinée
