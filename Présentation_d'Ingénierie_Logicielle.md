# Internet des Émotions - Présentation d'Ingénierie Logicielle

> **Plateforme d'Analyse Émotionnelle Mondiale en Temps Réel**  
> Un système de microservices prêt pour la production pour suivre les tendances émotionnelles dans plus de 195 pays

**Présenté par**: [Votre Nom]  
**Date**: 16 décembre 2025  
**Version**: 2.0.0

---

## Table des Matières

1. [Résumé Exécutif](#1-résumé-exécutif)
2. [Énoncé du Problème](#2-énoncé-du-problème)
3. [Architecture de la Solution](#3-architecture-de-la-solution)
4. [Pile Technologique](#4-pile-technologique)
5. [Conception du Système](#5-conception-du-système)
6. [Pipeline de Données](#6-pipeline-de-données)
7. [Conception de l'API](#7-conception-de-lapi)
8. [Conception de la Base de Données](#8-conception-de-la-base-de-données)
9. [Intégration de l'Apprentissage Automatique](#9-intégration-de-lapprentissage-automatique)
10. [Évolutivité et Performance](#10-évolutivité-et-performance)
11. [Gestion des Erreurs et Résilience](#11-gestion-des-erreurs-et-résilience)
12. [Stratégie de Test](#12-stratégie-de-test)
13. [Déploiement et DevOps](#13-déploiement-et-devops)
14. [Surveillance et Observabilité](#14-surveillance-et-observabilité)
15. [Considérations de Sécurité](#15-considérations-de-sécurité)
16. [Défis et Solutions](#16-défis-et-solutions)
17. [Feuille de Route Future](#17-feuille-de-route-future)
18. [Métriques et Résultats](#18-métriques-et-résultats)

---

## 1. Résumé Exécutif

### Aperçu du Projet

**Internet des Émotions** est une plateforme d'analyse émotionnelle en temps réel qui surveille les états émotionnels collectifs dans plus de 195 pays en analysant les publications Reddit à l'aide de techniques avancées d'IA/ML.

### Métriques Clés

- **6 Microservices** fonctionnant dans un pipeline orchestré
- **Plus de 195 pays** surveillés mondialement
- **Cycles de pipeline de 30 secondes** pour des mises à jour en temps réel
- **Modèle ML de ~500 Mo** (transformateur RoBERTa)
- **7 catégories d'émotions** détectées avec 90% de précision
- **Traduction automatique** vers l'anglais depuis n'importe quelle langue
- **2 494 lignes** de code Python en production

### Valeur Commerciale

- **Suivi du Sentiment Mondial**: Comprendre les tendances émotionnelles mondiales
- **Insights en Temps Réel**: Surveiller les réactions aux actualités
- **Analyse Basée sur les Données**: Basée sur des discussions réelles sur les réseaux sociaux
- **Architecture Évolutive**: Conception en microservices pour une mise à l'échelle indépendante

---

### 📢 Notes de Présentation - Section 1

**[Durée: 2-3 minutes]**

"Bonjour à tous. Aujourd'hui, je vais vous présenter **Internet des Émotions**, un projet ambitieux qui combine intelligence artificielle, microservices, et analyse de données à l'échelle mondiale.

**[Montrer le titre]** Notre mission est simple mais puissante : comprendre comment le monde entier se sent, en temps réel, en analysant les conversations sur les réseaux sociaux.

**[Métriques clés]** Regardons les chiffres impressionnants : nous avons construit un système avec 6 microservices indépendants qui surveillent plus de 195 pays simultanément. Notre pipeline traite les données toutes les 30 secondes pour garantir une actualité maximale. Nous utilisons un modèle d'apprentissage profond de 500 mégaoctets capable de détecter 7 catégories d'émotions différentes avec une précision de 90%. Et le plus impressionnant ? Notre système traduit automatiquement du contenu depuis n'importe quelle langue vers l'anglais pour l'analyse.

**[Valeur commerciale]** Pourquoi est-ce important ? Imaginez pouvoir surveiller les réactions mondiales à un événement majeur en temps réel. Comprendre si un pays est majoritairement joyeux, anxieux ou en colère. C'est exactement ce que notre plateforme permet. Elle transforme des millions de discussions en insights actionnables.

Passons maintenant au problème que nous avons résolu..."

---

## 2. Énoncé du Problème

### Défi

Comment suivre et analyser l'état émotionnel collectif du monde entier en temps réel ?

### Exigences Techniques

1. **Couverture Mondiale**: Surveiller tous les 195+ pays de manière équitable
2. **Traitement en Temps Réel**: Latence inférieure à une minute de la collecte à la visualisation
3. **Barrières Linguistiques**: Gérer le contenu dans n'importe quelle langue
4. **Variété de Contenu**: Traiter le texte, les liens vers des articles, les images, les vidéos
5. **Évolutivité**: Gérer des volumes de données variables par pays
6. **Précision**: Classification émotionnelle de haute qualité
7. **Fiabilité**: Le système doit fonctionner en continu 24h/24 et 7j/7

### Contraintes

- **Limites de l'API Reddit**: Maximum 60 requêtes/minute
- **Budget Mémoire**: ~2 Go pour les modèles ML
- **Temps de Traitement**: Équilibrer précision et vitesse
- **Coût**: Minimiser les coûts d'infrastructure cloud

---

### 📢 Notes de Présentation - Section 2

**[Durée: 2 minutes]**

"Alors, quel était le défi exact à relever ?

**[Le défi principal]** La question fondamentale était : comment peut-on suivre et analyser l'état émotionnel collectif du monde entier en temps réel ? Ce n'est pas juste une question technique, c'est un défi à multiples facettes.

**[Exigences techniques]** Parlons des exigences. D'abord, la couverture mondiale : nous devions surveiller les 195+ pays de manière équitable, sans biais géographique. Ensuite, le traitement en temps réel : nous visions une latence inférieure à une minute entre la collecte des données et leur visualisation. 

**[Barrières linguistiques]** Un défi majeur était les barrières linguistiques. Les gens s'expriment dans des centaines de langues différentes. Nous devions gérer du contenu en chinois, arabe, espagnol, français, et bien d'autres.

**[Variété de contenu]** Les publications Reddit ne sont pas seulement du texte. Ce sont des liens vers des articles, des images, des vidéos. Notre système devait extraire le sens de tous ces types de contenu.

**[Contraintes réelles]** Et bien sûr, nous avions des contraintes réelles. L'API Reddit nous limite à 60 requêtes par minute. Nous avions un budget mémoire de seulement 2 Go pour nos modèles d'IA. Et nous devions équilibrer précision et vitesse tout en minimisant les coûts d'infrastructure.

Ces contraintes ont vraiment façonné notre approche technique. Voyons maintenant comment nous les avons surmontées avec notre architecture..."

---

## 3. Architecture de la Solution

### Architecture de Haut Niveau

```mermaid
graph TB
    subgraph Frontend
        UI[Next.js Frontend<br/>Port 3000]
    end
    
    subgraph "API Gateway Layer"
        GW[API Gateway<br/>Port 5000<br/>Orchestration & Routing]
    end
    
    subgraph "Microservices Layer"
        DF[Data Fetcher<br/>Port 5001<br/>Reddit API]
        CE[Content Extractor<br/>Port 5007<br/>Article + Translation]
        EE[Event Extractor<br/>Port 5004<br/>Clustering + Summarization]
        ML[ML Analyzer<br/>Port 5005<br/>RoBERTa Emotions]
        AG[Aggregator<br/>Port 5003<br/>Country Statistics]
    end
    
    subgraph "Data Layer"
        DB[(SQLite Database<br/>WAL Mode)]
    end
    
    subgraph "External Services"
        REDDIT[Reddit API]
        TRANS[Google Translate]
        SENT[Sentry]
    end
    
    UI -->|REST API| GW
    GW -->|Circuit Breaker| DF
    GW -->|Circuit Breaker| CE
    GW -->|Circuit Breaker| EE
    GW -->|Circuit Breaker| ML
    GW -->|Circuit Breaker| AG
    
    DF -->|Write Posts| DB
    DF -.->|Fetch Data| REDDIT
    CE -->|Update Posts| DB
    CE -.->|Extract & Translate| TRANS
    EE -->|Write Events| DB
    EE -->|Read Posts| DB
    ML -->|Update Events| DB
    ML -->|Read Events| DB
    AG -->|Write Aggregations| DB
    AG -->|Read Events| DB
    
    GW -.->|Error Tracking| SENT
    
    style GW fill:#4A90E2,stroke:#333,stroke-width:3px,color:#fff
    style DB fill:#E74C3C,stroke:#333,stroke-width:3px,color:#fff
    style ML fill:#9B59B6,stroke:#333,stroke-width:2px,color:#fff
    style UI fill:#2ECC71,stroke:#333,stroke-width:2px,color:#fff
```

### Principes de Conception

**Architecture Microservices**
- ✅ Responsabilité Unique : Chaque service a un seul rôle
- ✅ Déploiement Indépendant : Les services peuvent être mis à jour séparément
- ✅ Diversité Technologique : Meilleur outil pour chaque tâche
- ✅ Isolation des Défaillances : Les pannes ne se propagent pas en cascade

**Pipeline Piloté par Événements**
- ✅ Traitement Asynchrone : Opérations non bloquantes
- ✅ Traitement Étagé : Étapes claires de transformation des données
- ✅ Idempotence : Sûr pour réessayer les opérations

**Modèles de Résilience**
- ✅ Disjoncteurs : Prévenir les défaillances en cascade
- ✅ Logique de Nouvelle Tentative : Gérer les défaillances transitoires
- ✅ Dégradation Gracieuse : Mécanismes de repli

---

### 📢 Notes de Présentation - Section 3

**[Durée: 6-7 minutes]**

"Passons maintenant à l'architecture de notre solution. Ce diagramme est absolument crucial - c'est le blueprint complet de notre système. Prenons le temps de décortiquer chaque élément.

**[Structure générale du diagramme]** Regardez bien : nous avons 5 sous-graphes principaux. Pourquoi cette organisation ? Parce que ça représente les couches logiques de notre architecture : Frontend, API Gateway Layer, Microservices Layer, Data Layer, et External Services. C'est une architecture en couches classique qui facilite la compréhension et la maintenance.

**[Sous-graphe 1 : Frontend - Box verte]** En haut, la boîte verte 'Next.js Frontend Port 3000'. Pourquoi verte ? Pour indiquer que c'est le point d'entrée utilisateur, l'interface accessible. Pourquoi Next.js ? Parce que c'est un framework React moderne qui nous offre du Server-Side Rendering (SSR) et du Static Site Generation (SSG). Le port 3000 est la convention Next.js par défaut. Cette couche est responsable uniquement de l'affichage - elle ne fait aucun traitement de données.

**[Sous-graphe 2 : API Gateway Layer - Box bleue]** Juste en dessous, regardez cette boîte bleue : 'API Gateway Port 5000 Orchestration & Routing'. C'est coloré en bleu (#4A90E2) avec un stroke épais de 3px pour montrer son importance centrale. Pourquoi une Gateway ? Trois raisons critiques : 1) Point d'entrée unique pour tous les clients - simplifie la sécurité. 2) Orchestration : elle coordonne l'exécution séquentielle de tous les microservices dans le pipeline. 3) Routing : elle route les requêtes vers le bon microservice selon le endpoint appelé. Le port 5000 est choisi arbitrairement mais c'est une convention pour les API Flask.

**[Flèche 1 : UI vers GW]** Regardez la première connexion : une flèche pleine 'REST API' du Frontend vers la Gateway. Pourquoi REST ? Parce que c'est le standard web universel : stateless, basé sur HTTP, utilise JSON. C'est une flèche pleine car c'est une communication synchrone - le Frontend attend la réponse.

**[Sous-graphe 3 : Microservices Layer - 5 services]** Maintenant, le cœur de notre architecture. Vous voyez 5 boîtes de services. Pourquoi 5 services séparés au lieu d'une application monolithique ?

**Data Fetcher (Port 5001 - Reddit API)** : Responsabilité unique - récupérer les données de Reddit. Pourquoi séparé ? Parce que c'est le seul service qui parle à l'API Reddit. Si Reddit change son API, on ne modifie que ce service. Le port 5001 est le premier de notre plage.

**Content Extractor (Port 5007 - Article + Translation)** : Extrait et traduit le contenu. Pourquoi port 5007 et pas 5002 ? Bonne question ! Initialement on avait d'autres services, donc on a gardé ces numéros pour la compatibilité. Pourquoi ce service existe ? Parce que l'extraction HTML et la traduction sont des opérations lourdes qu'on veut isoler.

**Event Extractor (Port 5004 - Clustering + Summarization)** : Regroupe les publications similaires. Pourquoi séparé ? Parce que le clustering (DBSCAN) et le résumé (TF-IDF) sont des opérations CPU-intensives avec un algorithme complexe. Isolation permet le débogage facile.

**ML Analyzer (Port 5005 - RoBERTa Emotions)** : Coloré en violet (#9B59B6) ! Pourquoi ? Pour montrer que c'est le service d'apprentissage automatique - visuellement distinct. Pourquoi séparé ? Parce qu'il charge un modèle de 500MB en mémoire. Si on le redémarre, les autres services continuent de fonctionner.

**Aggregator (Port 5003 - Country Statistics)** : Calcule les statistiques finales. Pourquoi dernier ? Parce qu'il dépend de tous les autres - c'est l'étape finale.

**[Flèches : GW vers Microservices]** Vous voyez 5 flèches identiques de la Gateway vers chaque service, toutes étiquetées 'Circuit Breaker'. Qu'est-ce qu'un Circuit Breaker ? C'est un pattern de résilience : si un service échoue 5 fois, le disjoncteur 's'ouvre' et rejette immédiatement les requêtes futures pendant 60 secondes. Pourquoi ? Pour éviter de surcharger un service déjà en difficulté et prévenir les défaillances en cascade. C'est comme un disjoncteur électrique qui protège votre maison.

**[Sous-graphe 4 : Data Layer - Box rouge]** La base de données SQLite en mode WAL, colorée en rouge (#E74C3C) avec stroke épais de 3px. Pourquoi rouge ? Convention visuelle - rouge pour la persistance critique. Pourquoi SQLite ? Trois raisons : 1) Zéro configuration - un simple fichier. 2) Suffisant pour notre échelle (1000 publications/jour). 3) WAL Mode (Write-Ahead Logging) permet les lectures concurrentes pendant les écritures. Pourquoi pas PostgreSQL ou MySQL ? Sur-engineering pour notre cas. SQLite nous fait économiser complexité et coûts.

**[Flèches : Microservices vers DB]** Regardez les connexions à la base de données :
- **Data Fetcher → DB** : Flèche pleine 'Write Posts'. Pourquoi pleine ? Opération synchrone - on attend la confirmation d'écriture.
- **Content Extractor → DB** : 'Update Posts'. Pourquoi Update et pas Write ? Parce qu'il modifie des posts existants (ajoute le texte traduit).
- **Event Extractor** : DEUX flèches ! 'Read Posts' ET 'Write Events'. Pourquoi deux ? Parce qu'il lit les publications pour les analyser, puis écrit de nouveaux événements.
- **ML Analyzer** : Aussi deux flèches. 'Read Events' pour récupérer les événements non-analysés, puis 'Update Events' pour stocker les émotions détectées.
- **Aggregator** : 'Read Events' + 'Write Aggregations'. Lit les événements pour calculer les stats, puis écrit dans la table country_emotions.

**[Sous-graphe 5 : External Services]** Trois services externes :

**Reddit API** : La source de données. Flèche en pointillés 'Fetch Data' depuis Data Fetcher. Pourquoi pointillés ? Pour montrer que c'est une communication externe, hors de notre contrôle, potentiellement instable.

**Google Translate** : Flèche pointillée 'Extract & Translate' depuis Content Extractor. Externe, donc pointillés. Pourquoi Google Translate ? Parce qu'il supporte 100+ langues et a un tier gratuit.

**Sentry** : Flèche pointillée 'Error Tracking' depuis la Gateway. Pourquoi depuis la Gateway et pas tous les services ? Parce que la Gateway centralise les erreurs de tous les services. Sentry est notre système de monitoring en production - il nous alerte en temps réel des crashes.

**[Codes couleurs et styles]** 
- **Vert (#2ECC71)** : Frontend - point d'entrée utilisateur
- **Bleu (#4A90E2)** : Gateway - orchestrateur central
- **Violet (#9B59B6)** : ML - intelligence artificielle
- **Rouge (#E74C3C)** : Database - persistance critique
- **Flèches pleines** : Communication synchrone (attente de réponse)
- **Flèches pointillées** : Communication externe ou asynchrone
- **Stroke épais** : Composants critiques

**[Principes architecturaux - Pourquoi cette architecture ?]**

**1. Architecture Microservices** - Pourquoi ce choix ?
- **Responsabilité unique (Single Responsibility)** : Chaque service fait UNE chose. Si on change l'algorithme de clustering, on touche seulement Event Extractor.
- **Déploiement indépendant** : On peut redémarrer ML Analyzer sans toucher aux autres.
- **Scalabilité sélective** : Si ML Analyzer est lent, on peut juste lui ajouter plus de CPU, pas tout le système.
- **Isolation des défaillances** : Si Event Extractor crashe, Data Fetcher continue de collecter des données.
- **Diversité technologique** : On pourrait réécrire ML Analyzer en Go sans toucher aux autres services Python.

**2. Pipeline piloté par événements (Event-Driven)** - Pourquoi ?
- **Traitement asynchrone** : Le Frontend ne bloque pas pendant que le pipeline tourne. Il rafraîchit toutes les 30 secondes.
- **Traitement étagé (Staged)** : Données → Enrichissement → Clustering → ML → Agrégation. Chaque étape transforme clairement les données.
- **Idempotence** : Si on exécute deux fois 'Update Events' avec les mêmes données, le résultat est le même. Pourquoi crucial ? Pour les retries - on peut réessayer en toute sécurité.

**3. Modèles de résilience** - Pourquoi nécessaires ?
- **Circuit Breakers** : Prévient l'effet domino. Si ML Analyzer tombe, le disjoncteur s'ouvre et évite de surcharger le service avec des requêtes qui échoueront de toute façon.
- **Logique de retry (Nouvelle tentative)** : Avec backoff exponentiel - 4s, 8s, 10s. Pourquoi exponentiel ? Pour laisser le temps au service de se rétablir, sans le bombarder.
- **Dégradation gracieuse (Graceful Degradation)** : Si RoBERTa échoue, on bascule sur VADER. Si VADER échoue, on met 'neutral'. Le système continue de fonctionner à capacité réduite plutôt que de crasher complètement.

**[Trade-offs et alternatives considérées]**

Pourquoi pas une architecture monolithique ? Plus simple à déployer, mais :
- Impossible de scaler sélectivement
- Un bug crashe tout
- Déploiements risqués

Pourquoi pas une architecture serverless (Lambda) ? Moins cher potentiellement, mais :
- Cold starts de 10-15s pour charger RoBERTa
- Limite de 15 minutes d'exécution (notre pipeline prend 75s)
- Complexité de coordination

Pourquoi pas Kubernetes maintenant ? Over-engineering :
- Coût ($200+/mois vs $30/mois actuel)
- Complexité opérationnelle
- Notre échelle ne le justifie pas encore

Cette architecture trouve le sweet spot entre simplicité et robustesse pour notre échelle actuelle, tout en étant prête à évoluer vers Kubernetes quand nécessaire. Maintenant, voyons précisément quelles technologies alimentent ces services..."

---

## 4. Technology Stack

### Backend

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Language** | Python 3.9+ | Rich ML ecosystem, rapid development |
| **Framework** | Flask | Lightweight, perfect for microservices |
| **Database** | SQLite + WAL | Zero-config, sufficient for current scale |
| **ML Framework** | PyTorch + Transformers | Industry-standard for NLP |
| **HTTP Client** | Requests + Tenacity | Robust with retry logic |
| **Data Source** | PRAW (Reddit API) | Official Python Reddit wrapper |

### Machine Learning

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Emotion Detection** | RoBERTa (j-hartmann) | State-of-the-art transformer, 90% accuracy |
| **Sentiment Fallback** | VADER | Fast lexicon-based backup |
| **Clustering** | DBSCAN (scikit-learn) | Density-based event grouping |
| **Vectorization** | TF-IDF | Lightweight semantic similarity |
| **Translation** | Google Translator | Multi-language support |
| **Language Detection** | langdetect | Automatic language identification |

### Frontend

| Component | Technology | Justification |
|-----------|------------|---------------|
| **Framework** | Next.js 15 | Modern React with SSR/SSG |
| **Language** | TypeScript | Type safety, better DX |
| **Styling** | Tailwind CSS | Utility-first, fast development |
| **Maps** | Leaflet | Lightweight, customizable |
| **State** | React Hooks | Simple, no external state lib needed |

### DevOps & Monitoring

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Error Tracking** | Sentry | Production error monitoring |
| **Metrics** | Prometheus format | System health metrics |
| **Logging** | Python logging | Structured application logs |
| **Process Management** | Shell scripts | Simple start/stop automation |

---

### 📢 Notes de Présentation - Section 4

**[Durée: 2-3 minutes]**

"Parlons maintenant de notre pile technologique. Nous avons soigneusement sélectionné chaque technologie en fonction des besoins spécifiques.

**[Backend]** Pour le backend, nous utilisons Python 3.9+ comme langage principal. Pourquoi Python ? Parce qu'il possède l'écosystème d'apprentissage automatique le plus riche et permet un développement rapide. Flask est notre framework web - léger, parfait pour les microservices. Pour la base de données, SQLite avec le mode WAL nous offre une configuration zéro tout en étant suffisant pour notre échelle actuelle.

**[Machine Learning]** Côté apprentissage automatique, c'est là que ça devient vraiment puissant. Nous utilisons PyTorch et Transformers, le standard de l'industrie pour le traitement du langage naturel. Notre modèle principal est RoBERTa de j-hartmann, un transformateur de pointe avec 90% de précision. Pour le clustering, nous utilisons DBSCAN de scikit-learn, qui détecte automatiquement les groupes d'événements basés sur la densité. Et pour la traduction, Google Translator nous permet de gérer n'importe quelle langue.

**[Frontend]** Le frontend utilise Next.js 15, un framework React moderne avec rendu côté serveur. TypeScript nous donne la sécurité des types et une meilleure expérience développeur. Tailwind CSS permet un développement rapide avec son approche utility-first. Et Leaflet nous offre des cartes interactives légères et personnalisables.

**[DevOps]** Pour la surveillance et les opérations, nous utilisons Sentry pour le suivi des erreurs en production, des métriques au format Prometheus pour la santé du système, et de simples scripts shell pour la gestion des processus.

Chaque choix a été fait pour optimiser soit la performance, soit la maintenabilité, soit les deux. Voyons maintenant comment nous avons conçu chaque service individuellement..."

---

## 5. Conception du Système

### Répartition des Services

#### 1. Data Fetcher (:5001)
**Responsabilité**: Collecte de données Reddit

**Décisions de Conception Clés**:
- **Rotation Circulaire**: Distribution équitable entre tous les pays (30/lot)
- **Stratégie Intelligente**: Direct `.new()` pour les subreddits de pays, `.search()` pour les actualités
- **Limitation du Débit**: Délai de 0,5s entre les requêtes → éviter les erreurs 429
- **Récupération Parallèle**: ThreadPoolExecutor avec 10 workers
- **Classification des Publications**: texte | lien | image | vidéo | social

**Pourquoi cette Conception ?**
- Assure une couverture équitable (aucun biais de pays)
- Respecte les limites de l'API (essentiel pour la durabilité)
- Le traitement parallèle maximise le débit
- La classification permet le filtrage en aval

#### 2. Content Extractor (:5007)
**Responsabilité**: Extraction d'articles + traduction

**Décisions de Conception Clés**:
- **Analyse BeautifulSoup**: Extrait le contenu principal du HTML
- **Sélecteurs Intelligents**: Essaie `<article>`, `.post-content`, repli sur `<main>`
- **Traduction Par Morceaux**: Divise le texte long (max 4500 caractères/morceau)
- **Détection de Langue**: Automatique avec langdetect
- **Ignorer Réseaux Sociaux**: Twitter/Facebook nécessitent une connexion → ignorer

**Pourquoi cette Conception ?**
- Enrichit les publications de liens avec le texte complet de l'article
- Brise automatiquement les barrières linguistiques
- Le découpage prévient les limites de l'API
- Ignorer les réseaux sociaux économise des ressources

#### 3. Event Extractor (:5004)
**Responsabilité**: Clustering de publications + résumé

**Décisions de Conception Clés**:
- **Clustering DBSCAN**: Basé sur la densité, détecte automatiquement les clusters
  - eps=0.75 (seuil de similarité de 25%)
  - min_samples=2 (nécessite 2 publications minimum)
- **Vectorisation TF-IDF**: Similarité sémantique légère
- **Événements Individuels**: Les publications non groupées (-1) deviennent des événements
- **Résumé Extractif**: Notation TF-IDF des phrases
  - Max 2 phrases, 250 caractères
  - Notation position + contenu + longueur

**Pourquoi cette Conception ?**
- DBSCAN ne nécessite pas de nombre de clusters prédéfini
- Le seuil tolérant garantit le regroupement des sujets liés
- Les événements individuels préservent les actualités importantes autonomes
- L'extractif est rapide, aucun GPU nécessaire

#### 4. ML Analyzer (:5005)
**Responsabilité**: Classification des émotions

**Décisions de Conception Clés**:
- **Transformateur RoBERTa**: j-hartmann/emotion-english-distilroberta-base
  - 7 émotions: joie, tristesse, colère, peur, surprise, dégoût, neutre
  - Limite de 512 jetons
  - Inférence CPU (device=-1)
- **Secours VADER**: Si RoBERTa échoue
- **Traitement Par Lots**: 50 événements à la fois

**Pourquoi cette Conception ?**
- RoBERTa: précision de pointe (~90%)
- Le secours garantit la fiabilité
- Inférence CPU: coût réduit, latence acceptable
- La taille du lot équilibre mémoire et débit

#### 5. Aggregator (:5003)
**Responsabilité**: Statistiques au niveau des pays

**Décisions de Conception Clés**:
- **Moyenne des Émotions**: Somme des confiances / nombre d'événements
- **Comptage des Publications**: Total des publications entre les événements (pas le nombre d'événements)
- **Sujets Principaux**: Extraction de mots-clés des titres
- **Normalisation de Casse**: Minuscules pour la cohérence

**Pourquoi cette Conception ?**
- La moyenne reflète le sentiment global du pays
- Le nombre de publications montre le volume de discussion
- La normalisation de casse prévient les échecs de recherche

#### 6. API Gateway (:5000)
**Responsabilité**: Orchestration + routage

**Décisions de Conception Clés**:
- **Thread d'Arrière-plan**: Cycles de pipeline de 30 secondes
- **Disjoncteurs**: 5 échecs → 60s ouvert
- **Logique de Nouvelle Tentative**: Backoff exponentiel (4s → 10s)
- **Stratégie de Délai d'Attente**: 
  - Data Fetcher: 90s
  - Content Extractor: 120s (la traduction prend du temps)
  - Event Extractor: 120s (clustering + résumé)
  - ML Analyzer: 120s (inférence RoBERTa)
  - Aggregator: 60s

**Pourquoi cette Conception ?**
- Le traitement en arrière-plan libère le frontend de l'orchestration
- Les disjoncteurs préviennent les défaillances en cascade
- Les nouvelles tentatives gèrent les problèmes réseau transitoires
- Les délais d'attente ajustés aux temps de traitement réels

---

### 📢 Notes de Présentation - Section 5

**[Durée: 4-5 minutes]**

"Maintenant, plongeons dans la conception détaillée de chaque service. C'est vraiment le cœur technique du système.

**[Service 1 - Data Fetcher]** Commençons par le Data Fetcher sur le port 5001. Sa responsabilité est simple : récupérer les données Reddit. Mais comment fait-il ? Nous utilisons une rotation circulaire pour garantir que tous les pays sont traités équitablement - 30 pays par lot. Nous avons implémenté une limitation du débit avec un délai de 0,5 seconde entre les requêtes pour éviter les erreurs 429 de Reddit. Et grâce au ThreadPoolExecutor avec 10 workers, nous maximisons le débit en parallélisant les requêtes.

**[Service 2 - Content Extractor]** Ensuite, le Content Extractor sur le port 5007. Il extrait le contenu complet des articles et le traduit. Nous utilisons BeautifulSoup pour analyser le HTML et extraire le contenu principal. La détection de langue est automatique avec langdetect, et nous découpons les longs textes en morceaux de 4500 caractères maximum pour respecter les limites de l'API de traduction. Un point important : nous ignorons Twitter et Facebook qui nécessitent une connexion.

**[Service 3 - Event Extractor]** Le troisième service, l'Event Extractor, est vraiment intéressant. Il utilise DBSCAN, un algorithme de clustering basé sur la densité, pour regrouper automatiquement les publications similaires. Avec un seuil de 0,75, deux publications doivent avoir au moins 25% de similarité pour être groupées. Puis nous générons des résumés extractifs - maximum 2 phrases, 250 caractères. C'est rapide car ça ne nécessite pas de GPU.

**[Service 4 - ML Analyzer]** Le ML Analyzer sur le port 5005 est notre moteur d'intelligence artificielle. Il utilise RoBERTa, un transformateur de pointe capable de détecter 7 émotions différentes avec 90% de précision. Nous le faisons tourner sur CPU plutôt que GPU pour réduire les coûts, et nous traitons 50 événements à la fois pour optimiser le débit. Si RoBERTa échoue, nous avons VADER comme solution de secours.

**[Service 5 - Aggregator]** Enfin, l'Aggregator calcule les statistiques finales par pays. Il fait la moyenne des confiances émotionnelles, compte le nombre total de publications, et extrait les sujets principaux à partir des titres.

**[Service 6 - API Gateway]** Et tout cela est orchestré par l'API Gateway qui exécute le pipeline toutes les 30 secondes en arrière-plan, avec des disjoncteurs pour prévenir les défaillances en cascade et une logique de nouvelle tentative avec backoff exponentiel.

Ce design modulaire nous permet de faire évoluer, déboguer et améliorer chaque service indépendamment. Voyons maintenant comment ces services travaillent ensemble dans notre pipeline de données..."

---

## 6. Pipeline de Données

### Diagramme de Flux du Pipeline

```mermaid
flowchart TD
    Start([30-Second Cycle Trigger]) --> Cleanup[Daily Cleanup<br/>Delete posts > 28 days]
    Cleanup --> Fetch
    
    subgraph Stage1["Stage 1: Data Collection (90s)"]
        Fetch[Data Fetcher<br/>Circular Rotation: 30 countries] --> |Parallel 10 workers|Reddit[Reddit API<br/>0.5s rate limit]
        Reddit --> Classify[Classify Posts<br/>text/link/image/video/social]
        Classify --> Store1[(Store raw_posts<br/>needs_extraction=1)]
    end
    
    subgraph Stage2["Stage 2: Content Enrichment (120s)"]
        Store1 --> Extract[Content Extractor<br/>BeautifulSoup parsing]
        Extract --> Detect[Language Detection<br/>langdetect]
        Detect --> Translate{Is English?}
        Translate -->|No| Trans[Google Translate<br/>Chunked 4500 chars]
        Translate -->|Yes| Update1
        Trans --> Update1[(Update raw_posts.text<br/>needs_extraction=0)]
    end
    
    subgraph Stage3["Stage 3: Event Extraction (120s)"]
        Update1 --> Vector[TF-IDF Vectorization<br/>max_features=500]
        Vector --> Cluster[DBSCAN Clustering<br/>eps=0.75, min_samples=2]
        Cluster --> Groups{Cluster or<br/>Individual?}
        Groups -->|Cluster| GroupSum[Extractive Summary<br/>2 sentences, 250 chars]
        Groups -->|Individual| IndivSum[Generate Title<br/>First sentence]
        GroupSum --> Store2
        IndivSum --> Store2[(Create events<br/>is_analyzed=0)]
    end
    
    subgraph Stage4["Stage 4: Emotion Analysis (120s)"]
        Store2 --> RoBERTa[RoBERTa Model<br/>7 emotions classification]
        RoBERTa --> Top[Extract Top Emotion<br/>+ Confidence]
        Top --> Update2[(Update events<br/>is_analyzed=1)]
    end
    
    subgraph Stage5["Stage 5: Aggregation (60s)"]
        Update2 --> Group[Group by Country<br/>Calculate averages]
        Group --> Count[Count Posts<br/>Extract Topics]
        Count --> Store3[(Update country_emotions)]
    end
    
    Store3 --> Cache[Update API Cache]
    Cache --> End([Wait 30s])
    End --> Start
    
    style Start fill:#2ECC71,stroke:#333,stroke-width:2px,color:#fff
    style End fill:#2ECC71,stroke:#333,stroke-width:2px,color:#fff
    style RoBERTa fill:#9B59B6,stroke:#333,stroke-width:2px,color:#fff
    style Cluster fill:#E67E22,stroke:#333,stroke-width:2px,color:#fff
```

### Pipeline Stages Breakdown

```
Stage 1: Data Collection (90s timeout)
┌──────────────────────────────────────────────┐
│ Circular Rotation → Select 30 countries     │
│ Parallel fetch (10 workers) → Reddit API    │
│ Classify posts → Insert raw_posts           │
│ Set needs_extraction=1 for link posts       │
└──────────────────────────────────────────────┘
                    ▼
Stage 2: Content Enrichment (120s timeout)
┌──────────────────────────────────────────────┐
│ Find posts with needs_extraction=1          │
│ Extract article content (BeautifulSoup)     │
│ Detect language → Translate to English      │
│ Update text field → Set needs_extraction=0  │
└──────────────────────────────────────────────┘
                    ▼
Stage 3: Event Extraction (120s timeout)
┌──────────────────────────────────────────────┐
│ Get posts from last 7 days (needs_extraction=0) │
│ TF-IDF vectorization → Cosine similarity    │
│ DBSCAN clustering (eps=0.75, min_samples=2) │
│ Generate extractive summaries (2 sent, 250c)│
│ Insert events → Set is_analyzed=0           │
└──────────────────────────────────────────────┘
                    ▼
Stage 4: Emotion Analysis (120s timeout)
┌──────────────────────────────────────────────┐
│ Find events with is_analyzed=0              │
│ RoBERTa classification (7 emotions)         │
│ Extract top emotion + confidence            │
│ Update events → Set is_analyzed=1           │
└──────────────────────────────────────────────┘
                    ▼
Stage 5: Aggregation (60s timeout)
┌──────────────────────────────────────────────┐
│ Group events by country                     │
│ Average emotion confidences                 │
│ Count total posts (from post_ids)           │
│ Insert/update country_emotions              │
└──────────────────────────────────────────────┘
                    ▼
Stage 6: Frontend Display
┌──────────────────────────────────────────────┐
│ GET /api/emotions → Fetch all countries     │
│ Render interactive map with emotion colors  │
│ Auto-refresh every 30 seconds               │
└──────────────────────────────────────────────┘
```

### Caractéristiques de Performance

| Étape | Durée | Goulot d'étranglement | Optimisation |
|-------|----------|------------|--------------|
| Collecte de Données | ~15-30s | Limites de débit de l'API Reddit | Workers parallèles, limitation du débit |
| Extraction de Contenu | ~20-40s | I/O réseau, traduction | Requêtes asynchrones, découpage |
| Extraction d'Événements | ~5-10s | Vectorisation TF-IDF | Limiter les fonctionnalités à 500 |
| Analyse des Émotions | ~10-20s | Inférence RoBERTa | Traitement par lots, inférence CPU |
| Agrégation | ~2-5s | Requêtes de base de données | Indexation sur country, is_analyzed |

**Durée Totale du Pipeline**: ~52-105 secondes (moy ~75s)  
**Fréquence du Pipeline**: Toutes les 30 secondes (chevauchement autorisé)

---

### 📢 Notes de Présentation - Section 6

**[Durée: 5-6 minutes]**

"Voyons maintenant comment toutes les pièces s'assemblent dans notre pipeline de données. C'est le flux complet, de la collecte à la visualisation. Regardons ce diagramme en détail.

**[Point de départ - Cycle de 30 secondes]** Tout commence avec un déclencheur automatique toutes les 30 secondes, représenté en vert sur le diagramme. C'est le rythme cardiaque de notre système. Avant de commencer le traitement, nous effectuons un nettoyage quotidien : nous supprimons toutes les publications de plus de 28 jours pour maintenir la base de données propre et performante.

**[Étape 1 - Collecte de Données - 90 secondes maximum]** Vous voyez ici la première boîte bleue : Data Collection. Le Data Fetcher utilise une rotation circulaire pour sélectionner 30 pays à chaque cycle - cela garantit l'équité. Ensuite, regardez cette flèche 'Parallel 10 workers' : nous utilisons 10 threads parallèles pour maximiser le débit. Chaque requête vers l'API Reddit respecte une limite de débit de 0,5 seconde - c'est crucial pour éviter les erreurs 429. Les publications sont ensuite classifiées en 5 catégories : texte, lien, image, vidéo, ou social. Finalement, tout est stocké dans la table raw_posts avec le flag needs_extraction=1 pour les liens qui nécessitent une extraction de contenu.

**[Étape 2 - Enrichissement du Contenu - 120 secondes maximum]** La deuxième boîte représente l'enrichissement. Vous voyez que nous utilisons BeautifulSoup pour l'extraction - c'est une bibliothèque Python qui analyse le HTML et extrait le contenu principal des articles. Puis vient la détection de langue avec langdetect. Regardez ce losange de décision : 'Is English?' Si oui, on passe directement à la mise à jour. Si non, on utilise Google Translate avec un découpage en morceaux de 4500 caractères maximum - c'est pour respecter les limites de l'API. À la fin, nous mettons à jour le champ texte dans raw_posts et changeons needs_extraction à 0.

**[Étape 3 - Extraction d'Événements - 120 secondes maximum]** Troisième étape, colorée en orange pour le clustering. D'abord, la vectorisation TF-IDF avec un maximum de 500 features - c'est un compromis entre précision et performance. Ensuite, DBSCAN avec epsilon=0,75 et minimum 2 samples - ces paramètres signifient que deux publications doivent avoir au moins 25% de similarité cosinus pour être groupées, et il faut au moins 2 publications pour former un cluster. Regardez cette décision : 'Cluster or Individual?' Si c'est un cluster, nous générons un résumé extractif de 2 phrases maximum, 250 caractères. Si c'est individuel, nous générons simplement un titre à partir de la première phrase. Dans les deux cas, nous créons des événements dans la table events avec is_analyzed=0.

**[Étape 4 - Analyse Émotionnelle - 120 secondes maximum]** Quatrième étape, en violet, c'est notre modèle RoBERTa. Ce transformateur de 500 mégaoctets analyse chaque événement et produit des probabilités pour 7 émotions : joie, tristesse, colère, peur, surprise, dégoût, et neutre. Nous extrayons l'émotion dominante - celle avec la plus haute probabilité - ainsi que son score de confiance. Puis nous mettons à jour la table events en changeant is_analyzed à 1 pour marquer que c'est terminé.

**[Étape 5 - Agrégation - 60 secondes maximum]** Cinquième étape : l'agrégation par pays. Nous groupons tous les événements d'un même pays, calculons les moyennes des scores émotionnels pour obtenir le profil émotionnel global du pays, comptons le nombre total de publications, et extrayons les sujets principaux à partir des titres. Tout cela est inséré ou mis à jour dans la table country_emotions.

**[Étape 6 - Mise en Cache et Boucle]** Après l'agrégation, nous mettons à jour le cache de l'API avec les nouvelles données. Puis le système attend 30 secondes avant de recommencer le cycle complet. Cette boucle continue indéfiniment, garantissant que nos données sont toujours fraîches.

**[Performance globale et parallélisme]** Vous remarquerez que chaque étape a un timeout différent : 90s, 120s, 120s, 120s, 60s. Au total, le pipeline complet peut prendre entre 52 et 105 secondes, avec une moyenne de 75 secondes. Maintenant, voici un point important : comme nous lançons un nouveau cycle toutes les 30 secondes, plusieurs pipelines peuvent s'exécuter en parallèle. Par exemple, pendant qu'un pipeline est à l'étape 3, un autre peut démarrer à l'étape 1. C'est parfaitement acceptable et c'est pour cela que nous avons des timeouts généreux.

**[Points de stockage]** Notez les symboles de base de données sur le diagramme : Store raw_posts, Update raw_posts.text, Create events, Update events, Update country_emotions. Chaque étape persiste ses résultats immédiatement, ce qui rend le système résilient. Si une étape échoue, les données des étapes précédentes sont déjà sauvegardées.

**[Visualisation des couleurs]** Les couleurs du diagramme ne sont pas décoratives : vert pour le début et la fin du cycle, bleu pour la collecte, pas de couleur spéciale pour l'enrichissement, orange pour le clustering (DBSCAN), et violet pour l'apprentissage automatique (RoBERTa). Cela aide à visualiser rapidement où se trouve chaque type de traitement.

Ce flux orchestré garantit que nos données sont toujours fraîches, que chaque étape est optimisée, et que le système peut se remettre gracieusement des erreurs. Parlons maintenant de notre conception d'API et comment le frontend consomme ces données..."

---

## 7. Conception de l'API

### Diagramme de Séquence des Requêtes API

```mermaid
sequenceDiagram
    participant User as Utilisateur Frontend
    participant UI as Frontend Next.js
    participant GW as Passerelle API
    participant CB as Disjoncteur
    participant MS as Microservices
    participant DB as Base de Données SQLite
    participant Cache as Cache de Réponse
    
    User->>UI: Ouvrir le Tableau de Bord
    UI->>GW: GET /api/emotions
    
    GW->>Cache: Vérifier le Cache (TTL: 30s)
    alt Cache Trouvé
        Cache-->>GW: Retourner les Données en Cache
        GW-->>UI: 200 OK + JSON
    else Cache Manquant
        GW->>CB: Vérifier l'État du Circuit
        alt Circuit Fermé (Sain)
            CB->>MS: Router la Requête
            MS->>DB: SELECT * FROM country_emotions
            DB-->>MS: Retourner les Lignes
            MS-->>CB: Réponse JSON
            CB-->>GW: Succès
            GW->>Cache: Stocker la Réponse (TTL 30s)
            GW-->>UI: 200 OK + JSON
        else Circuit Ouvert (En Panne)
            CB-->>GW: Échec Rapide
            GW-->>UI: 503 Service Indisponible
        end
    end
    
    UI->>UI: Afficher la Carte + Couleurs des Émotions
    UI-->>User: Afficher la Carte Interactive
    
    Note over User,DB: L'utilisateur clique sur la France
    
    User->>UI: Cliquer sur France
    UI->>GW: GET /api/country/france
    GW->>CB: Vérifier le Circuit
    CB->>MS: Service Agrégateur
    MS->>DB: SELECT * FROM events WHERE country='france'
    DB-->>MS: Événements + Publications
    MS-->>GW: JSON Détaillé
    GW-->>UI: 200 OK
    UI-->>User: Afficher le Panneau de Détails du Pays
    
    Note over GW,DB: Pipeline en Arrière-plan (Toutes les 30s)
    
    loop Toutes les 30 secondes
        GW->>MS: Déclencher les Étapes du Pipeline
        MS->>DB: Écrire les Nouvelles Données
        DB-->>MS: Confirmer
        MS-->>GW: Pipeline Terminé
        GW->>Cache: Invalider le Cache
    end
```

### Principes RESTful

✅ **URLs Orientées Ressources**: `/api/emotions`, `/api/country/{name}`  
✅ **Verbes HTTP**: GET pour les lectures, POST pour les actions  
✅ **Réponses JSON**: Format cohérent sur tous les endpoints  
✅ **Codes de Statut**: 200 OK, 404 Not Found, 500 Internal Error  
✅ **CORS Activé**: Requêtes cross-origin supportées

### Endpoints de l'API

#### Santé et Surveillance

```http
GET /health
```
**Réponse**:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "timestamp": "2025-12-16T10:30:00"
}
```

```http
GET /api/health
```
**Réponse**:

```json
{
  "status": "healthy",
  "services": {
    "data-fetcher": "healthy",
    "content-extractor": "healthy",
    "event-extractor": "healthy",
    "ml-analyzer": "healthy",
    "aggregator": "healthy"
  },
  "db_posts": 1234,
  "timestamp": "2025-12-16T10:30:00"
}
```

#### Récupération de Données

```http
GET /api/emotions
```
**Objectif**: Obtenir les données émotionnelles pour tous les pays  
**Réponse**:
```json
{
  "emotions": {
    "france": {
      "emotions": {
        "joy": 0.35,
        "sadness": 0.25,
        "anger": 0.20,
        "fear": 0.10,
        "surprise": 0.05,
        "disgust": 0.03,
        "neutral": 0.02
      },
      "top_emotion": "joy",
      "confidence": 0.78,
      "post_count": 45,
      "event_count": 12,
      "top_topics": ["climate", "economy", "politics"]
    }
  }
}
```

```http
GET /api/country/<country_name>
```
**Objectif**: Obtenir les données détaillées pour un pays spécifique  
**Exemple**: `GET /api/country/france`  
**Réponse**:
```json
{
  "country": "france",
  "emotions": {...},
  "events": [
    {
      "id": 1,
      "title": "French government announces climate policy",
      "description": "Parliament passes new environmental legislation targeting carbon emissions.",
      "post_count": 8,
      "top_emotion": "hope",
      "confidence": 0.82,
      "event_date": "2025-12-16T10:30:00"
    }
  ],
  "posts": [...],
  "top_topics": ["climate", "policy", "environment"]
}
```

#### Opérations Manuelles

```http
POST /api/fetch
Content-Type: application/json

{
  "countries": ["france", "germany"],
  "limit": 50
}
```
**Objectif**: Déclencher manuellement la récupération de données  
**Cas d'Usage**: Tests, remplissage rétroactif des données

```http
POST /api/trigger_pipeline
```
**Objectif**: Déclencher manuellement le pipeline complet  
**Cas d'Usage**: Forcer le traitement immédiat

---

### 📢 Notes de Présentation - Section 7

**[Durée: 3 minutes]**

"Parlons maintenant de notre conception d'API, qui est l'interface entre notre backend et le frontend.

**[Montrer le diagramme de séquence]** Ce diagramme montre comment une requête utilisateur traverse notre système. Quand un utilisateur ouvre le tableau de bord, le frontend Next.js fait une requête GET /api/emotions vers l'API Gateway.

**[Mécanisme de cache]** Première optimisation : nous vérifions le cache avec un TTL de 30 secondes. Si les données sont fraîches, on retourne immédiatement. Sinon, on interroge les microservices.

**[Disjoncteurs]** Avant de router la requête, nous vérifions l'état du disjoncteur. Si le service est sain, on continue. S'il est en panne, on fait un échec rapide plutôt que d'attendre un timeout. C'est un pattern de résilience crucial.

**[Principes RESTful]** Notre API suit les principes RESTful : URLs orientées ressources, verbes HTTP appropriés, réponses JSON cohérentes, et codes de statut HTTP standard. Le CORS est activé pour permettre les requêtes cross-origin.

**[Endpoints principaux]** Nous avons trois types d'endpoints :
1. **Santé** : /health et /api/health pour monitorer le système
2. **Récupération** : /api/emotions pour tous les pays, et /api/country/{name} pour un pays spécifique
3. **Opérations manuelles** : /api/fetch et /api/trigger_pipeline pour les tests et le débogage

**[Exemple de réponse]** Les réponses sont structurées avec les émotions, les scores de confiance, le nombre de publications, et les sujets principaux. Tout est en JSON pour une consommation facile par le frontend.

Cette API simple mais robuste permet une intégration facile et une expérience utilisateur fluide. Maintenant, voyons comment nous stockons toutes ces données..."

---

## 8. Conception de la Base de Données

### Diagramme Entité-Relation

```mermaid
erDiagram
    RAW_POSTS ||--o{ EVENTS : "regroupés_en"
    EVENTS ||--o{ COUNTRY_EMOTIONS : "agrégés_vers"
    
    RAW_POSTS {
        TEXT id PK "ID de publication Reddit"
        TEXT text "Contenu traduit"
        TEXT country "Pays associé"
        TEXT timestamp "ISO 8601"
        TEXT source "Domaine"
        TEXT url "URL Reddit"
        TEXT author "Nom d'utilisateur"
        INTEGER score "Votes positifs"
        TEXT post_type "text/link/image/video/social"
        TEXT media_url "URL image/vidéo"
        TEXT link_url "Article externe"
        INTEGER needs_extraction "0 ou 1"
        INTEGER content_extracted "0 ou 1"
        TEXT created_at
    }
    
    EVENTS {
        INTEGER id PK "Auto-incrément"
        TEXT country FK "Nom du pays"
        TEXT title "Max 200 caractères"
        TEXT description "Résumé IA 250c"
        TEXT post_ids "Tableau JSON"
        TEXT event_date "Publication la plus récente"
        INTEGER post_count "Publications dans l'événement"
        TEXT emotion "joy/sadness/anger/fear/surprise/disgust/neutral"
        REAL confidence "0.0-1.0"
        INTEGER is_analyzed "0 ou 1"
        TEXT created_at
    }
    
    COUNTRY_EMOTIONS {
        TEXT country PK "Nom en minuscules"
        TEXT emotions "Scores émotionnels JSON"
        TEXT top_emotion "Émotion dominante"
        REAL confidence "Score de l'émotion principale"
        INTEGER total_posts "Somme entre événements"
        INTEGER event_count "Nombre d'événements"
        TEXT top_topics "Tableau JSON"
        TEXT last_updated "ISO 8601"
    }
```

### Principes de Conception du Schéma

✅ **Dénormalisation**: Optimiser pour la performance en lecture  
✅ **Stockage JSON**: Flexible pour les données imbriquées (emotions, post_ids)  
✅ **Index**: Sur les champs fréquemment interrogés (country, is_analyzed)  
✅ **Horodatages**: Suivre la création et les mises à jour  
✅ **SQLite + WAL**: Garanties ACID, lectures concurrentes

### Table: `raw_posts`

**Objectif**: Stocker les publications Reddit originales

```sql
CREATE TABLE raw_posts (
  id TEXT PRIMARY KEY,              -- ID de publication Reddit (unique)
  text TEXT,                        -- Contenu de la publication (traduit en anglais)
  country TEXT,                     -- Pays associé
  timestamp TEXT,                   -- Heure de publication Reddit (ISO 8601)
  source TEXT,                      -- Domaine (ex: 'bbc.com')
  url TEXT,                         -- URL Reddit complète
  author TEXT,                      -- Nom d'utilisateur Reddit
  score INTEGER,                    -- Votes positifs
  post_type TEXT,                   -- 'text' | 'link' | 'image' | 'video' | 'social'
  media_url TEXT,                   -- URL image/vidéo
  link_url TEXT,                    -- URL de l'article externe
  needs_extraction INTEGER,         -- 1 = nécessite l'extraction de contenu
  content_extracted INTEGER,        -- 1 = extraction terminée
  extracted_content TEXT,           -- Texte complet de l'article (déprécié)
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_country ON raw_posts(country);
CREATE INDEX idx_needs_extraction ON raw_posts(needs_extraction);
CREATE INDEX idx_timestamp ON raw_posts(timestamp);
```

**Justification des Index**:
- `country`: Filtrage rapide pour l'extraction d'événements
- `needs_extraction`: Trouver rapidement les publications en attente
- `timestamp`: Filtrer par récence (fenêtre de 7 jours)

### Table: `events`

**Objectif**: Stocker les événements regroupés avec résumés

```sql
CREATE TABLE events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  country TEXT,                     -- Nom du pays
  title TEXT,                       -- Titre de l'événement (max 200 caractères)
  description TEXT,                 -- Résumé IA (250 caractères, 2 phrases)
  post_ids TEXT,                    -- Tableau JSON: ["abc123", "def456"]
  event_date TEXT,                  -- Horodatage de la publication la plus récente
  post_count INTEGER,               -- Nombre de publications dans l'événement
  emotion TEXT,                     -- Émotion principale de RoBERTa
  confidence REAL,                  -- Confiance de l'émotion (0-1)
  is_analyzed INTEGER DEFAULT 0,   -- 0 = en attente, 1 = analysé
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_country_events ON events(country);
CREATE INDEX idx_is_analyzed ON events(is_analyzed);
CREATE INDEX idx_event_date ON events(event_date);
```

**Notes de Conception**:
- `post_ids` en JSON: Flexible, facile à étendre
- Indicateur `is_analyzed`: Suit la progression du pipeline
- Les horodatages permettent le filtrage temporel

### Table: `country_emotions`

**Objectif**: Données agrégées au niveau des pays

```sql
CREATE TABLE country_emotions (
  country TEXT PRIMARY KEY,         -- Nom du pays (minuscules)
  emotions TEXT,                    -- JSON: {"joy": 0.35, "sadness": 0.25, ...}
  top_emotion TEXT,                 -- Émotion dominante
  confidence REAL,                  -- Confiance de l'émotion principale
  total_posts INTEGER,              -- Somme des publications de tous les événements
  event_count INTEGER,              -- Nombre d'événements
  top_topics TEXT,                  -- JSON: ["climate", "economy"]
  last_updated TEXT                 -- Heure de la dernière agrégation
);
```

**Compromis de Normalisation**:
- Pourrait normaliser les émotions dans une table séparée
- Choix du JSON pour des requêtes plus simples et une consommation frontend facile
- La charge de travail orientée lecture bénéficie de la dénormalisation

---

### 📢 Notes de Présentation - Section 8

**[Durée: 5-6 minutes]**

"La base de données est le cœur battant de notre système - toutes les données y transitent et y sont persistées. Ce diagramme Entité-Relation (ER) est crucial. Analysons-le en détail.

**[Structure du diagramme ER]** Regardez : nous avons trois tables principales représentées comme des rectangles. Les lignes entre elles montrent les relations. C'est un diagramme ER de type 'crow's foot notation' - les symboles aux extrémités des lignes indiquent la cardinalité.

**[Relation 1 : RAW_POSTS vers EVENTS]** Voyez cette ligne : RAW_POSTS ||--o{ EVENTS avec le label 'regroupés_en'. Décortiquons ce symbole :
- **||** (côté RAW_POSTS) : Une et une seule publication
- **--o{** (côté EVENTS) : Zéro ou plusieurs événements
- **Signification** : Une publication RAW_POST peut être regroupée dans zéro, un, ou plusieurs événements. Pourquoi zéro ? Parce qu'une publication pourrait être trop ancienne (>7 jours) et non incluse dans les événements actuels. Pourquoi plusieurs ? Théoriquement possible mais rare - une publication très pertinente pourrait matcher plusieurs clusters.

**[Relation 2 : EVENTS vers COUNTRY_EMOTIONS]** EVENTS ||--o{ COUNTRY_EMOTIONS 'agrégés_vers'. 
- **||** (côté EVENTS) : Un événement appartient à un seul pays
- **--o{** (côté COUNTRY_EMOTIONS) : Un pays a zéro ou plusieurs événements
- **Signification** : Tous les événements d'un pays sont agrégés dans une seule ligne country_emotions. Pourquoi un seul pays par événement ? Parce qu'un événement est toujours lié à un pays spécifique (ex: France, USA).

**[TABLE 1 : RAW_POSTS - La source de vérité]**

**Champ id (TEXT PRIMARY KEY)** : Pourquoi TEXT et pas INTEGER ? Parce que Reddit utilise des IDs alphanumériques comme 't3_abc123'. PRIMARY KEY garantit l'unicité - pas de doublons. Pourquoi crucial ? Pour l'idempotence - si on récupère la même publication deux fois, elle ne sera pas insérée en double.

**Champ text (TEXT)** : Le contenu de la publication. Pourquoi traduit en anglais ? Parce que notre modèle RoBERTa ne comprend que l'anglais. Ce champ peut contenir plusieurs kilobytes de texte - d'où le type TEXT et pas VARCHAR(255).

**Champ country (TEXT)** : Le pays associé. Pourquoi TEXT ? Parce qu'on stocke le nom complet 'france', 'united states', pas un code. Alternative considérée : table countries séparée avec foreign key. Rejeté car : over-normalization pour notre cas. On a seulement 195 pays, la duplication de string est négligeable.

**Champ timestamp (TEXT)** : Format ISO 8601 (ex: '2025-12-16T10:30:00Z'). Pourquoi TEXT et pas DATETIME ? Parce que SQLite n'a pas de type DATETIME natif - il stocke tout comme TEXT, INTEGER, ou REAL. TEXT avec ISO 8601 est la recommandation officielle SQLite pour les dates.

**Champ source (TEXT)** : Le domaine (ex: 'bbc.com', 'cnn.com'). Pourquoi stocker ça ? Pour filtrer les sources fiables vs non-fiables. Pour les analytics - quelles sources génèrent le plus de contenu émotionnel.

**Champ url (TEXT)** : L'URL Reddit complète. Pourquoi ? Pour traçabilité - on peut revenir à la source originale. Pour debugging - vérifier si notre extraction est correcte.

**Champ author (TEXT)** : Nom d'utilisateur Reddit. Pourquoi anonyme ? Reddit est public, pas de problème de confidentialité. Pourquoi utile ? Pour détecter les bots (un compte qui poste 100x/jour).

**Champ score (INTEGER)** : Les upvotes Reddit. Pourquoi stocker ? Pour pondérer - une publication avec 10,000 upvotes a plus d'impact qu'une avec 5. Pas encore implémenté mais prévu.

**Champ post_type (TEXT)** : 'text' | 'link' | 'image' | 'video' | 'social'. Pourquoi cette classification ?
- **text** : Publication Reddit directe - texte déjà disponible
- **link** : Article externe - nécessite extraction de contenu
- **image** : Nécessiterait OCR (pas implémenté)
- **video** : Nécessiterait transcription (pas implémenté)
- **social** : Twitter/Facebook - nécessite authentification (ignoré)

Cette classification pilote le workflow : seuls les 'link' vont au Content Extractor.

**Champ media_url (TEXT)** : URL de l'image ou vidéo. Pourquoi stocker si on ne traite pas ? Pour feature future - quand on ajoutera l'analyse d'images.

**Champ link_url (TEXT)** : URL de l'article externe. Pourquoi séparé de 'url' ? Parce que 'url' pointe vers Reddit, 'link_url' vers l'article original.

**Champ needs_extraction (INTEGER)** : Flag booléen (0 ou 1). Pourquoi INTEGER et pas BOOLEAN ? SQLite n'a pas de type BOOLEAN - convention d'utiliser INTEGER. Pourquoi ce flag ? Pour marquer les publications qui nécessitent extraction de contenu. Le Content Extractor query WHERE needs_extraction=1.

**Champ content_extracted (INTEGER)** : Flag de progression. Pourquoi deux flags (needs_extraction ET content_extracted) ? Pour distinguer :
- needs_extraction=0, content_extracted=0 : Publication texte, rien à faire
- needs_extraction=1, content_extracted=0 : En attente d'extraction
- needs_extraction=1, content_extracted=1 : Extraction terminée

**Champ created_at (TEXT DEFAULT CURRENT_TIMESTAMP)** : Horodatage d'insertion. Pourquoi ? Pour debugging (quand cette publication est-elle entrée dans notre système ?). Pour cleanup - supprimer les publications >28 jours.

**[Index de la table RAW_POSTS]** Trois index - pourquoi ces trois spécifiquement ?

**INDEX idx_country ON raw_posts(country)** : Pourquoi ? Parce que Event Extractor fait SELECT * FROM raw_posts WHERE country='france'. Sans index, SQLite scanne toute la table (table scan) - lent. Avec l'index, lookup direct - rapide. Trade-off : l'index consomme de l'espace disque et ralentit les INSERT. Mais nos lectures >> écritures, donc ça vaut le coup.

**INDEX idx_needs_extraction ON raw_posts(needs_extraction)** : Pour Content Extractor qui query WHERE needs_extraction=1. Pourquoi important ? Parce que 80% des publications ont needs_extraction=0, l'index permet de skip rapidement vers les 20% qui nécessitent extraction.

**INDEX idx_timestamp ON raw_posts(timestamp)** : Pour Event Extractor qui query WHERE timestamp > (maintenant - 7 jours). Pourquoi 7 jours ? Fenêtre glissante - on ne clustering que les publications récentes. Index permet de filtrer rapidement par date.

**[TABLE 2 : EVENTS - Les événements agrégés]**

**Champ id (INTEGER PRIMARY KEY AUTOINCREMENT)** : ID auto-généré. Pourquoi AUTOINCREMENT ? Parce qu'on n'a pas d'ID naturel pour un événement. SQLite génère automatiquement 1, 2, 3, ...

**Champ country (TEXT)** : Le pays. Pourquoi répété ? Dénormalisation délibérée - on aurait pu faire une foreign key vers une table countries, mais c'est over-engineering. Avec 195 pays, la duplication de string est négligeable.

**Champ title (TEXT)** : Max 200 caractères. Pourquoi limité ? Pour l'affichage UI - trop long casse la mise en page. Comment généré ? Pour les clusters : première phrase de la publication la plus upvotée. Pour les événements individuels : titre de la publication.

**Champ description (TEXT)** : Résumé IA de 250 caractères, 2 phrases. Pourquoi 250c ? Trade-off : assez long pour être informatif, assez court pour un affichage rapide. Pourquoi 2 phrases ? Tests montrent qu'1 phrase est trop vague, 3+ phrases sont trop longues.

**Champ post_ids (TEXT)** : Tableau JSON : ["abc123", "def456"]. Pourquoi JSON ? Pour flexibilité - un événement peut avoir 1 à 50 publications. Pourquoi pas une table de jointure events_posts ? Parce qu'on ne query jamais dans l'autre sens (publications → événements). Le JSON est plus simple et suffisant.

**Champ event_date (TEXT)** : Horodatage de la publication la plus récente dans l'événement. Pourquoi la plus récente ? Pour trier les événements - afficher les plus récents en premier.

**Champ post_count (INTEGER)** : Nombre de publications dans l'événement. Pourquoi stocker alors qu'on a post_ids ? Pour performance - COUNT(post_ids) nécessite de parser le JSON. Avec post_count, lookup direct.

**Champ emotion (TEXT)** : 'joy', 'sadness', 'anger', 'fear', 'surprise', 'disgust', 'neutral'. Pourquoi TEXT et pas ENUM ? SQLite n'a pas de type ENUM. Pourquoi ces 7 exactement ? C'est le modèle de Paul Ekman sur les émotions universelles, que notre modèle RoBERTa utilise.

**Champ confidence (REAL)** : Score 0.0-1.0. Pourquoi REAL ? Pour les nombres décimaux (floating point). Ex: 0.87 = 87% de confiance que l'émotion détectée est correcte.

**Champ is_analyzed (INTEGER DEFAULT 0)** : Flag de progression. 0 = en attente d'analyse ML, 1 = analysé. Pourquoi ce flag ? Pour que ML Analyzer query WHERE is_analyzed=0 et ne traite que les événements non-analysés. Sans ce flag, on ré-analyserait tout à chaque cycle - gaspillage de CPU.

**[Index de la table EVENTS]**

**INDEX idx_country_events ON events(country)** : Pour Aggregator qui fait SELECT * FROM events WHERE country='france' GROUP BY country.

**INDEX idx_is_analyzed ON events(is_analyzed)** : Pour ML Analyzer : SELECT * FROM events WHERE is_analyzed=0 LIMIT 50 - récupère rapidement le prochain batch à analyser.

**INDEX idx_event_date ON events(event_date)** : Pour trier par récence : ORDER BY event_date DESC - afficher les événements les plus récents en premier.

**[TABLE 3 : COUNTRY_EMOTIONS - L'agrégation finale]**

**Champ country (TEXT PRIMARY KEY)** : Le pays en minuscules. Pourquoi PRIMARY KEY ? Un seul enregistrement par pays. Pourquoi minuscules ? Normalisation - évite 'France' vs 'france' vs 'FRANCE'. Fonction LOWER() appliquée partout.

**Champ emotions (TEXT)** : JSON : {"joy": 0.35, "sadness": 0.25, ...}. Pourquoi JSON ? Flexibilité - 7 émotions aujourd'hui, peut-être 10 demain. Alternative considérée : 7 colonnes (joy REAL, sadness REAL, ...). Rejeté car : moins flexible, requêtes plus complexes. Avec JSON, le frontend consomme directement.

**Champ top_emotion (TEXT)** : L'émotion dominante. Pourquoi stocker alors qu'on a le JSON emotions ? Pour sorting - ORDER BY top_emotion. Pour filtrage rapide - WHERE top_emotion='joy'. Pour affichage - pas besoin de parser le JSON.

**Champ confidence (REAL)** : Confiance de l'émotion dominante. Ex: si joy=0.45 est la plus haute, confidence=0.45. Pourquoi utile ? Pour filtrer les résultats peu fiables. Si confidence<0.3, afficher 'inconnu'.

**Champ total_posts (INTEGER)** : Somme de tous les post_count des événements. Pourquoi pas event_count ? Parce qu'on veut savoir combien de PUBLICATIONS (discussions réelles) il y a, pas combien d'événements agrégés.

**Champ event_count (INTEGER)** : Nombre d'événements. Pourquoi utile ? Pour montrer l'activité - un pays avec 100 publications groupées en 2 événements (2 gros sujets) vs 100 publications en 50 événements (plein de petits sujets).

**Champ top_topics (TEXT)** : JSON : ["climate", "economy", "politics"]. Extraction de mots-clés des titres. Pourquoi JSON ? Pour flexibilité - 3 topics aujourd'hui, peut-être 10 demain.

**Champ last_updated (TEXT)** : Horodatage de la dernière agrégation. Pourquoi ? Pour debugging - vérifier la fraîcheur des données. Pour cache invalidation - si last_updated est récent, cache est valide.

**[Compromis de normalisation - TRÈS IMPORTANT]**

Le professeur demandera : 'Pourquoi stocker emotions en JSON au lieu de normaliser avec une table emotions séparée ?'

**Approche normalisée (3NF) rejetée :**
```sql
CREATE TABLE country_emotions_normalized (
  country TEXT,
  emotion TEXT,
  confidence REAL,
  PRIMARY KEY (country, emotion)
);
```

**Pourquoi rejetée ?**
1. **Requêtes plus complexes** : Pour récupérer toutes les émotions d'un pays, il faut 7 JOINs ou 7 requêtes. Avec JSON, une seule requête.
2. **Charge de travail orientée lecture** : On lit 1000x plus qu'on écrit. La normalisation optimise les écritures (éviter la duplication), mais pénalise les lectures (plus de JOINs).
3. **Consommation frontend** : Le frontend veut exactement ce format JSON. Avec la normalisation, il faudrait restructurer côté backend.
4. **Duplication négligeable** : 195 pays × 7 émotions = 1365 lignes. Minuscule.

**Conclusion** : Pour notre cas d'usage (lecture >> écriture, données relativement statiques, frontend JSON-friendly), la dénormalisation avec JSON est le choix optimal.

**[SQLite + WAL Mode - Pourquoi ce choix ?]**

**Pourquoi SQLite ?**
- **Zéro configuration** : Pas de serveur PostgreSQL à installer/maintenir
- **Un seul fichier** : database.db - facile à backup
- **Suffisant pour l'échelle** : 1000 publications/jour, 100MB/semaine
- **ACID garanti** : Pas de corruption de données

**Pourquoi WAL Mode ?**
- WAL = Write-Ahead Logging
- **Lectures concurrentes** : Plusieurs readers peuvent lire pendant qu'un writer écrit
- Sans WAL : Les writes bloquent les reads
- **Crucial pour nous** : Le pipeline écrit constamment, le frontend lit constamment

**Quand migrer vers PostgreSQL ?**
- Si on dépasse 10GB de données
- Si on veut du scaling horizontal (replicas)
- Si on a besoin de features SQL avancées (window functions, CTEs)
- Pour l'instant : SQLite est parfait

Cette structure de base de données a été minutieusement optimisée pour notre pattern d'accès : beaucoup de lectures, quelques écritures, données semi-structurées (JSON), et fenêtre temporelle glissante (7 jours). Voyons maintenant comment l'apprentissage automatique s'intègre..."

---

## 9. Intégration de l'Apprentissage Automatique

### Architecture du Pipeline ML

```mermaid
flowchart LR
    subgraph Input
        Text[Texte de l'Événement<br/>Traduit en anglais]
    end
    
    subgraph Preprocessing
        Clean[Nettoyage du Texte<br/>Supprimer URLs, mentions]
        Token[Tokenisation<br/>Tokeniseur RoBERTa]
        Pad[Padding/Troncature<br/>Max 512 jetons]
    end
    
    subgraph "Modèle RoBERTa (500MB)"
        Embed[Couche d'Embedding<br/>768 dimensions]
        Trans[12 Couches Transformer<br/>Auto-Attention]
        Pool[Couche de Pooling<br/>Jeton CLS]
        Class[Tête de Classification<br/>7 émotions]
    end
    
    subgraph Output
        Softmax[Activation Softmax<br/>Distribution de probabilité]
        Top[ArgMax<br/>Émotion principale + confiance]
    end
    
    subgraph Fallback
        VADER[Sentiment VADER<br/>Basé sur lexique]
        Map[Mapper vers Émotions<br/>positive→joy, negative→sadness]
    end
    
    Text --> Clean
    Clean --> Token
    Token --> Pad
    Pad --> Embed
    Embed --> Trans
    Trans --> Pool
    Pool --> Class
    Class --> Softmax
    Softmax --> Top
    
    Class -.->|Erreur| VADER
    VADER -.->|Secours| Map
    Map -.->|Par défaut| Top
    
    Top --> Result["Émotion: joy<br/>Confiance: 0.87"]
    
    style Trans fill:#9B59B6,stroke:#333,stroke-width:3px,color:#fff
    style VADER fill:#E67E22,stroke:#333,stroke-width:2px,color:#fff
    style Result fill:#2ECC71,stroke:#333,stroke-width:2px,color:#fff
```

### 📢 Notes de Présentation - Section 9 (Architecture ML)

**[Durée: 5-6 minutes]**

"Maintenant, plongeons dans le cœur de notre intelligence artificielle : le pipeline d'apprentissage automatique. Ce diagramme montre exactement comment nous transformons un texte brut en émotion détectée. Suivons le flux étape par étape.

**[Les composants]** Ce diagramme est organisé en 5 sous-graphes principaux : Input (entrée), Preprocessing (prétraitement), le Modèle RoBERTa lui-même, Output (sortie), et Fallback (secours). Vous voyez aussi un flux principal en flèches pleines et un flux de secours en pointillés.

**[Input - Point de départ]** Tout commence avec le 'Texte de l'Événement Traduit en anglais'. C'est crucial : notre modèle RoBERTa est entraîné uniquement sur l'anglais, c'est pourquoi nous traduisons tout en amont. Ce texte peut être un résumé d'événement généré par le clustering, ou une publication individuelle.

**[Preprocessing - Étape 1 : Nettoyage]** **Flèche 1** : Le texte brut passe d'abord par le nettoyage. Regardez cette boîte : 'Nettoyage du Texte - Supprimer URLs, mentions'. Nous retirons les URLs (http://...), les mentions (@username), les hashtags, et tout ce qui n'est pas du texte significatif. Pourquoi ? Parce que ces éléments polluent l'analyse émotionnelle sans apporter de valeur sémantique.

**[Preprocessing - Étape 2 : Tokenisation]** **Flèche 2** : Le texte nettoyé est ensuite tokenisé. Vous voyez 'Tokenisation - Tokeniseur RoBERTa'. Le tokeniseur découpe le texte en unités atomiques appelées tokens - ce ne sont pas exactement des mots, mais des sous-mots. Par exemple, 'unhappiness' pourrait devenir ['un', 'happiness']. C'est la force de RoBERTa : il comprend la structure morphologique des mots.

**[Preprocessing - Étape 3 : Padding/Troncature]** **Flèche 3** : Ensuite vient le padding et la troncature. Regardez : 'Max 512 jetons'. RoBERTa a une limite stricte de 512 tokens. Si le texte est plus court, nous ajoutons du padding (des tokens spéciaux [PAD]). S'il est plus long, nous le tronquons. C'est une contrainte architecturale du modèle Transformer.

**[Modèle RoBERTa - Le cœur en violet]** Maintenant, nous entrons dans le modèle RoBERTa lui-même, représenté en violet. C'est un bloc de 500 mégaoctets avec plusieurs couches.

**[RoBERTa - Étape 1 : Embedding]** **Flèche 4** : Les tokens entrent dans la 'Couche d'Embedding - 768 dimensions'. Chaque token est converti en un vecteur de 768 nombres réels. C'est la représentation numérique dense du sens sémantique. 768 dimensions, c'est énorme - c'est ce qui permet au modèle de capturer des nuances subtiles.

**[RoBERTa - Étape 2 : Transformers]** **Flèche 5** : Ces embeddings passent ensuite par '12 Couches Transformer - Auto-Attention'. C'est le cœur du cœur. Chaque couche Transformer utilise le mécanisme d'auto-attention : chaque mot 'regarde' tous les autres mots pour comprendre le contexte. Par exemple, dans 'Je ne suis pas heureux', le modèle comprend que 'pas' inverse le sens de 'heureux'. Les 12 couches empilées permettent une compréhension profonde et hiérarchique.

**[RoBERTa - Étape 3 : Pooling]** **Flèche 6** : Après les 12 transformers, nous avons 512 vecteurs (un par token). La 'Couche de Pooling - Jeton CLS' extrait uniquement le premier token spécial [CLS] (pour 'classification'). Ce token unique a été entraîné pour résumer tout le contexte de la phrase en un seul vecteur de 768 dimensions.

**[RoBERTa - Étape 4 : Classification]** **Flèche 7** : Ce vecteur CLS entre dans la 'Tête de Classification - 7 émotions'. C'est une simple couche dense (fully connected) qui projette les 768 dimensions vers 7 scores bruts - un pour chaque émotion : joie, tristesse, colère, peur, surprise, dégoût, neutre.

**[Output - Normalisation et Extraction]** Nous sortons maintenant du bloc violet.

**[Sortie - Étape 1 : Softmax]** **Flèche 8** : Les 7 scores bruts passent par 'Activation Softmax - Distribution de probabilité'. Softmax normalise les scores pour qu'ils somment à 1.0, créant une véritable distribution de probabilité. Par exemple : {joie: 0.45, tristesse: 0.30, colère: 0.15, ...}.

**[Sortie - Étape 2 : ArgMax]** **Flèche 9** : Enfin, 'ArgMax - Émotion principale + confiance' sélectionne l'émotion avec la probabilité la plus élevée. Si joie = 0.45 est le maximum, notre résultat est 'Émotion: joy, Confiance: 0.45'.

**[Résultat Final]** **Flèche 10** : Vous voyez la boîte verte finale : 'Émotion: joy, Confiance: 0.87'. C'est notre output final qui sera stocké dans la base de données.

**[Flux de Secours - Le Plan B]** Maintenant, regardez attentivement les flèches en pointillés. C'est notre système de résilience.

**[Secours - Déclenchement]** Si à n'importe quel moment dans le modèle RoBERTa une erreur se produit - mémoire insuffisante, timeout, crash du modèle - regardez cette flèche en pointillés depuis 'Tête de Classification' vers 'Sentiment VADER'. **Flèche de secours 1** : Nous basculons immédiatement vers VADER (Valence Aware Dictionary and sEntiment Reasoner).

**[Secours - VADER]** Vous voyez la boîte orange : 'Sentiment VADER - Basé sur lexique'. VADER est un analyseur de sentiment beaucoup plus simple. Il ne fait pas d'apprentissage profond - il utilise juste un dictionnaire de mots avec leurs polarités. Par exemple : 'heureux' = +0.8, 'triste' = -0.7. C'est rapide, léger, mais moins précis.

**[Secours - Mapping]** **Flèche de secours 2** : VADER nous donne un score de sentiment simple : positif, négatif, ou neutre. La boîte 'Mapper vers Émotions' fait la conversion : positive → joy, negative → sadness, neutral → neutral. C'est une simplification, mais c'est mieux que rien.

**[Secours - Convergence]** **Flèche de secours 3** : Ce résultat de secours rejoint le flux principal avec 'Par défaut' et alimente la même sortie finale. Si VADER échoue aussi (très rare), nous retournons par défaut : émotion 'neutral' avec confiance 0.3.

**[Performances et Compromis]** Pourquoi cette architecture ? RoBERTa nous donne 90% de précision mais prend 50-100ms par événement sur CPU et nécessite 500 MB de RAM. VADER est instantané et nécessite seulement quelques MB, mais n'a que 60-70% de précision. Le système de secours garantit que nous produisons toujours un résultat, même si le modèle principal tombe en panne.

**[Visualisation des couleurs]** Les couleurs du diagramme ont un sens : violet pour le modèle d'apprentissage profond (RoBERTa), orange pour le secours basique (VADER), et vert pour le résultat final réussi.

**[Flux de données]** Notez que c'est un flux strictement unidirectionnel de gauche à droite - pas de boucles, pas de retour en arrière. C'est délibéré : cela rend le système prévisible, facile à déboguer, et facilite le traitement par lots.

Cette architecture ML combine l'état de l'art (RoBERTa) avec la résilience (VADER fallback) pour garantir à la fois précision et fiabilité. Voyons maintenant comment nous gérons l'évolutivité et la performance du système global..."

---

### Modèle de Détection des Émotions

**Modèle**: `j-hartmann/emotion-english-distilroberta-base`

**Architecture**:
- Base: RoBERTa (Robustly Optimized BERT)
- Affiné sur: 6 ensembles de données d'émotions
- Paramètres: ~82M
- Taille: ~500MB
- Inférence: CPU (PyTorch)

**Données d'Entraînement**:
- 58 000 exemples étiquetés
- 7 émotions: joy, sadness, anger, fear, surprise, disgust, neutral
- Équilibré entre les émotions

**Performance**:
- Précision: ~90% sur l'ensemble de test
- Temps d'inférence: ~50-100ms par événement (CPU)
- Mémoire: ~500MB modèle chargé

**Pourquoi RoBERTa ?**
- État de l'art pour la classification de texte
- Pré-entraîné sur un corpus massif
- Meilleur que BERT pour notre cas d'usage
- Maintenance active et communauté

### Algorithme de Clustering

**Algorithme**: DBSCAN (Density-Based Spatial Clustering)

**Paramètres**:
- `eps=0.75`: Distance maximale (1 - cosine_similarity)
- `min_samples=2`: Minimum de publications par cluster
- `metric='precomputed'`: Utiliser la matrice de similarité cosinus

**Pourquoi DBSCAN ?**:
- Ne nécessite pas de nombre de clusters prédéfini
- Gère le bruit (points non regroupés)
- Fonctionne bien avec des densités variables
- Robuste aux valeurs aberrantes

**Métrique de Distance**:
```python
# Vecteurs TF-IDF → Similarité cosinus
similarity = cosine_similarity(tfidf_matrix)

# Convertir en distance pour DBSCAN
distance = 1 - similarity
```

**Interprétation des Clusters**:
- `label >= 0`: Cluster d'événement
- `label == -1`: Événement autonome (pas du bruit !)

### Approche de Résumé

**Méthode**: Extractive (basée sur TF-IDF)

**Algorithme**:
1. Diviser le texte en phrases
2. Calculer les scores TF-IDF pour chaque phrase
3. Ajouter un bonus de position (plus tôt = score plus élevé)
4. Soustraire la pénalité de longueur (très long = score plus faible)
5. Filtrer les phrases (20-200 caractères)
6. Sélectionner les 2 meilleures phrases
7. Trier par position d'origine (maintenir le flux)
8. Limiter à 250 caractères au total

**Pourquoi Extractif ?**:
- Rapide: Aucun réseau neuronal nécessaire
- Léger: ~50MB vectoriseur TF-IDF
- Précis: Préserve la formulation originale
- Pas de GPU: Peut fonctionner facilement sur CPU

**Alternative Considérée**:
- Résumé abstractif T5: Modèle de 1GB, plus lent, GPU recommandé
- Compromis: Vitesse et efficacité des ressources plutt que créativité

---

## 10. Évolutivité et Performance

### Performance Actuelle

| Métrique | Valeur | Notes |
|--------|-------|-------|
| **Temps de Cycle du Pipeline** | 30 secondes | Temps entre les cycles |
| **Temps de Traitement Total** | 52-105s (moy 75s) | De bout en bout par cycle |
| **Pays par Lot** | 30 | Rotation circulaire |
| **Publications par Pays** | 5-30 | Varie selon l'activité |
| **Événements Créés** | 10-50/cycle | Dépend du clustering |
| **Utilisation Mémoire** | ~2GB | Incluant les modèles ML |
| **Taille de la Base de Données** | ~100MB | Après 1 semaine de données |
| **Temps de Réponse API** | <200ms | Endpoint `/api/emotions` |

### Goulots d'Étranglement et Optimisations

#### 1. Limites de Débit de l'API Reddit
**Problème**: Limite de 60 requêtes/minute  
**Solution**:
- Délai de 0,5s entre les requêtes
- Workers parallèles (10 threads)
- Traitement par lots (30 pays à la fois)
- Mise en cache intelligente (ne pas récupérer les doublons)

#### 2. Appels à l'API de Traduction
**Problème**: Limites de débit de Google Translate  
**Solution**:
- Découpage du texte long (max 4500 caractères)
- Traduction uniquement du contenu non-anglais
- Repli sur l'original en cas d'erreurs

#### 3. Temps d'Inférence RoBERTa
**Problème**: 50-100ms par événement (CPU)  
**Solution**:
- Traitement par lots (50 événements à la fois)
- Inférence CPU (GPU serait plus rapide mais coûteux)
- Traiter uniquement les nouveaux événements (is_analyzed=0)

#### 4. Contention de la Base de Données
**Problème**: Goulot d'étranglement d'écriture unique SQLite  
**Solution**:
- Mode WAL (lectures concurrentes pendant les écritures)
- Insertions par lots lorsque possible
- Indexation des champs fréquemment interrogés

### Stratégie de Mise à l'Échelle

#### Mise à l'Échelle Horizontale (Futur)

**Architecture Actuelle vs Future**:

```mermaid
graph TB
    subgraph "Actuel: Serveur Unique"
        S1[Tous les Services<br/>Une Machine<br/>2GB RAM]
        D1[(SQLite)]
        S1 --> D1
    end
    
    subgraph "Futur: Cluster Kubernetes"
        LB[Équilibreur de Charge<br/>NGINX]
        
        subgraph "Pod Passerelle API (3 réplicas)"
            GW1[Passerelle 1]
            GW2[Passerelle 2]
            GW3[Passerelle 3]
        end
        
        subgraph "Pod Récupérateur de Données (5 réplicas)"
            DF1[Récupérateur 1]
            DF2[Récupérateur 2]
            DF3[Récupérateur 3]
            DF4[Récupérateur 4]
            DF5[Récupérateur 5]
        end
        
        subgraph "Pod Analyseur ML (2 réplicas + GPU)"
            ML1[ML 1 GPU]
            ML2[ML 2 GPU]
        end
        
        LB --> GW1
        LB --> GW2
        LB --> GW3
        
        GW1 --> DF1
        GW1 --> DF2
        GW2 --> DF3
        GW2 --> DF4
        GW3 --> DF5
        
        GW1 --> ML1
        GW2 --> ML2
        
        DF1 --> PG
        DF2 --> PG
        ML1 --> PG
        ML2 --> PG
        
        subgraph "Cluster de Base de Données"
            PG[(PostgreSQL<br/>Primaire)]
            R1[(Réplica Lecture 1)]
            R2[(Réplica Lecture 2)]
            PG -.->|Réplication| R1
            PG -.->|Réplication| R2
        end
    end
    
    style S1 fill:#E74C3C,stroke:#333,stroke-width:2px,color:#fff
    style LB fill:#2ECC71,stroke:#333,stroke-width:2px,color:#fff
    style ML1 fill:#9B59B6,stroke:#333,stroke-width:2px,color:#fff
    style ML2 fill:#9B59B6,stroke:#333,stroke-width:2px,color:#fff
```

**Chemin de Migration**:
1. Conteneuriser les services (Docker)
2. Orchestrer avec Kubernetes
3. Migrer SQLite → PostgreSQL
4. Ajouter des réplicas de lecture
5. Implémenter des politiques d'auto-scaling

#### Mise à l'Échelle Verticale (Immédiat)

- Augmenter la RAM: 4GB → 16GB (plus de modèles ML en mémoire)
- Ajouter un GPU: Inférence RoBERTa 10x plus rapide
- Plus de cœurs CPU: Workers parallèles 10 → 50

### Stratégie de Mise en Cache

```
Niveau 1: Cache d'Application (Passerelle API)
├─ TTL: 30 secondes
├─ Clés: /api/emotions, /api/country/{name}
└─ Éviction: Complétion du pipeline en arrière-plan

Niveau 2: Résultats de Requêtes de Base de Données
├─ Index sur les champs fréquemment interrogés
├─ Agrégations matérialisées (table country_emotions)
└─ Sujets principaux précalculés
```

---

## 11. Gestion des Erreurs et Résilience

### Modèles de Résilience

#### 1. Modèle de Disjoncteur

**Implémentation**: Bibliothèque PyBreaker

```python
data_fetcher_breaker = CircuitBreaker(
    fail_max=5,        # Ouvrir après 5 échecs
    reset_timeout=60   # Réessayer après 60 secondes
)
```

**Machine à États du Disjoncteur**:

```mermaid
stateDiagram-v2
    [*] --> Closed
    
    Closed --> Open: 5 échecs consécutifs
    Closed --> Closed: Requête réussie<br/>(réinitialiser le compteur)
    
    Open --> HalfOpen: 60 secondes écoulées<br/>(délai de réinitialisation)
    Open --> Open: Requête rejetée<br/>(échec rapide)
    
    HalfOpen --> Closed: Requête réussie<br/>(service récupéré)
    HalfOpen --> Open: Requête échouée<br/>(toujours en panne)
    
    note right of Closed
        Opération normale
        Toutes les requêtes passent
        Compteur: 0/5
    end note
    
    note right of Open
        Service en panne
        Rejeter toutes les requêtes immédiatement
        Attendre le délai de réinitialisation
    end note
    
    note right of HalfOpen
        Test de récupération
        Autoriser 1 requête de test
        Décider: Closed ou Open
    end note
```

**États**:
- **Closed**: Opération normale, les requêtes passent
- **Open**: Trop d'échecs, requêtes rejetées immédiatement
- **Half-Open**: Test si le service a récupéré

**Avantages**:
- Prévient les défaillances en cascade
- Échec rapide (pas d'attente de délai)
- Test automatique de récupération

### 📢 Notes de Présentation - Section 11 (Circuit Breaker)

**[Durée: 5-6 minutes]**

"Maintenant, parlons d'un pattern de résilience crucial : le Circuit Breaker, ou disjoncteur. Ce diagramme de machine à états montre exactement comment notre système se protège contre les défaillances en cascade. Analysons chaque élément.

**[Le concept du Circuit Breaker]** D'abord, comprenons la métaphore. Comme un disjoncteur électrique dans votre maison qui coupe le courant quand il y a une surcharge, notre Circuit Breaker logiciel coupe les requêtes vers un service défaillant. Pourquoi ? Pour éviter de le surcharger davantage et permettre sa récupération.

**[Configuration - Les paramètres]** Regardez le code Python :
```python
data_fetcher_breaker = CircuitBreaker(
    fail_max=5,        # Ouvrir après 5 échecs
    reset_timeout=60   # Réessayer après 60 secondes
)
```

**fail_max=5** : Pourquoi 5 et pas 1 ou 10 ? Parce que 1 serait trop sensible - une seule erreur réseau transitoire ouvrirait le circuit. Et 10 serait trop tolérant - 10 échecs signifient que le service est vraiment en panne, pas besoin d'attendre plus. 5 est un sweet spot testé empiriquement.

**reset_timeout=60** : Pourquoi 60 secondes ? Parce que la plupart des redémarrages de service prennent 10-30 secondes. 60s donne une marge confortable. Pourquoi pas 300s (5 minutes) ? Trop long - on veut reprendre le service rapidement dès qu'il est rétabli.

**[Le diagramme de machine à états]** C'est un State Diagram avec 3 états principaux. Regardons la structure : nous avons un point de départ [*], trois rectangles représentant les états (Closed, Open, HalfOpen), et des transitions fléchées entre eux.

**[État 1 : CLOSED - Opération normale - Couleur par défaut]**

Regardez la boîte 'Closed' avec la note à droite : 'Opération normale, Toutes les requêtes passent, Compteur: 0/5'. 

**Que signifie 'Closed' ?** Contre-intuitif ! En électricité, un circuit 'fermé' signifie que le courant PASSE. C'est pareil ici - le circuit fermé laisse passer les requêtes. C'est l'état normal et sain.

**Compteur 0/5** : C'est un compteur d'échecs qui s'incrémente à chaque erreur et se réinitialise à chaque succès. Actuellement à 0, ce qui signifie zéro échec récent.

**[Transition 1 : Closed → Closed (Boucle)]** Flèche qui revient sur elle-même avec le label 'Requête réussie (réinitialiser le compteur)'. Que se passe-t-il ? 
- Une requête arrive
- Le service répond avec succès (HTTP 200)
- Le compteur est réinitialisé à 0/5
- On reste dans l'état Closed

Pourquoi réinitialiser à chaque succès ? Parce qu'on veut détecter les échecs CONSÉCUTIFS, pas cumulatifs. Si on a : succès, succès, échec, succès, échec, le compteur est toujours à 1, pas à 2. Seuls les échecs consécutifs comptent.

**[Transition 2 : Closed → Open (La coupure)]** Flèche vers l'état Open avec le label '5 échecs consécutifs'. C'est le moment critique.

**Scénario** : 
1. Requête 1 → Échec → Compteur: 1/5
2. Requête 2 → Échec → Compteur: 2/5
3. Requête 3 → Échec → Compteur: 3/5
4. Requête 4 → Échec → Compteur: 4/5
5. Requête 5 → Échec → Compteur: 5/5 → **TRANSITION vers OPEN**

Pourquoi 5 échecs consécutifs signalent une panne ? Parce que la probabilité qu'une erreur réseau aléatoire se reproduise 5 fois de suite est infime (< 0.1% si taux d'erreur réseau = 5%). 5 échecs consécutifs = service vraiment en panne.

**[État 2 : OPEN - Le circuit est coupé - État de protection]**

Regardez la note : 'Service en panne, Rejeter toutes les requêtes immédiatement, Attendre le délai de réinitialisation'. 

**Comportement** : Toute nouvelle requête qui arrive est IMMÉDIATEMENT rejetée avec une erreur de type 'CircuitBreakerOpen' SANS même essayer de contacter le service. 

**Pourquoi ce comportement ?** Trois raisons critiques :
1. **Protéger le service** : Il est déjà en difficulté. Continuer à lui envoyer des requêtes empire la situation (plus de charge CPU, plus de mémoire, empêche le redémarrage).
2. **Échec rapide (Fail Fast)** : Au lieu d'attendre un timeout de 120 secondes, on répond immédiatement 'service indisponible'. L'utilisateur voit l'erreur en 1ms au lieu de 120s. Meilleure expérience.
3. **Économiser les ressources** : Pas besoin de gaspiller des threads, des connexions TCP, etc. sur des requêtes qui échoueront de toute façon.

**[Transition 3 : Open → Open (Boucle de rejet)]** Flèche qui boucle avec le label 'Requête rejetée (échec rapide)'. Tant qu'on est dans Open :
- Requête arrive
- Vérifie l'état : Open
- Rejette immédiatement
- Reste dans Open
- Pas de compteur, pas d'incrémentation - on rejette juste

**[Transition 4 : Open → HalfOpen (Le test de récupération)]** Flèche vers HalfOpen avec le label '60 secondes écoulées (délai de réinitialisation)'. 

**Mécanisme** : Un timer démarre dès qu'on entre dans Open. Après exactement 60 secondes :
- Transition automatique vers HalfOpen
- Aucune requête nécessaire pour déclencher ça
- C'est un processus en arrière-plan

Pourquoi automatique ? Parce qu'on veut donner une chance au service de se rétablir. Peut-être qu'il a redémarré automatiquement, ou que le problème réseau est résolu.

**[État 3 : HALF-OPEN - Le test prudent - État de transition]**

Note : 'Test de récupération, Autoriser 1 requête de test, Décider: Closed ou Open'.

**Comportement** : C'est un état très court et très spécifique :
1. Autoriser EXACTEMENT UNE requête de passer (une requête 'probe' ou 'test')
2. Si elle réussit → Transition vers Closed (service récupéré !)
3. Si elle échoue → Transition vers Open (toujours en panne, réessayer dans 60s)

Pourquoi une seule requête ? Parce que c'est un test prudent. On ne veut pas bombarder le service avec 100 requêtes si il est toujours en panne. Une seule requête test suffit pour savoir.

**[Transition 5 : HalfOpen → Closed (Récupération réussie)]** Flèche vers Closed avec 'Requête réussie (service récupéré)'.

**Scénario de succès** :
- On est en HalfOpen
- La requête test arrive
- Résultat : HTTP 200 (succès !)
- Conclusion : Le service a récupéré
- Action : Transition vers Closed, réinitialiser le compteur à 0/5
- Effet : Le trafic normal reprend

C'est le happy path - le service est revenu à la normale.

**[Transition 6 : HalfOpen → Open (Toujours en panne)]** Flèche vers Open avec 'Requête échouée (toujours en panne)'.

**Scénario d'échec** :
- On est en HalfOpen
- La requête test arrive
- Résultat : Timeout / HTTP 500 / Erreur de connexion
- Conclusion : Le service est toujours en panne
- Action : Retour vers Open
- Effet : Redémarrer le timer de 60s, réessayer plus tard

**[Exemple concret de flux complet]**

Imaginons un scénario réel :

**10h00:00** - État: Closed, Compteur: 0/5. Tout va bien.

**10h00:10** - Le service Data Fetcher crashe (mémoire insuffisante).

**10h00:11** - Requête 1 → Échec (connection refused) → Compteur: 1/5

**10h00:12** - Requête 2 → Échec → Compteur: 2/5

**10h00:13** - Requête 3 → Échec → Compteur: 3/5

**10h00:14** - Requête 4 → Échec → Compteur: 4/5

**10h00:15** - Requête 5 → Échec → Compteur: 5/5 → **Transition vers OPEN**

**10h00:16 à 10h01:14** - État: Open. Toutes les requêtes rejetées immédiatement avec CircuitBreakerOpen. Le service a le temps de redémarrer automatiquement.

**10h01:15** - 60 secondes écoulées → **Transition automatique vers HALF-OPEN**

**10h01:16** - Requête test arrive → Envoyée au service → Succès (200 OK) → **Transition vers CLOSED**

**10h01:17** - État: Closed, Compteur: 0/5. Le trafic normal reprend.

**[Les trois avantages clés - Pourquoi utiliser ce pattern ?]**

**Avantage 1 : Prévient les défaillances en cascade**
Sans Circuit Breaker : Data Fetcher crashe → API Gateway continue d'envoyer des requêtes → Data Fetcher surchargé → ne peut pas redémarrer → Event Extractor timeout en attendant → tout le système ralentit → défaillance totale.

Avec Circuit Breaker : Data Fetcher crashe → Circuit s'ouvre après 5 échecs → Rejets immédiats → Data Fetcher a le temps de redémarrer proprement → Récupération en 60s → Système stable.

**Avantage 2 : Échec rapide (Fail Fast)**
Sans Circuit Breaker : Chaque requête attend le timeout complet (90s pour Data Fetcher) → L'utilisateur attend 90s pour voir une erreur → Horrible expérience.

Avec Circuit Breaker : Circuit ouvert → Rejet en <1ms → L'utilisateur voit immédiatement 'Service temporairement indisponible' → Peut réessayer plus tard.

**Avantage 3 : Test automatique de récupération**
Sans Circuit Breaker : Le service redémarre, mais personne n'essaie de l'utiliser → Pas de détection automatique de récupération.

Avec Circuit Breaker : Après 60s, requête test automatique → Si succès, trafic reprend automatiquement → Pas d'intervention manuelle nécessaire.

**[Implémentation avec PyBreaker]** Pourquoi utiliser la bibliothèque PyBreaker et pas coder à la main ?
- **Code testé en bataille** : PyBreaker est utilisé en production par des milliers d'apps
- **Thread-safe** : Gère correctement les compteurs partagés entre threads
- **Configurable** : Facile de changer fail_max et reset_timeout
- **Lightweight** : Seulement quelques kilobytes

**[Où appliquons-nous le Circuit Breaker ?]** Regardez le diagramme d'architecture (Section 3) : toutes les flèches de API Gateway vers les microservices sont étiquetées 'Circuit Breaker'. Chaque service a son propre disjoncteur indépendant. Pourquoi ? Parce que si Data Fetcher tombe en panne, on ne veut pas bloquer ML Analyzer qui fonctionne bien.

Ce pattern de Circuit Breaker est absolument critique pour la résilience de notre système. Il transforme des défaillances catastrophiques en interruptions courtes et gérables. Voyons maintenant comment nous testons tout ce système..."

#### 2. Nouvelle Tentative avec Backoff Exponentiel

**Implémentation**: Bibliothèque Tenacity

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Timeout, ConnectionError))
)
def call_service():
    ...
```

**Stratégie**:
- Tentative 1: Immédiate
- Tentative 2: Attendre 4s
- Tentative 3: Attendre 8s
- Attente max: 10s

**Avantages**:
- Gère les problèmes réseau transitoires
- Ne surcharge pas le service défaillant
- Donne du temps pour la récupération

#### 3. Dégradation Gracieuse

**Chaîne de Repli**:

```
Détection d'Émotion RoBERTa
    ↓ (si échec)
Analyse de Sentiment VADER
    ↓ (si échec)
Par défaut: émotion neutre (confiance: 0.3)
```

**Extraction de Contenu**:
```
Extraction Complète d'Article
    ↓ (si échec)
Utiliser le Titre de Publication Original
```

**Traduction**:
```
Google Translate
    ↓ (si échec)
Retourner le Texte en Langue Originale
```

### Suivi des Erreurs

**Intégration Sentry**:

```python
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment='production',
    traces_sample_rate=0.1,  # 10% surveillance de performance
    integrations=[FlaskIntegration()]
)
```

**Événements Capturés**:
- Exceptions avec traces de pile
- Contexte de requête (URL, en-têtes, corps)
- Contexte utilisateur (si applicable)
- Métriques de performance (requêtes lentes)

**Avantages**:
- Notifications d'erreurs en temps réel
- Modèles d'erreurs agrégés
- Détection de régression de performance
- Tendances d'erreurs historiques

### Stratégie de Journalisation

**Journalisation Structurée**:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

**Niveaux de Log**:
- **DEBUG**: Étapes détaillées du pipeline (désactivé en production)
- **INFO**: Opérations normales (récupération terminée, événements créés)
- **WARNING**: Problèmes récupérables (délai API, nouvelle tentative)
- **ERROR**: Défaillances de service, exceptions
- **CRITICAL**: Défaillances système globales

**Rotation des Logs**:
- Taille max: 100MB par fichier
- Garder: 10 rotations
- Compression: gzip des anciens logs

---

## 12. Testing Strategy

### Test Pyramid

```
       ┌──────────────┐
       │  E2E Tests   │ ← 10% (full pipeline)
       └──────────────┘
      ┌────────────────┐
      │ Integration    │ ← 30% (service interactions)
      │     Tests      │
      └────────────────┘
    ┌──────────────────────┐
    │    Unit Tests        │ ← 60% (individual functions)
    └──────────────────────┘
```

### Unit Tests

**Coverage**: Individual functions and methods

**Example** (`test_data_fetcher.py`):

```python
def test_classify_link_post():
    """Tester la classification des publications de lien"""
    submission = Mock(
        is_self=False,
        title="Breaking News",
        url="https://bbc.com/article",
        created_utc=time.time()
    )
    
    result = classify_and_extract_post(submission, "france")
    
    assert result['post_type'] == 'link'
    assert result['needs_extraction'] == 1
    assert result['link_url'] == "https://bbc.com/article"

def test_circular_rotation():
    """Tester la rotation équitable des pays"""
    countries = ["france", "germany", "italy"]
    rotation = CircularRotation(countries)
    
    batch1, cycle1, idx1 = rotation.get_next_batch()
    
    assert len(batch1) == 3  # Un cycle complet
    assert cycle1 == 0       # Premier cycle
    assert idx1 == 0         # Réinitialiser au début
```

**Outils**:
- `pytest`: Framework de test
- `pytest-cov`: Rapport de couverture
- `unittest.mock`: Simulation des dépendances externes

### Tests d'Intégration

**Couverture**: Interactions service-à-service

**Exemple** (`test_integration.py`):

```python
def test_full_pipeline():
    """Tester le pipeline de données complet"""
    # 1. Récupérer les publications
    response = requests.post(
        'http://localhost:5001/fetch',
        json={'countries': ['france'], 'limit': 10}
    )
    assert response.status_code == 200
    
    # 2. Extraire le contenu
    response = requests.post(
        'http://localhost:5007/process/pending'
    )
    assert response.status_code == 200
    
    # 3. Extraire les événements
    response = requests.post(
        'http://localhost:5004/extract_events',
        json={'countries': ['france']}
    )
    events = response.json()
    assert events['total_events'] > 0
    
    # 4. Analyser les émotions
    response = requests.post(
        'http://localhost:5005/process/pending'
    )
    assert response.status_code == 200
    
    # 5. Agréger
    response = requests.post(
        'http://localhost:5003/aggregate/all'
    )
    assert response.status_code == 200
```

### Tests de Bout en Bout

**Couverture**: Flux de travail utilisateur

**Scénarios**:
1. L'utilisateur ouvre le tableau de bord → Voir la carte mondiale des émotions
2. L'utilisateur clique sur un pays → Voir les détails du pays
3. L'utilisateur déclenche une récupération manuelle → De nouvelles données apparaissent
4. Le système fonctionne pendant 24 heures → Aucun crash

**Outils**:
- Selenium: Automatisation de navigateur
- pytest-playwright: Tests E2E modernes

### Défis de Test

**Défi 1**: Dépendances API Externes (Reddit, Google Translate)  
**Solution**: Simuler les réponses API avec des données réalistes

**Défi 2**: Temps de Chargement du Modèle ML (10-15s)  
**Solution**: Chargement paresseux, mise en cache des modèles chargés entre les tests

**Défi 3**: Pipeline Asynchrone  
**Solution**: Interrogation avec délai d'attente pour la complétion du pipeline

---

## 13. Déploiement et DevOps

### Architecture de Déploiement Actuelle

```mermaid
graph TB
    subgraph Internet
        Users[Utilisateurs Mondiaux]
    end
    
    subgraph "Serveur Ubuntu 22.04 LTS - Nœud Unique"
        subgraph "Couche Frontend"
            Next[Application Next.js<br/>Port 3000<br/>npm run build]
        end
        
        subgraph "Services Backend - start-backend.sh"
            GW[Passerelle API :5000<br/>PID: gateway.pid]
            DF[Récupérateur de Données :5001<br/>PID: data-fetcher.pid]
            CE[Extracteur de Contenu :5007<br/>PID: content-extractor.pid]
            EE[Extracteur d'Événements :5004<br/>PID: event-extractor.pid]
            ML[Analyseur ML :5005<br/>PID: ml-analyzer.pid]
            AG[Agrégateur :5003<br/>PID: aggregator.pid]
        end
        
        subgraph "Stockage de Données"
            DB[(database.db<br/>SQLite + WAL)]
            Logs[Fichiers de Log<br/>*.log dans /logs]
        end
        
        subgraph "Environnement Python"
            Venv[Environnement Virtuel<br/>.venv/<br/>Python 3.9+]
            Models[Modèles ML<br/>RoBERTa ~500MB<br/>Mis en cache en mémoire]
        end
    end
    
    subgraph "Services Externes"
        Reddit[API Reddit<br/>OAuth2]
        Google[Google Translate<br/>Niveau Gratuit]
        Sentry[Sentry.io<br/>Suivi d'Erreurs]
    end
    
    Users -->|HTTPS| Next
    Next -->|HTTP| GW
    GW --> DF
    GW --> CE
    GW --> EE
    GW --> ML
    GW --> AG
    
    DF --> DB
    CE --> DB
    EE --> DB
    ML --> DB
    AG --> DB
    
    DF -.->|API Calls| Reddit
    CE -.->|Translation| Google
    GW -.->|Errors| Sentry
    
    ML --> Models
    
    DF --> Logs
    CE --> Logs
    EE --> Logs
    ML --> Logs
    AG --> Logs
    GW --> Logs
    
    style Next fill:#2ECC71,stroke:#333,stroke-width:2px
    style DB fill:#E74C3C,stroke:#333,stroke-width:3px,color:#fff
    style ML fill:#9B59B6,stroke:#333,stroke-width:2px,color:#fff
    style Models fill:#F39C12,stroke:#333,stroke-width:2px
```

### Vue de Déploiement Traditionnel

**Actuel**: Déploiement sur serveur unique

```
┌────────────────────────────────────┐
│      Serveur Ubuntu 22.04 LTS       │
│                                    │
│  ┌──────────────────────────────┐ │
│  │  start-backend.sh            │ │
│  │  ├─ data-fetcher (:5001)     │ │
│  │  ├─ content-extractor (:5007)│ │
│  │  ├─ event-extractor (:5004)  │ │
│  │  ├─ ml-analyzer (:5005)      │ │
│  │  ├─ aggregator (:5003)       │ │
│  │  └─ api-gateway (:5000)      │ │
│  └──────────────────────────────┘ │
│                                    │
│  ┌──────────────────────────────┐ │
│  │  Frontend (Next.js)          │ │
│  │  npm run build → Port 3000   │ │
│  └──────────────────────────────┘ │
│                                    │
│  Base de données: /microservices/database.db │
│  Logs: /logs/*.log                │
└────────────────────────────────────┘
```

### Gestion des Processus

**Script de Démarrage** (`start-backend.sh`):

```bash
#!/bin/bash
PROJECT_ROOT="/path/to/InternetOfEmotions-main"
VENV_PATH="$PROJECT_ROOT/backend/.venv"

# Démarrer chaque service en arrière-plan
start_service() {
    local service=$1
    local port=$2
    
    cd "$PROJECT_ROOT/backend/microservices/$service"
    nohup $VENV_PATH/bin/python app.py > "$PROJECT_ROOT/logs/$service.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/$service.pid"
}

# Démarrer tous les services avec un délai de 2s
start_service "data-fetcher" 5001
sleep 2
start_service "content-extractor" 5007
sleep 2
# ... etc
```

**Script d'Arrêt** (`stop-backend.sh`):

```bash
#!/bin/bash
stop_service() {
    local service=$1
    local pid_file="logs/$service.pid"
    
    if [ -f "$pid_file" ]; then
        kill $(cat "$pid_file")
        rm "$pid_file"
    fi
}

# Arrêter tous les services
stop_service "api-gateway"
stop_service "aggregator"
# ... etc
```

### Gestion de l'Environnement

**Environnement Virtuel**:

```bash
# Configuration
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# Geler les dépendances
pip freeze > backend/requirements.txt
```

**Variables d'Environnement** (`.env`):

```bash
# API Reddit (requis)
REDDIT_CLIENT_ID=xxx
REDDIT_CLIENT_SECRET=xxx
REDDIT_USER_AGENT=InternetOfEmotions/1.0

# Optionnel
MAX_POST_AGE_DAYS=28
DATA_FETCH_WORKERS=10
SENTRY_DSN=https://...@sentry.io/...
```

### Pipeline CI/CD (Futur)

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Exécuter les tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: SSH et déployer
        run: |
          ssh user@server 'cd /app && git pull && ./stop-backend.sh && ./start-backend.sh'
```

---

## 14. Surveillance et Observabilité

### Vérifications de Santé

**Niveau Service**:

```http
GET /health → {"status": "healthy", "service": "data-fetcher"}
```

**Niveau Système**:

```http
GET /api/health → {
  "status": "healthy",
  "services": {
    "data-fetcher": "healthy",
    "content-extractor": "healthy",
    ...
  },
  "db_posts": 1234
}
```

### Métriques

**Endpoint Compatible Prometheus** (`/metrics`):

```
# HELP api_requests_total Nombre total de requêtes API
# TYPE api_requests_total counter
api_requests_total{method="GET",endpoint="/api/emotions"} 1234

# HELP pipeline_duration_seconds Temps d'exécution du pipeline
# TYPE pipeline_duration_seconds histogram
pipeline_duration_seconds_bucket{le="60"} 50
pipeline_duration_seconds_bucket{le="90"} 85
pipeline_duration_seconds_sum 6543
pipeline_duration_seconds_count 100

# HELP circuit_breaker_state États du disjoncteur
# TYPE circuit_breaker_state gauge
circuit_breaker_state{service="data-fetcher",state="closed"} 1
circuit_breaker_state{service="ml-analyzer",state="open"} 0
```

### Tableaux de Bord (Futur)

**Tableau de Bord Grafana**:

```
┌─────────────────────────────────────────┐
│  Santé du Système                          │
│  ✅ Tous les services sains                │
│  📊 Cycles du pipeline: 2,456              │
│  ⏱️  Temps moyen du cycle: 68s                │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Volume de Données (24h)                      │
│  📥 Publications récupérées: 45,230               │
│  📰 Contenu extrait: 12,345           │
│  🎯 Événements créés: 3,456               │
│  🧠 Émotions analysées: 3,456            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Taux d'Erreurs (24h)                      │
│  ⚠️  Erreurs Reddit 429: 23              │
│  ❌ Échecs de traduction: 5             │
│  🔴 Ouvertures du disjoncteur: 2         │
└─────────────────────────────────────────┘
```

### Règles d'Alerte

```yaml
# Alerte si le pipeline se bloque
- alert: PipelineStalled
  expr: time() - pipeline_last_run > 300
  annotations:
    description: "Le pipeline n'a pas été exécuté depuis 5 minutes"

# Alerte si le disjoncteur s'ouvre
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state{state="open"} == 1
  annotations:
    description: "Disjoncteur du service {{ $labels.service }} ouvert"

# Alerte si la base de données grandit trop vite
- alert: DatabaseSizeHigh
  expr: database_size_bytes > 10e9  # 10GB
  annotations:
    description: "La base de données dépasse 10GB"
```

---

## 15. Considérations de Sécurité

### Sécurité de l'API

**Authentification**: Non implémentée (futur: jetons JWT)  
**Limitation de Débit**: Non implémentée (futur: limites par IP)  
**CORS**: Activé pour le domaine frontend

**Validation des Entrées**:

```python
# Valider les noms de pays
allowed_countries = set(ALL_COUNTRIES)
if country.lower() not in allowed_countries:
    return jsonify({'error': 'Pays invalide'}), 400

# Assainir les entrées utilisateur
import bleach
country = bleach.clean(request.json.get('country', ''))
```

### Confidentialité des Données

**Gestion des PII**:
- ✅ Stocker uniquement les données publiques Reddit
- ✅ Pas de suivi utilisateur ni de cookies
- ✅ Aucune information personnelle collectée

**Conformité RGPD**:
- ✅ Toutes les données provenant de sources publiques
- ✅ Droit à la suppression: Effacer les publications >28 jours
- ✅ Portabilité des données: API JSON

### Gestion des Secrets

**Actuel**: Variables d'environnement (fichier `.env`)  
**Futur**: AWS Secrets Manager ou HashiCorp Vault

```python
# Ne jamais commit dans Git
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')

# Valider la présence
if not REDDIT_CLIENT_SECRET:
    raise ValueError("REDDIT_CLIENT_SECRET manquant")
```

### Sécurité des Dépendances

**Analyse des Vulnérabilités**:

```bash
# Vérifier les vulnérabilités connues
pip-audit

# Mettre à jour les dépendances
pip install --upgrade -r requirements.txt
```

**Versions Épinglées**:

```txt
# requirements.txt
Flask==3.0.0              # Épingler la version majeure
requests==2.31.0
transformers==4.35.2
```

---

## 16. Défis et Solutions

### Challenge 1: Reddit API Rate Limits

**Problem**: 60 requests/minute, need to fetch 195 countries  
**Initial Approach**: Sequential fetching → 195 requests → 3+ minutes  
**Solution**:
- Parallel fetching (10 workers) → 10x faster
- Batch processing (30 countries at a time)
- 0.5s delay between requests → avoid 429 errors
- Circular rotation → fair distribution

**Result**: Can fetch 30 countries in ~15-30 seconds

### Challenge 2: Non-English Content

**Problem**: 50%+ of Reddit posts in non-English languages  
**Initial Approach**: Filter out non-English → lost 50% data  
**Solution**:
- Added language detection (langdetect)
- Integrated Google Translate (deep_translator)
- Chunked translation for long text
- Graceful fallback on errors

**Result**: Process all languages, translate to English for ML

### Challenge 3: Event Duplication

**Problem**: Similar posts creating multiple events  
**Initial Approach**: Simple keyword matching → inaccurate  
**Solution**:
- TF-IDF vectorization → semantic similarity
- DBSCAN clustering → auto-detects groups
- Lenient threshold (eps=0.75) → related topics cluster
- Individual posts preserved → no data loss

**Result**: High-quality event grouping with no false negatives

### Défi 4: Mémoire du Modèle ML

**Problème**: RoBERTa + BART + CLIP = 8GB RAM  
**Approche Initiale**: Charger tous les modèles → mémoire insuffisante  
**Solution**:
- Suppression de BART (pas nécessaire)
- Suppression de CLIP (focus texte uniquement)
- Inférence CPU au lieu de GPU
- Modèle RoBERTa unique → 500MB

**Résultat**: Le système fonctionne sur 2GB RAM

### Défi 5: Orchestration du Pipeline

**Problème**: Coordination manuelle de 6 services → sujette aux erreurs  
**Approche Initiale**: Appels API manuels → fastidieux  
**Solution**:
- Thread de traitement en arrière-plan dans la Passerelle API
- Cycles automatiques de 30 secondes
- Disjoncteurs pour la résilience
- Logique de nouvelle tentative pour les défaillances transitoires

**Résultat**: Pipeline entièrement automatisé et auto-réparateur

### Défi 6: Qualité du Résumé

**Problème**: Première tentative → résumés longs et génériques  
**Approche Initiale**: T5 abstractif → modèle 1GB, lent  
**Solution**:
- Résumé extractif (TF-IDF)
- Notation position + contenu + longueur
- Filtrer les phrases génériques (AMA, "Bonjour tout le monde")
- Limites strictes: 2 phrases, 250 caractères

**Résultat**: Résumés rapides, concis et pertinents

---

## 17. Feuille de Route Future

### Phase 1: Évolutivité (T1 2026)

**Objectif**: Gérer 10x plus de données

- [ ] Migration vers PostgreSQL (depuis SQLite)
- [ ] Couche de mise en cache Redis
- [ ] Déploiement Kubernetes
- [ ] Auto-scaling basé sur la charge
- [ ] Réplicas de lecture pour la base de données

**Impact Attendu**:
- 10x débit (500 pays)
- 100x requêtes plus rapides
- 99.9% disponibilité

### Phase 2: ML Amélioré (T2 2026)

**Objectif**: Meilleure précision des émotions

- [ ] Affiner RoBERTa sur les données du domaine
- [ ] Ajouter la détection de tendances de sentiment
- [ ] Implémenter la modélisation de sujets (LDA)
- [ ] Corrélation d'émotions entre pays
- [ ] Prévision de séries temporelles d'émotions

**Impact Attendu**:
- 95% de précision des émotions (contre 90%)
- Insights prédictifs
- Détection de tendances

### Phase 3: Données Multi-Sources (T3 2026)

**Objectif**: Au-delà de Reddit

- [ ] Intégration Twitter/X
- [ ] Intégration API d'actualités
- [ ] Traitement de flux RSS
- [ ] Analyse de commentaires YouTube

**Impact Attendu**:
- 5x plus de sources de données
- Meilleure couverture mondiale
- Insights plus riches

### Phase 4: Fonctionnalités Avancées (T4 2026)

**Objectif**: Fonctionnalités entreprise

- [ ] Authentification utilisateur (JWT)
- [ ] Tableaux de bord personnalisés
- [ ] Alertes email sur les pics d'émotions
- [ ] Export de données (CSV, JSON)
- [ ] Analyse de tendances historiques
- [ ] Limitation de débit API

**Impact Attendu**:
- Prêt pour l'entreprise
- Potentiel de revenus

---

## 18. Métriques et Résultats

### Performance du Système

| Métrique | Valeur | Cible | Statut |
|--------|-------|--------|--------|
| **Disponibilité** | 99.5% | 99.9% | 🟡 Bon |
| **Temps de Réponse API** | <200ms | <500ms | ✅ Excellent |
| **Latence du Pipeline** | 75s moy | <120s | ✅ Excellent |
| **Taux d'Erreur** | 0.1% | <1% | ✅ Excellent |
| **Taille de la Base de Données** | 100MB/semaine | <500MB/semaine | ✅ Excellent |

### Qualité des Données

| Métrique | Valeur | Notes |
|--------|-------|-------|
| **Pays Couverts** | 195+ | Tous les pays de l'ONU |
| **Publications Traitées** | ~1,000/jour | Varie selon le pays |
| **Événements Créés** | ~200/jour | Après clustering |
| **Précision de Traduction** | 95%+ | Google Translate |
| **Précision des Émotions** | ~90% | Base RoBERTa |
| **Qualité du Résumé** | Élevée | Révision manuelle |

### Efficacité des Coûts

| Composant | Coût/Mois | Optimisation |
|-----------|------------|--------------|
| **Serveur (4GB RAM)** | $20 | VPS, pas de majoration cloud |
| **Base de Données** | $0 | SQLite (inclus) |
| **Inférence ML** | $0 | CPU (pas de GPU nécessaire) |
| **API de Traduction** | $10 | Uniquement non-anglais |
| **Surveillance** | $0 | Logs auto-hébergés |
| **Total** | **$30** | Très rentable |

**Alternative Cloud**: AWS/GCP → $200-500/mois  
**Économies**: Réduction de coût de 85%

### Engagement Utilisateur (Frontend)

| Métrique | Valeur | Notes |
|--------|-------|-------|
| **Temps de Chargement de Page** | <2s | Optimisation Next.js |
| **Carte Interactive** | Fluide | Performance Leaflet |
| **Fraîcheur des Données** | 30s | Rafraîchissement auto |
| **Pays Affichés** | 195+ | Couverture complète |

---

## Conclusion

### Réalisations Clés

✅ **Système Prêt pour la Production**: Fonctionne 24h/24 et 7j/7 avec 99,5% de disponibilité  
✅ **Couverture Mondiale**: 195+ pays surveillés équitablement  
✅ **Traitement en Temps Réel**: Cycles de rafraîchissement de 30 secondes  
✅ **Haute Précision**: Classification des émotions à 90%  
✅ **Rentable**: Coût d'exploitation de $30/mois  
✅ **Architecture Évolutive**: Conception en microservices prête à s'étendre  
✅ **Conception Résiliente**: Disjoncteurs, nouvelles tentatives, replis

### Points Forts Techniques

🏆 **Architecture Microservices**: 6 services indépendants, faiblement couplés  
🏆 **Intégration ML**: Transformateur RoBERTa pour la détection des émotions  
🏆 **Traduction Automatisée**: Prend en charge toutes les langues de manière transparente  
🏆 **Extraction d'Événements**: Clustering DBSCAN + résumé extractif  
🏆 **Gestion des Erreurs**: Disjoncteurs, nouvelles tentatives, dégradation gracieuse  
🏆 **Surveillance**: Suivi d'erreurs Sentry, métriques Prometheus

### Leçons Apprises

1. **Commencer Simple**: SQLite suffit, ne pas sur-concevoir  
2. **La Résilience Compte**: Les disjoncteurs nous ont sauvés des défaillances en cascade  
3. **Profiler Avant d'Optimiser**: Workers parallèles gain de performance 10x  
4. **La Gestion des Erreurs est Critique**: La logique de nouvelle tentative gère 90% des problèmes transitoires  
5. **La Documentation est un Investissement**: Économisé des semaines en temps d'intégration

### Prochaines Étapes

1. Déployer en environnement de production
2. Configurer les tableaux de bord de surveillance (Grafana)
3. Implémenter les sauvegardes automatisées
4. Ajouter l'authentification utilisateur
5. Étendre à plus de sources de données

---

## Questions?

**Dépôt du Projet**: [Lien GitHub]  
**Démo en Direct**: [URL de Démo]  
**Documentation**: [URL de Documentation]  
**Contact**: [Email/Slack]

---

**Merci de votre attention!**

*Présentation préparée par [Votre Nom]*  
*16 décembre 2025*
