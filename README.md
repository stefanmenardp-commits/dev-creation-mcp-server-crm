# Création d’un serveur MCP personnalisé pour Teamleader

Développement d'un serveur MCP pour faciliter les interactions avec le CRM Teamleader

## Avis de confidentialité

Ce projet a été mené dans un cadre professionnel.

Le code source, les données de production, les informations relatives aux clients et les captures d'écran originales ne sont pas accessibles au public pour des raisons de confidentialité.

Ce référentiel présente la portée du projet et l’architecture technique et le code effectué.

## Table des matières

- [Présentation du projet](#présentation-du-projet)
- [Contexte métier](#contexte-métier)
- [Objectifs](#objectifs)
- [Fonctionnalités couvertes](#fonctionnalités-couvertes)
- [Architecture technique](#architecture-technique)
- [Etapes d'un worflow](#etapes-d'un-worflow)
- [Stack technique](#stack-technique)
- [Compétences développées](#compétences-développées)

## Présentation du projet

Ce projet consistait à développer un serveur MCP (*Model Context Protocol*) personnalisé permettant de connecter Claude Desktop à l’API du CRM Teamleader.

L’objectif était de permettre à un modèle de langage d’exécuter différentes opérations dans Teamleader à partir de demandes formulées en langage naturel.

Aucun MCP existant n’étant disponible pour Teamleader, l’intégration a été entièrement conçue et développée en Python.

Le serveur exposait plusieurs outils couvrant plusieurs domaines :

- les contacts
- les entreprises
- les produits
- les taux de TVA
- les opportunités commerciales / les devis et leurs lignes

---

## Contexte métier

La création et la modification de données dans Teamleader nécessitaient plusieurs manipulations manuelles.

Par exemple, pour créer un devis, il fallait généralement :

- rechercher ou créer un contact ou une entreprise
- créer une opportunité
- créer un devis associé
- ajouter les produits ou les lignes libres
- renseigner les quantités, prix et taux de TVA
- associer le client au devis
- modifier ou supprimer certaines lignes si nécessaire

Le projet avait donc pour objectif de simplifier ces opérations en permettant aux utilisateurs de formuler directement leur demande à Claude Desktop.

Exemple :

> « Crée un devis pour l’entreprise concernée avec une prestation de développement à 1 500 € et une prestation de maintenance à 300 €. »

Claude pouvait alors utiliser les outils MCP nécessaires pour effectuer les opérations dans Teamleader.

---

## Objectifs

Les objectifs du projet étaient de :

- simplifier l’utilisation du CRM via le langage naturel
- réduire les manipulations manuelles
- structurer une intégration réutilisable avec l’API Teamleader
- documenter les bonnes pratiques de création d’un serveur MCP
- mettre en place un déploiement automatisé dans le cloud

---

## Fonctionnalités couvertes

### Contacts

- lister et rechercher des contacts
- créer un contact
- modifier un contact

### Entreprises

- lister et rechercher des entreprises
- créer une entreprise
- modifier une entreprise
- lier un contact à une entreprise
- délier un contact d’une entreprise

### Produits

- lister et rechercher des produits
- créer un produit
- modifier un produit

### Taux de TVA

- lister les taux de TVA disponibles
- récupérer l’identifiant d’un taux de TVA

### Opportunités commerciales

- lister et rechercher des opportunités
- consulter les détails d’une opportunité
- créer une opportunité liée à un contact ou une entreprise

### Devis

- lister les devis
- consulter les détails d’un devis
- créer un devis
- modifier la devise ou la date d’expiration
- ajouter un produit à un devis
- ajouter une ligne libre
- modifier une ligne existante
- supprimer une ligne
- associer un contact ou une entreprise au devis

## Architecture technique

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

### Hébergement du serveur MCP

Le serveur MCP était conteneurisé avec Docker, puis hébergé sur Google Cloud Run.

Google Cloud Run a été choisi pour permettre un déploiement flexible et facilement maintenable, sans avoir à gérer directement l’infrastructure serveur.

### Versionnement et CI/CD

Le code source était versionné avec Git et GitLab. Le pipeline CI/CD permettait de :

1. détecter une modification sur le projet
2. construire une nouvelle image Docker
3. publier l’image sur Google Cloud
4. déployer la nouvelle version sur Google Cloud Run

## Etapes d'un worflow

Prenons l'exemple de la création d'un devis, voici les étapes qui vont suivre : 

```text
Indication de la demande de l'utilisateur à Claude Code
        │
        ▼
LLM Claude
│   ├── Rechercher ou créer le client
│   ├── Créer l’opportunité
│   ├── Créer le devis associé
│   ├── Modifier le devis en indiquant les divers informations (Taux de TVA, Contact/entreprise/Contenu du devis (ligne libre ou produit existant)
│   └── Récapitulatif du devis créé pour l'utilisateur
        │
        ▼
Validation par l'utilisateur du devis créé
```

Pour plus de détails sur le contenu du projet, je vous laisse vous rediriger vers les fichiers dans le dossier [docs/](https://github.com/stefanmenardp-commits/dev-creation-mcp-server-crm/tree/main/docs).

---

## Stack technique

| **Domaines** | **Technologies** |
|---|---|
| **Langage** | `Python` |
| **Protocole IA** | `Model Context Protocol` |
| **Client LLM** | `Claude Desktop` |
| **CRM** | `Teamleader` |
| **API** | `Teamleader API REST` |
| **Authentification** | `OAuth 2.0` |
| **Versionnement et CI/CD** | `Git/GitLab`, `GitLab CI/CD` |
| **Conteneurisation** | `Docker` |
| **Hébergement** | `Google Cloud Run` |
| **Configuration** | `.env`, `GCP Secret manager` |

---

## Compétences développées

Ce projet m'a permis de développer et de mettre en œuvre mes compétences dans les domaines suivants :

- autonomnie dans la gestion d'un projet
- analyse métier et recueil des besoins
- connaissance d'architecture d'un MCP
- développement en python
- utilisation d'API
- versionning et pipeline ci/cd
- conteneurisation
- hébergement Cloud
- documentation technique et fonctionnelle

Pour ce qui est des outils, j'ai développé des compétences dans ceux qui sont présents dans la partie stack technique.
