# Cahier des Charges Technique
## Application fullstack Django — GesStock Madina

*Gestion de Stock · Marché de Madina, Conakry, Guinée*

| Champ | Valeur |
|---|---|
| **Projet** | GesStock Madina |
| **Stack** | Django 5.x + PostgreSQL + HTMX + Alpine.js |
| **Architecture** | Fullstack monolithique — PWA offline-first |
| **Version** | 1.0 — Document technique initial |
| **Date** | Avril 2026 |

---

## Table des matières

1. [Stack technologique](#1-stack-technologique)
2. [Structure du projet Django](#2-structure-du-projet-django)
3. [Modèles de données (ORM Django)](#3-modèles-de-données-orm-django)
4. [Vues, URLs et logique métier](#4-vues-urls-et-logique-métier)
5. [Mode hors-ligne (PWA Offline-First)](#5-mode-hors-ligne-pwa-offline-first)
6. [Authentification et permissions](#6-authentification-et-permissions)
7. [Templates, frontend et UX](#7-templates-frontend-et-ux)
8. [Génération PDF et exports](#8-génération-pdf-et-exports)
9. [Performance et sécurité](#9-performance-et-sécurité)
10. [Déploiement et infrastructure](#10-déploiement-et-infrastructure)
11. [Dépendances Python](#11-dépendances-python-requirements)
12. [Planning de développement](#12-planning-de-développement)

---

## 1. Stack technologique

### 1.1 Vue d'ensemble

> **Note :** Choix d'une architecture monolithique Django fullstack — simple à déployer, à maintenir et à faire évoluer. Idéale pour une seule équipe de développement.

| Couche | Technologie | Version | Rôle |
|---|---|---|---|
| Backend | Python / Django | 3.12 / 5.x | Logique métier, ORM, vues, API |
| Base de données | PostgreSQL | 16+ | Stockage principal |
| Frontend | HTMX | 2.x | Interactivité sans SPA (requêtes AJAX déclaratives) |
| Frontend JS | Alpine.js | 3.x | Micro-interactions côté client |
| CSS | Tailwind CSS | 3.x | Styling utilitaire, responsive |
| Offline / PWA | Service Worker + Workbox | — | Cache & synchronisation hors-ligne |
| PDF | WeasyPrint | dernière | Génération de factures PDF |
| Excel | openpyxl | dernière | Export des rapports `.xlsx` |
| Auth | django-allauth | — | Authentification, sessions |
| Tâches async | Celery + Redis | — | Envoi de rapports, sync background |
| Serveur web | Gunicorn + Nginx | — | Production |
| Déploiement | VPS Linux (Ubuntu 22) | — | Hébergement (ex. DigitalOcean, OVH) |

### 1.2 Pourquoi ce choix de stack ?

- Django fournit l'admin, l'ORM, les formulaires, l'auth — tout en un, sans assembler des briques séparées
- HTMX évite un frontend React/Vue complexe : les pages restent des templates Django avec des fragments dynamiques
- Alpine.js gère les dropdowns, toggles, validations légères — sans bundler webpack
- Tailwind CSS est compilé en production pour un CSS minimal et rapide
- PostgreSQL offre les transactions ACID nécessaires pour la cohérence stock/ventes
- Service Worker + Workbox gère le mode hors-ligne sans framework tiers

---

## 2. Structure du projet Django

### 2.1 Arborescence

```
gesstock/                    # Répertoire racine du projet
├── config/                  # Settings, urls, wsgi, asgi
│   ├── settings/
│   │   ├── base.py          # Settings communs
│   │   ├── dev.py           # Dev local (DEBUG=True, SQLite optionnel)
│   │   └── prod.py          # Production (PostgreSQL, sécurité)
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/                # App principale : dashboard, base templates
│   ├── produits/            # Produits, catégories, stock
│   ├── clients/             # Clients, dettes
│   ├── fournisseurs/        # Fournisseurs
│   ├── ventes/              # Ventes, lignes de vente
│   ├── paiements/           # Paiements, versements
│   ├── factures/            # Génération PDF des factures
│   ├── stock/               # Mouvements de stock, inventaire
│   ├── rapports/            # Reporting, exports
│   └── utilisateurs/        # Gestion rôles, profils
├── static/
│   ├── css/                 # Tailwind compilé
│   ├── js/                  # Alpine.js, HTMX, service worker
│   └── icons/               # PWA icons
├── templates/               # Templates Django globaux
│   ├── base.html
│   ├── partials/            # Fragments HTMX
│   └── [app]/               # Templates par app
├── media/                   # Uploads (photos produits)
├── locale/                  # i18n (français)
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── manage.py
└── .env                     # Variables d'environnement (non versionné)
```

### 2.2 Conventions de code

- **Langue du code :** anglais (noms de variables, fonctions, classes, commentaires)
- **Langue de l'interface :** français (labels, messages, templates)
- **Formatage :** Black + isort — exécutés via pre-commit hooks
- **Linting :** Flake8 / Ruff
- **Tests :** pytest-django — couverture minimale 70 % sur la logique métier
- **Commits :** convention Conventional Commits (`feat:`, `fix:`, `chore:`…)
- **Versioning :** Git — branche `main` (prod) + `develop` + feature branches

---

## 3. Modèles de données (ORM Django)

### 3.1 App : `produits`

#### `Categorie`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `nom` | `CharField(100)` | unique, not null | Nom de la catégorie |
| `description` | `TextField` | blank=True | Description optionnelle |
| `created_at` | `DateTimeField` | auto_now_add | Date de création |

#### `Produit`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `code` | `CharField(50)` | unique | Référence interne |
| `nom` | `CharField(200)` | not null | Nom du produit |
| `categorie` | `ForeignKey(Categorie)` | CASCADE | Catégorie du produit |
| `unite_mesure` | `CharField(50)` | not null | sac, carton, litre, kg… |
| `prix_achat` | `DecimalField(12,2)` | not null | Coût fournisseur |
| `prix_vente_gros` | `DecimalField(12,2)` | not null | Prix de vente grossiste |
| `prix_vente_detail` | `DecimalField(12,2)` | not null | Prix vente détail |
| `stock_actuel` | `DecimalField(12,3)` | default=0 | Quantité en stock |
| `seuil_alerte` | `DecimalField(12,3)` | default=0 | Seuil d'alerte minimum |
| `photo` | `ImageField` | blank=True | Photo du produit |
| `actif` | `BooleanField` | default=True | Produit actif/archivé |
| `created_at` | `DateTimeField` | auto_now_add | Date de création |
| `updated_at` | `DateTimeField` | auto_now | Dernière modification |

> `stock_actuel` est mis à jour automatiquement via des **signals Django** à chaque mouvement de stock validé.

---

### 3.2 App : `stock`

#### `MouvementStock`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `produit` | `ForeignKey(Produit)` | CASCADE | Produit concerné |
| `type_mvt` | `CharField(20)` | choices | `ENTREE / SORTIE / AJUSTEMENT / INVENTAIRE` |
| `quantite` | `DecimalField(12,3)` | not null | Quantité (positive) |
| `motif` | `TextField` | blank=True | Raison (obligatoire pour AJUSTEMENT) |
| `fournisseur` | `ForeignKey(Fournisseur)` | null=True | Fournisseur (si ENTREE) |
| `vente` | `ForeignKey(Vente)` | null=True | Vente liée (si SORTIE) |
| `prix_unitaire` | `DecimalField(12,2)` | null=True | Prix à ce moment (entrées) |
| `utilisateur` | `ForeignKey(User)` | SET_NULL, null=True | Qui a fait l'action |
| `created_at` | `DateTimeField` | auto_now_add | Date du mouvement |

---

### 3.3 App : `clients`

#### `Client`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `nom` | `CharField(150)` | not null | Nom complet |
| `telephone` | `CharField(20)` | not null | Téléphone principal |
| `telephone2` | `CharField(20)` | blank=True | Téléphone secondaire |
| `quartier` | `CharField(100)` | blank=True | Quartier / adresse |
| `type_client` | `CharField(30)` | choices | `REVENDEUR / PARTICULIER / RESTAURATEUR…` |
| `solde_du` | `DecimalField(14,2)` | default=0 | Montant total dû (calculé) |
| `notes` | `TextField` | blank=True | Notes libres |
| `actif` | `BooleanField` | default=True | Client actif/archivé |
| `created_at` | `DateTimeField` | auto_now_add | Date d'enregistrement |

> `solde_du` est recalculé via une propriété `@property` ou une annotation `QuerySet` — jamais stocké en dur sans signal de cohérence.

---

### 3.4 App : `fournisseurs`

#### `Fournisseur`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `nom` | `CharField(150)` | not null | Nom du fournisseur |
| `telephone` | `CharField(20)` | blank=True | Contact |
| `adresse` | `TextField` | blank=True | Adresse |
| `solde_du` | `DecimalField(14,2)` | default=0 | Dette envers ce fournisseur |
| `notes` | `TextField` | blank=True | Notes libres |
| `created_at` | `DateTimeField` | auto_now_add | Date d'enregistrement |

---

### 3.5 App : `ventes`

#### `Vente`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `numero` | `CharField(30)` | unique | Numéro de vente (ex. `VTE-2025-00042`) |
| `client` | `ForeignKey(Client)` | null=True | Client (null = vente anonyme) |
| `date_vente` | `DateTimeField` | auto_now_add | Date et heure |
| `montant_total` | `DecimalField(14,2)` | not null | Total de la vente |
| `montant_paye` | `DecimalField(14,2)` | default=0 | Montant encaissé |
| `solde_restant` | `DecimalField(14,2)` | default=0 | Montant encore dû |
| `statut` | `CharField(20)` | choices | `EN_ATTENTE / PARTIEL / SOLDE` |
| `notes` | `TextField` | blank=True | Remarques |
| `utilisateur` | `ForeignKey(User)` | SET_NULL | Qui a enregistré |
| `created_at` | `DateTimeField` | auto_now_add | Timestamp |

#### `LigneVente`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `vente` | `ForeignKey(Vente)` | CASCADE | Vente parente |
| `produit` | `ForeignKey(Produit)` | CASCADE | Produit vendu |
| `quantite` | `DecimalField(12,3)` | not null | Quantité vendue |
| `prix_unitaire` | `DecimalField(12,2)` | not null | Prix au moment de la vente |
| `sous_total` | `DecimalField(14,2)` | not null | `quantite × prix_unitaire` |

---

### 3.6 App : `paiements`

#### `Paiement`

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `id` | `AutoField` | PK | Identifiant auto |
| `vente` | `ForeignKey(Vente)` | CASCADE | Vente concernée |
| `client` | `ForeignKey(Client)` | CASCADE | Client (dénormalisé pour rapidité) |
| `montant` | `DecimalField(14,2)` | not null | Montant de ce versement |
| `mode_paiement` | `CharField(30)` | choices | `ESPECES / VIREMENT / CREDIT` |
| `reference` | `CharField(100)` | blank=True | Réf. virement bancaire |
| `date_paiement` | `DateTimeField` | auto_now_add | Date du versement |
| `utilisateur` | `ForeignKey(User)` | SET_NULL | Qui a enregistré |
| `notes` | `TextField` | blank=True | Commentaire |

---

### 3.7 App : `utilisateurs`

#### `ProfilUtilisateur` (extension de `User` Django)

| Champ | Type Django | Contraintes | Description |
|---|---|---|---|
| `user` | `OneToOneField(User)` | CASCADE | Utilisateur Django natif |
| `role` | `CharField(20)` | choices | `GERANT / EMPLOYE` |
| `telephone` | `CharField(20)` | blank=True | Contact |
| `actif` | `BooleanField` | default=True | Compte actif |

---

## 4. Vues, URLs et logique métier

### 4.1 Pattern de vues

> On utilise les **Class-Based Views (CBV)** pour les opérations CRUD standards, et des **Function-Based Views (FBV)** pour les logiques métier complexes (enregistrement d'une vente, synchronisation offline).

| App | URL pattern | Vue / Action | Accès |
|---|---|---|---|
| `core` | `/` | Dashboard | Tous |
| `produits` | `/produits/` | Liste des produits | Tous |
| `produits` | `/produits/ajouter/` | Créer produit | Gérant |
| `produits` | `/produits/<id>/modifier/` | Modifier produit | Gérant |
| `stock` | `/stock/entree/` | Entrée de stock | Tous |
| `stock` | `/stock/mouvements/` | Historique mouvements | Tous |
| `stock` | `/stock/inventaire/` | Inventaire physique | Gérant |
| `clients` | `/clients/` | Liste clients | Tous |
| `clients` | `/clients/<id>/` | Fiche client + historique | Tous |
| `clients` | `/clients/<id>/versement/` | Enregistrer versement | Tous |
| `ventes` | `/ventes/nouvelle/` | Enregistrer une vente | Tous |
| `ventes` | `/ventes/` | Historique des ventes | Tous |
| `ventes` | `/ventes/<id>/` | Détail vente | Tous |
| `factures` | `/factures/<id>/pdf/` | Générer PDF facture | Tous |
| `rapports` | `/rapports/ventes/` | Rapport de ventes | Gérant |
| `rapports` | `/rapports/stock/` | Rapport de stock | Gérant |
| `rapports` | `/rapports/clients/` | Rapport clients / dettes | Gérant |
| `rapports` | `/rapports/export/` | Export Excel | Gérant |
| `utilisateurs` | `/utilisateurs/` | Gestion des comptes | Gérant |
| `api` | `/api/sync/` | Endpoint sync offline (JSON) | Tous (auth) |

### 4.2 Logique métier clé

#### Enregistrement d'une vente (atomique)

- Toute la transaction est wrappée dans `transaction.atomic()`
- Vérification du stock disponible pour chaque ligne avant validation
- Création des `LigneVente` et du `Paiement` initial
- Génération automatique du numéro de vente (`VTE-AAAA-XXXXX`)
- Émission d'un signal `post_save` qui déclenche les mouvements de stock en `SORTIE`
- Mise à jour du `solde_du` du client si paiement partiel ou à crédit

#### Mouvements de stock (via signals)

- Signal `post_save` sur `LigneVente` → crée automatiquement un `MouvementStock SORTIE`
- Signal `post_save` sur `MouvementStock ENTREE` → incrémente `Produit.stock_actuel`
- Signal `post_save` sur `MouvementStock SORTIE` → décrémente `Produit.stock_actuel`
- Tout ajustement manuel requiert un motif et est tracé avec l'utilisateur

#### Calcul du solde client

- Le `solde_du` est annoté dynamiquement via `QuerySet.annotate()` pour l'affichage des listes
- Pour la fiche client : `SUM(ventes.montant_total) - SUM(paiements.montant)`
- Un signal `post_save` sur `Paiement` met à jour `Vente.montant_paye` et `Vente.statut`

---

## 5. Mode hors-ligne (PWA Offline-First)

### 5.1 Stratégie globale

> La connexion au marché de Madina est instable. L'application doit fonctionner **intégralement sans internet** et synchroniser automatiquement dès que la connexion revient.

| Ressource | Stratégie Service Worker | Détail |
|---|---|---|
| HTML / templates | Cache First | Mise en cache au premier chargement |
| CSS / JS / images | Cache First | Precache via Workbox au build |
| Ventes offline | Background Sync | File d'attente persistante (IndexedDB) |
| Entrées de stock offline | Background Sync | Idem — synchronisées à la reconnexion |
| Données produits/clients | Network First + Cache | Fraîches si réseau, sinon cache local |
| Génération PDF | Network Only | Requiert la connexion — signalé à l'utilisateur |

### 5.2 Implémentation technique

#### Service Worker (Workbox)

- Workbox 7.x géré côté static Django
- Precaching de tous les assets statiques à chaque déploiement
- Background Sync API pour les requêtes POST échouées (ventes, paiements)
- La file d'attente persiste dans IndexedDB côté navigateur

#### Endpoint de synchronisation

- **URL :** `POST /api/sync/`
- Accepte un tableau de transactions JSON signées (token JWT ou session cookie)
- Traite chaque transaction dans un `transaction.atomic()` individuel
- Retourne un rapport de succès/erreur par transaction
- **Idempotent :** un UUID client est généré pour chaque transaction offline afin d'éviter les doublons

#### Indicateur de statut connexion

- Bannière en haut de page : 🟢 En ligne / 🟠 Hors-ligne — données en attente de sync
- Compteur de transactions en attente de synchronisation
- Déclenchement automatique de la sync dès que `navigator.onLine` repasse à `true`

---

## 6. Authentification et permissions

### 6.1 Authentification

- Utilisation de l'authentification native Django (`django.contrib.auth`)
- Sessions côté serveur (pas de JWT pour le frontend — sessions Django standards)
- Connexion par identifiant + mot de passe
- Déconnexion automatique après 8h d'inactivité
- Réinitialisation du mot de passe par le Gérant uniquement (pas d'email requis)

### 6.2 Système de permissions

| Fonctionnalité | Gérant | Employé |
|---|---|---|
| Tableau de bord | Complet (CA, marges, dettes) | Simplifié (ventes du jour, alertes) |
| Consulter produits / stock | Oui | Oui |
| Ajouter / modifier produit | Oui | Non |
| Supprimer produit | Oui | Non |
| Entrée de stock | Oui | Oui |
| Ajustement manuel stock | Oui | Non |
| Enregistrer une vente | Oui | Oui |
| Annuler une vente | Oui | Non |
| Gérer les clients | Oui (CRUD complet) | Oui (lecture + versement) |
| Gérer les fournisseurs | Oui | Non |
| Accéder aux rapports | Oui | Non |
| Exporter données | Oui | Non |
| Gérer les utilisateurs | Oui | Non |

> Permissions implémentées via `LoginRequiredMixin`, `UserPassesTestMixin` et un décorateur `@gerant_required` personnalisé.

---

## 7. Templates, frontend et UX

### 7.1 Architecture des templates

- `base.html` : layout global — navbar, sidebar, zone de contenu, bannière offline
- Héritage Django : `{% extends 'base.html' %}` dans chaque page
- Partials HTMX dans `templates/partials/` — fragments rechargés sans rechargement de page
- Composants Alpine.js inline pour les menus, modales de confirmation, compteurs

### 7.2 Interactions HTMX clés

| Interaction | Déclencheur HTMX | Résultat |
|---|---|---|
| Recherche produit (vente) | `hx-trigger="keyup delay:300ms"` | Liste filtrée rechargée sans rechargement page |
| Ajout ligne de vente | `hx-post` + `hx-swap="outerHTML"` | Ligne ajoutée au panier dynamiquement |
| Mise à jour total vente | `hx-trigger="change"` | Total recalculé côté serveur, affiché |
| Versement client | `hx-post` + `hx-swap="outerHTML"` | Solde client mis à jour en temps réel |
| Alerte stock en temps réel | `hx-get` + `hx-trigger="load"` | Badge rouge affiché si seuil atteint |
| Pagination rapports | `hx-get` + `hx-push-url` | Pagination sans rechargement |

### 7.3 Charte UI

- **Palette :** bleu foncé (navigation) + blanc (contenu) + rouge (alertes) + vert (succès)
- **Police :** Inter ou système par défaut — lisible, pas décorative
- **Boutons :** grands (min 44px hauteur), libellés explicites
- **Tableaux :** alternance de lignes, tri par colonne, recherche intégrée
- **Formulaires :** validation HTML5 native + messages d'erreur en rouge sous le champ
- **Responsive :** optimisé desktop — pas de breakpoints mobile requis en v1

---

## 8. Génération PDF et exports

### 8.1 Factures PDF (WeasyPrint)

- Vue Django : `GET /factures/<id>/pdf/` → retourne `HttpResponse` `content_type='application/pdf'`
- Template dédié : `templates/factures/facture_pdf.html` — CSS print-friendly
- Contenu : en-tête magasin, numéro, client, lignes articles, totaux, mode paiement, solde restant
- Option impression directe : ouverture dans un nouvel onglet navigateur
- WeasyPrint est installé côté serveur — ne dépend pas du navigateur

### 8.2 Exports Excel (openpyxl)

- Vue Django : `GET /rapports/export/?type=ventes&debut=...&fin=...`
- Retourne un fichier `.xlsx` en streaming (`StreamingHttpResponse`)
- Rapports exportables : ventes, stock, clients & dettes, fournisseurs, bénéfices
- Formatage : en-têtes en gras, colonnes auto-dimensionnées, filtres Excel activés

### 8.3 Numérotation automatique

| Document | Format | Exemple |
|---|---|---|
| Vente | `VTE-AAAA-NNNNN` | `VTE-2025-00042` |
| Facture | `FAC-AAAA-NNNNN` | `FAC-2025-00042` |
| Entrée stock | `ENT-AAAA-NNNNN` | `ENT-2025-00015` |

> Le numéro est généré côté Python dans un bloc `transaction.atomic()` avec `select_for_update()` pour éviter les doublons en accès concurrent.

---

## 9. Performance et sécurité

### 9.1 Optimisation des requêtes

- Utilisation systématique de `select_related()` et `prefetch_related()` dans les QuerySets
- Annotations SQL (`SUM`, `COUNT`) plutôt que calculs Python sur grands ensembles
- Index PostgreSQL sur : `Produit.nom`, `Client.nom`, `Vente.date_vente`, `Vente.statut`
- Index composé sur `MouvementStock (produit, created_at)` pour les historiques
- Pagination obligatoire sur toutes les listes (25 éléments par page par défaut)
- Cache Django (memcached ou Redis) sur les rapports agrégés — TTL 5 minutes

### 9.2 Sécurité

- CSRF protection Django activée sur tous les formulaires
- Protection XSS : auto-escaping Django dans les templates
- Injection SQL : ORM Django uniquement, pas de `raw()` sans paramètres bindés
- Validation côté serveur sur tous les formulaires (`ModelForm` + validation métier)
- Pas d'exposition des IDs séquentiels dans les URLs sensibles — utiliser des slugs ou UUIDs pour les ressources critiques
- Fichiers uploadés (photos produits) servis par Nginx — jamais via Django en production
- `SECRET_KEY` et `DATABASE_URL` dans `.env` — jamais en dur dans le code
- HTTPS obligatoire en production (Let's Encrypt via Certbot)
- Headers de sécurité : `django-csp`, `X-Frame-Options`, `HSTS`

### 9.3 Logging & traçabilité

- Chaque action d'écriture (vente, paiement, ajustement) est logguée avec : utilisateur, date, données avant/après
- Log Django configuré : niveau `WARNING` en prod, `DEBUG` en dev
- Logs applicatifs dans `/var/log/gesstock/` — rotation hebdomadaire
- En cas d'erreur 500, notification par email au Gérant (`django.core.mail`)

---

## 10. Déploiement et infrastructure

### 10.1 Environnements

| Environnement | Objectif | Configuration |
|---|---|---|
| Développement | Dev local | Django runserver, SQLite ou PostgreSQL local, `DEBUG=True` |
| Staging | Tests avant mise en prod | VPS identique à prod, données anonymisées |
| Production | Live utilisateurs | VPS Ubuntu, PostgreSQL, Gunicorn, Nginx, HTTPS |

### 10.2 Stack de production

```
[ Navigateur client ]
        │  HTTPS
[ Nginx ]  ←── sert les fichiers statiques/media directement
        │  proxy_pass
[ Gunicorn (4 workers) ]
        │
[ Django Application ]
        │
[ PostgreSQL ]    [ Redis (cache + Celery broker) ]
```

### 10.3 Fichier `.env` de production

```env
DJANGO_SECRET_KEY=<clé longue et aléatoire>
DJANGO_DEBUG=False
DATABASE_URL=postgres://user:password@localhost:5432/gesstock
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=gesstock.mondomaine.com
DJANGO_SETTINGS_MODULE=config.settings.prod
```

### 10.4 Commandes de déploiement

```bash
git pull origin main
pip install -r requirements/prod.txt
python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py compilemessages
sudo systemctl restart gunicorn gesstock
```

### 10.5 Sauvegarde des données

- Backup PostgreSQL automatique quotidien : `pg_dump` → fichier compressé `.sql.gz`
- Conservation : 7 sauvegardes quotidiennes + 4 hebdomadaires
- Stockage sur un second serveur ou bucket objet (ex. Backblaze B2)
- Procédure de restauration documentée et testée tous les mois

---

## 11. Dépendances Python (requirements)

### `requirements/base.txt`

```txt
Django>=5.0,<6.0
psycopg2-binary>=2.9
django-environ>=0.11          # Gestion des variables .env
Pillow>=10.0                  # Traitement des images (photos produits)
WeasyPrint>=62.0              # Génération PDF
openpyxl>=3.1                 # Export Excel
django-allauth>=0.63          # Authentification
django-htmx>=1.18             # Intégration HTMX dans Django
django-crispy-forms>=2.1      # Formulaires stylisés
crispy-tailwind>=1.0          # Adapter Tailwind pour crispy
django-csp>=3.8               # Headers Content-Security-Policy
```

### `requirements/prod.txt`

```txt
-r base.txt
gunicorn>=22.0
celery>=5.3
redis>=5.0
```

### `requirements/dev.txt`

```txt
-r base.txt
pytest-django>=4.8
factory-boy>=3.3              # Fixtures de test
black>=24.0
ruff>=0.4
django-debug-toolbar>=4.4
coverage>=7.5
```

---

## 12. Planning de développement

| Phase | Tâches | Durée estimée |
|---|---|---|
| **Phase 0 — Setup** | Init projet Django, config settings (dev/prod), PostgreSQL, Tailwind, HTMX, Workbox, CI | 1 semaine |
| **Phase 1 — Produits & Stock** | Modèles Produit/Categorie/Mouvement, CRUD produits, entrées stock, dashboard basique | 2–3 semaines |
| **Phase 2 — Clients & Fournisseurs** | Modèles Client/Fournisseur, CRUD, fiche client, gestion des dettes | 1–2 semaines |
| **Phase 3 — Ventes & Facturation** | Enregistrement vente (panier HTMX), paiements, génération PDF WeasyPrint | 3 semaines |
| **Phase 4 — Reporting** | Rapports agrégés (SQL annotations), graphiques, exports Excel | 2 semaines |
| **Phase 5 — PWA Offline** | Service Worker Workbox, Background Sync, endpoint `/api/sync/`, indicateur statut | 2 semaines |
| **Phase 6 — Auth & Permissions** | Rôles Gérant/Employé, dashboards différenciés, logs d'audit | 1 semaine |
| **Phase 7 — Tests & Déploiement** | Tests unitaires et d'intégration, déploiement VPS, formation utilisateur | 2 semaines |

**Durée totale estimée : 14 à 17 semaines.**

---

*GesStock Madina — Document technique v1.0 — Confidentiel*
