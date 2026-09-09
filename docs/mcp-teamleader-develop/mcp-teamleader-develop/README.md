# mcp-teamleader

Un serveur MCP (Model Context Protocol) qui connecte Claude Desktop à l'API du CRM Teamleader, permettant de lister des contacts, gérer des entreprises, créer et modifier des opportunités et des devis — le tout en langage naturel dans Claude Desktop.

---

## Table des matières

- [Présentation](#présentation)
- [Architecture](#architecture)
- [Outils disponibles](#outils-disponibles)
- [Workflow des devis](#workflow-des-devis)
- [Installation](#installation)
  - [Prérequis](#prérequis)
  - [Installation (Windows)](#installation-windows)
  - [Installation (macOS)](#installation-macos)
- [Configuration de Claude Desktop](#configuration-de-claude-desktop)
- [Authentification](#authentification)
- [Modèles de requêtes](#modèles-de-requêtes)
- [Exemples de requêtes par outil](#exemples-de-requêtes-par-outil)

---

## Présentation

`mcp-teamleader` est un serveur MCP local écrit en Python. Il est utilisé exclusivement via **Claude Desktop** et expose 25 outils qui interagissent avec l'API Teamleader pour :

- Lister, rechercher, créer et modifier des contacts
- Lister, rechercher, créer et modifier des entreprises (avec adresse et liaison de contacts)
- Lister, rechercher, créer et modifier des produits
- Lister les taux de TVA
- Créer et gérer des opportunités (deals), avec recherche par titre/référence/nom du client
- Créer et modifier des devis avec gestion complète des lignes : ajout, modification et suppression (produits, lignes libres, sections)

Le serveur gère l'authentification OAuth 2.0 automatiquement, incluant le rafraîchissement silencieux des tokens et un flux de ré-authentification complet qui relance Claude Desktop si nécessaire.

---

## Architecture

```
mcp-teamleader/
├── mcp_server.py          # Point d'entrée MCP — enregistre et dispatch tous les outils
├── pyproject.toml         # Configuration du projet et dépendances
├── .env                   # Variables d'environnement
│
├── teamleader/            # Couche métier de l'API Teamleader
│   ├── auth.py            # Gestion du cycle de vie des tokens OAuth
│   ├── contacts.py        # Contacts (Lecture, Création, Modification)
│   ├── companies.py       # Entreprises (Lecture, Création, Modification)
│   ├── products.py        # Produits (Lecture, Création, Modification)
│   ├── deals.py           # Opportunités (Création, Lecture, Modification)
│   ├── tax_rates.py       # Taux de TVA (Lecture)
│   └── quotations.py      # Devis (Création, Lecture, Modification, CRUD lignes)
│
├── scripts/
│   └── auto_reauth.py     # Sous-processus de ré-authentification OAuth (flux navigateur)
│
└── utils/
    ├── env.py             # Helpers de lecture/écriture du fichier .env
    └── state.py           # État du cycle de ré-authentification (fichier)
```

### Structure en couches

| Couche | Emplacement | Rôle |
|--------|-------------|------|
| Transport MCP | `mcp_server.py` | Enregistrement et dispatch des outils, aucune logique métier |
| Logique métier | `teamleader/` | Un module par domaine, appelle l'API REST Teamleader |
| Utilitaires | `utils/` | Gestion de l'environnement, état inter-processus |
| Ré-authentification | `scripts/auto_reauth.py` | Sous-processus séparé pour le flux OAuth navigateur |

### Système de packages

Le projet utilise `pip install -e .` pour s'installer en tant que package éditable. Cela rend `teamleader` et `utils` importables en tant que packages de premier niveau depuis n'importe où dans le projet — aucun hack `sys.path` nécessaire. Chaque dossier possède un `__init__.py` pour être reconnu comme package Python.

---

## Outils disponibles

### Contacts

| Outil | Description |
|-------|-------------|
| `list_contacts` | Lister les contacts avec filtre de recherche optionnel (`term` : nom, prénom, email ou téléphone) et pagination (`page`, `size`). Retourne id, nom complet, email, téléphone, pays. |
| `create_contact` | Créer un nouveau contact. Paramètres : `last_name` (requis), `first_name`, `email`, `phone`, `language`. |
| `update_contact` | Modifier un contact existant. Paramètres : `contact_id` (requis), `first_name`, `last_name`, `email`, `phone`, `language`. Seuls les champs fournis sont modifiés. |

### Entreprises

| Outil | Description |
|-------|-------------|
| `list_companies` | Lister les entreprises avec filtre de recherche optionnel (`term` : nom, email ou téléphone) et pagination (`page`, `size`). Retourne id, nom, email, téléphone, pays, numéro de TVA. |
| `create_company` | Créer une nouvelle entreprise. Paramètres : `name` (requis), `email`, `phone`, `vat_number`, `language`, `website`, `address_line`, `postal_code`, `city`, `country`, `address_type`. |
| `update_company` | Modifier une entreprise existante. Paramètres : `company_id` (requis), `name`, `email`, `phone`, `vat_number`, `language`, `website`, `address_line`, `postal_code`, `city`, `country`, `address_type`. Seuls les champs fournis sont modifiés. |
| `link_contact_to_company` | Lier un contact à une entreprise. Paramètres : `contact_id` (requis), `company_id` (requis), `position`, `decision_maker`. |
| `unlink_contact_from_company` | Délier un contact d'une entreprise. Paramètres : `contact_id` (requis), `company_id` (requis). |

### Produits

| Outil | Description |
|-------|-------------|
| `list_products` | Lister les produits avec filtre de recherche optionnel (`term` : nom ou code) et pagination (`page`, `size`). Retourne id, nom, code, prix de vente/achat, info TVA, unité. |
| `create_product` | Créer un nouveau produit. Paramètres : `name` (requis), `description`, `code`, `selling_price`, `currency`, `purchase_price`, `tax_rate_id`. |
| `update_product` | Modifier un produit existant. Paramètres : `product_id` (requis), `name`, `description`, `code`, `selling_price`, `currency`, `purchase_price`, `tax_rate_id`. Seuls les champs fournis sont modifiés. |

### Taux de TVA

| Outil | Description |
|-------|-------------|
| `list_tax_rates` | Lister tous les taux de TVA disponibles — retourne id, description, pourcentage. |

### Opportunités (Deals)

| Outil | Description |
|-------|-------------|
| `list_deals` | Lister les opportunités avec filtres optionnels : `term` (recherche sur titre, référence, nom du client), `customer_type` + `customer_id`, et pagination. |
| `get_deal` | Obtenir les détails complets d'une opportunité par id. |
| `create_deal` | Créer une nouvelle opportunité liée à un contact ou une entreprise. |

### Devis

| Outil | Description |
|-------|-------------|
| `list_quotations` | Lister les devis, avec filtre optionnel par ID d'opportunité (`deal_id`), et pagination. |
| `get_quotation` | Obtenir les détails complets d'un devis incluant toutes les lignes (groupées par section). |
| `create_quotation` | Créer un devis vide lié à une opportunité. |
| `update_quotation` | Modifier la devise ou la date d'expiration d'un devis. |
| `add_product_to_quotation` | Ajouter un produit (lié par product_id) comme ligne de devis (avec options de remise et périodicité). |
| `add_custom_line_to_quotation` | Ajouter une ligne libre (sans référence produit) à un devis. |
| `update_line_in_quotation` | Modifier une ligne existante (description, quantité, prix unitaire, taux TVA, remise…). Identifie la ligne par titre de section + description de la ligne. |
| `delete_line_from_quotation` | Supprimer une ligne de devis. Identifie par titre de section + description de la ligne. Supprime la section si elle devient vide. |
| `add_contact_to_quotation` | Lier un contact comme client du devis (via l'opportunité associée). |
| `add_company_to_quotation` | Lier une entreprise comme client du devis (via l'opportunité associée). |

---

## Workflow des devis

La gestion des devis suit un workflow spécifique en raison du fonctionnement de l'API Teamleader. Voici la relation entre les outils :

### Flux de création typique

```
1. create_deal                      → Crée l'opportunité
2. create_quotation (deal_id)       → Crée un devis vide lié à l'opportunité
3. add_product_to_quotation         → Ajoute une ligne produit à une section
   ou add_custom_line_to_quotation  → Ajoute une ligne libre à une section
4. add_contact_to_quotation         → Lie le client (contact ou entreprise)
   ou add_company_to_quotation
```

### Gestion des lignes (lecture-modification-écriture)

L'API Teamleader remplace **toutes** les lignes à chaque mise à jour. Le serveur gère cela de manière transparente :

1. **Lecture** — Récupère le devis actuel via `quotations.info` (`_get_quotation_raw`)
2. **Normalisation** — Convertit le format de lecture en format d'écriture (`_normalize_grouped_lines`), ex. `tax.id` → `tax_rate_id`
3. **Modification** — Ajoute, modifie ou supprime la ligne ciblée
4. **Écriture** — Envoie le tableau complet `grouped_lines` modifié via `quotations.update`

Ce pattern est partagé par :
- `add_product_to_quotation` / `add_custom_line_to_quotation` — ajoute une ligne
- `update_line_in_quotation` — modifie les champs de la ligne correspondante (seuls les champs fournis sont changés)
- `delete_line_from_quotation` — supprime la ligne correspondante (et la section si elle est vide)

Les lignes sont identifiées par **titre de section** + **description de la ligne** (première correspondance). Il n'y a pas d'ID de ligne stable exposé par l'API.

### Fonctions internes (privées)

| Fonction | Rôle |
|----------|------|
| `_get_quotation_raw()` | Récupère les données brutes de l'API pour les opérations lecture-modification-écriture |
| `_normalize_grouped_lines()` | Convertit le format de lecture API → format d'écriture |
| `_format_grouped_lines()` | Convertit les données brutes → format d'affichage propre pour le LLM |
| `_add_line_item()` | Logique partagée pour l'ajout d'une ligne (utilisée par add_product et add_custom_line) |

---

## Installation

### Prérequis

- Python 3.10 ou supérieur
- Claude Desktop installé
- Un compte Teamleader avec des identifiants API (OAuth Client ID et Client Secret)

---

### Installation (Windows)

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/your-org/mcp-teamleader.git
   cd mcp-teamleader
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   ```

3. **Installer le projet et ses dépendances**
   ```bash
   venv\Scripts\pip install -e .
   ```

4. **Configurer les variables d'environnement**

   Copier `.env.example` vers `.env` et renseigner vos identifiants OAuth Teamleader :
   ```
   TEAMLEADER_CLIENT_ID=votre_client_id
   TEAMLEADER_CLIENT_SECRET=votre_client_secret
   ```
   Les champs de tokens (`TEAMLEADER_ACCESS_TOKEN`, `TEAMLEADER_REFRESH_TOKEN`, etc.) sont remplis automatiquement lors de la première authentification.

5. **Configurer Claude Desktop** — voir [Configuration de Claude Desktop](#configuration-de-claude-desktop) ci-dessous.

6. **Redémarrer Claude Desktop** et lancer une première requête — l'authentification se lancera automatiquement dans votre navigateur.

---

### Installation (macOS)

1. **Cloner le dépôt**
   ```bash
   git clone https://github.com/your-org/mcp-teamleader.git
   cd mcp-teamleader
   ```

2. **Créer un environnement virtuel**
   ```bash
   python3 -m venv venv
   ```

3. **Installer le projet et ses dépendances**
   ```bash
   venv/bin/pip install -e .
   ```

4. **Configurer les variables d'environnement**

   Copier `.env.example` vers `.env` et renseigner vos identifiants :
   ```
   TEAMLEADER_CLIENT_ID=votre_client_id
   TEAMLEADER_CLIENT_SECRET=votre_client_secret
   ```

5. **Configurer Claude Desktop** — voir ci-dessous.

6. **Redémarrer Claude Desktop** et lancer une première requête pour s'authentifier.

---

## Configuration de Claude Desktop

Ouvrir le fichier de configuration développeur de Claude Desktop et ajouter l'entrée du serveur `mcp-teamleader`.

**Emplacement du fichier de configuration :**
- Windows : `%APPDATA%\Claude\claude_desktop_config.json`
- macOS : `~/Library/Application Support/Claude/claude_desktop_config.json`

**Exemple Windows :**
```json
{
  "mcpServers": {
    "mcp-teamleader": {
      "command": "C:\\Users\\VotreNom\\mcp-teamleader\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\VotreNom\\mcp-teamleader\\mcp_server.py"
      ]
    }
  }
}
```

**Exemple macOS :**
```json
{
  "mcpServers": {
    "mcp-teamleader": {
      "command": "/Users/votrenom/mcp-teamleader/venv/bin/python",
      "args": [
        "/Users/votrenom/mcp-teamleader/mcp_server.py"
      ]
    }
  }
}
```

> **Important :** Le chemin `command` doit pointer vers l'exécutable Python à l'intérieur du `venv` du projet. Ce chemin est spécifique à chaque machine et ne doit jamais être commité dans le dépôt. Chaque développeur doit définir son propre chemin absolu.

---

## Authentification

Le serveur utilise OAuth 2.0 avec gestion automatique des tokens :

1. **Rafraîchissement silencieux** — La vérification du token est effectuée silencieusement à chaque exécution d'outil. Si tout est OK, le token d'accès est automatiquement retourné via des vérifications Python, sans aucun appel API. Lorsque le token d'accès expire, il est rafraîchi silencieusement à l'aide du token de rafraîchissement. Aucune action utilisateur requise.
2. **Ré-authentification complète** — Lorsque le token de rafraîchissement est manquant ou expire dans moins de 7 jours, le serveur :
   - Lance `auto_reauth.py` dans un sous-processus
   - Ouvre votre navigateur sur la page d'autorisation Teamleader
   - Écoute sur `http://localhost:3000` pour le callback OAuth
   - Écrit les nouveaux tokens dans `.env`
   - Redémarre Claude Desktop automatiquement

Après la ré-authentification, Claude Desktop redémarre et reprend normalement. Aucune action manuelle n'est nécessaire.

---

## Modèles de requêtes

Voici les formulations recommandées pour vos requêtes à Claude pour chaque opération majeure.

---

### Lister ou rechercher des contacts

> Lister tous les contacts
> Montre-moi le contact **[nom / prénom / email / téléphone]**

Exemples :
- *Lister tous les contacts*
- *Montre-moi le contact Jean Dupont*
- *Trouver le contact avec l'email jean.dupont@example.com*
- *Chercher le contact +33 6 12 34 56 78*
- *Affiche-moi les 50 premiers contacts*

---

### Créer un contact

> Créer un contact **[prénom]** **[nom]** avec l'email **[email]** et le téléphone **[téléphone]**

Exemples :
- *Créer un contact Jean Dupont avec l'email jean.dupont@example.com*
- *Ajouter un nouveau contact : Marie Martin, téléphone +33 6 98 76 54 32, langue fr*
- *Créer le contact Pierre Durand*

---

### Modifier un contact

> Modifier le contact **[nom]** : **[changements]**

Exemples :
- *Modifier le contact Jean Dupont : changer l'email en jean.dupont@newmail.com*
- *Mettre à jour le téléphone de Marie Martin en +33 6 11 22 33 44*
- *Changer le nom de famille du contact Pierre en Durand-Lefèvre*

---

### Lister ou rechercher des entreprises

> Lister toutes les entreprises
> Montre-moi l'entreprise **[nom / email / téléphone]**

Exemples :
- *Lister toutes les entreprises*
- *Montre-moi l'entreprise Acme Corp*
- *Chercher l'entreprise avec l'email contact@acme.com*
- *Affiche les entreprises en page 2*

---

### Créer une entreprise

> Créer une entreprise **[nom]** avec le numéro de TVA **[TVA]** et l'email **[email]**
> Adresse : **[rue]**, **[code postal]** **[ville]**, **[pays]**

Exemples :
- *Créer une entreprise Acme Corp avec l'email contact@acme.com et le numéro de TVA BE0123456789*
- *Ajouter l'entreprise Dupont & Fils, téléphone +33 1 23 45 67 89, site web www.dupont-fils.fr, adresse 15 rue de la Paix, 75002 Paris, FR*
- *Créer l'entreprise Tech Solutions, langue fr, adresse Dok Noord 3A 101, 9000 Ghent, BE*

---

### Modifier une entreprise

> Modifier l'entreprise **[nom]** : **[changements]**

Exemples :
- *Modifier l'entreprise Acme Corp : changer l'email en info@acme.com*
- *Mettre à jour le numéro de TVA d'Acme Corp en FR12345678901*
- *Changer l'adresse de Tech Solutions en 10 rue du Commerce, 69001 Lyon, FR*
- *Changer le site web de Tech Solutions en www.techsolutions.io*

---

### Lier un contact à une entreprise

> Lier le contact **[nom du contact]** à l'entreprise **[nom de l'entreprise]** en tant que **[poste]**

Exemples :
- *Lier le contact Jean Dupont à l'entreprise Acme Corp en tant que Directeur commercial*
- *Associer Marie Martin à Tech Solutions, décisionnaire*
- *Rattacher Pierre Durand à Dupont & Fils, poste Responsable technique*
- *Délier le contact Jean Dupont de l'entreprise Acme Corp*
- *Retirer Marie Martin de Tech Solutions*

---

### Lister ou rechercher des produits

> Lister tous les produits
> Rechercher le produit **[nom / code]**

Exemples :
- *Lister tous les produits*
- *Rechercher le produit "Développement Frontend"*
- *Trouver le produit avec le code DEV-001*

---

### Créer un produit

> Créer un produit **[nom]** au prix de **[prix]** avec le code **[code]**

Exemples :
- *Créer un produit "Développement Frontend" au prix de 150 EUR, code DEV-001*
- *Ajouter un produit "Maintenance mensuelle" à 500 EUR avec la description "Support technique mensuel"*
- *Créer le produit "Hébergement VPS" au prix de vente 80 EUR et prix d'achat 40 EUR*

---

### Modifier un produit

> Modifier le produit **[nom / code]** : **[changements]**

Exemples :
- *Modifier le produit "Développement Frontend" : changer le prix à 180 EUR*
- *Mettre à jour la description du produit DEV-001*
- *Changer le code du produit "Hébergement VPS" en HOST-001*

---

### Afficher un devis

> Montre-moi le devis **[nom du devis / id]** avec **[nom du client (contact ou entreprise)]**

Le serveur recherche d'abord l'opportunité liée au devis, puis récupère les détails du devis.

Exemples :
- *Montre-moi le devis DEV-2024-001 pour Acme Corp*
- *Quelles sont les lignes du devis pour Jean Dupont ?*
- *Affiche le devis lié à l'opportunité id abc123*

---

### Afficher une opportunité (deal)

> Montre-moi l'opportunité **[nom / id]** avec **[nom du client (contact ou entreprise)]**

Exemples :
- *Montre-moi l'opportunité "Refonte du site web" pour Acme Corp*
- *Rechercher les opportunités correspondant à "Site web"*
- *Quel est le statut de l'opportunité de Jean Dupont ?*
- *Affiche l'opportunité id abc123*

---

### Créer un devis

> Créer un devis pour **[nom du contact ou de l'entreprise]** avec les lignes suivantes :
> - Section : **[nom de la section]**
> - Ligne : **[nom de la ligne]**, prix **[prix unitaire]**, quantité **[qté]**, description **[description]**
> - ...
>
> Appliquer un taux de TVA de **[X%]**. *(par défaut : TVA 20%)*
> Appliquer une remise de **[X%]** si nécessaire.

Cette opération :
1. Crée une opportunité (deal) si nécessaire
2. Récupère l'id du taux de TVA approprié
3. Crée le devis lié à l'opportunité
4. Ajoute toutes les lignes dans l'ordre

Exemples :
- *Créer un devis pour Acme Corp avec : Section "Développement" — Ligne "Intégration frontend", prix 1500, quantité 1, description "Intégration React". Appliquer la TVA à 20%.*
- *Créer un devis pour Jean Dupont — Section "Design", Ligne "Maquettes UI" 800 x1, Ligne "Logo" 400 x1. Remise de 10% sur la ligne logo. Taux de TVA par défaut.*

---

### Modifier un devis

> Modifier le devis **[devis / id]** pour **[nom du client (contact ou entreprise)]** :
> **[décrire les changements]**

Exemples :
- *Modifier le devis DEV-2024-001 pour Acme Corp : changer la date d'expiration au 31 mars 2025*
- *Sur le devis de Jean Dupont, ajouter une ligne "Maintenance" dans la section "Web", 200, quantité 12*
- *Modifier le devis pour Acme Corp : ajouter une section "Hébergement" avec une ligne libre "Serveur VPS" à 80*

---

### Modifier une ligne de devis existante

> Sur le devis pour **[nom du client]**, modifier la ligne **[description de la ligne]** dans la section **[nom de la section]** : **[nouvelles valeurs]**

Exemples :
- *Sur le devis pour Acme Corp, modifier la ligne "Intégration frontend" dans la section "Développement" : mettre le prix à 1800*
- *Modifier la ligne "Maquettes UI" dans la section "Design" du devis de Jean Dupont : quantité 2, remise 15%*
- *Changer la description de "Serveur VPS" dans la section "Hébergement" en "Serveur dédié"*

---

### Supprimer une ligne de devis

> Sur le devis pour **[nom du client]**, supprimer la ligne **[description de la ligne]** de la section **[nom de la section]**

Exemples :
- *Sur le devis pour Acme Corp, supprimer la ligne "Logo" de la section "Design"*
- *Supprimer la ligne "Maintenance" de la section "Web" sur le devis de Jean Dupont*
