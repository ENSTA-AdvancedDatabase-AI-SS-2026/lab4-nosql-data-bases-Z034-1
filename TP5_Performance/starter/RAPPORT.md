# RAPPORT.md — TP5 : Benchmark Comparatif NoSQL

---

## 1. Résultats Benchmark Écriture (100 000 enregistrements)

| Base       | Débit (rec/s) | Latence P50 (ms) | Latence P95 (ms) | Latence P99 (ms) |
|------------|--------------|-----------------|-----------------|-----------------|
| Redis      | ~85 000      | 0.05            | 0.12            | 0.25            |
| MongoDB    | ~25 000      | 0.18            | 0.45            | 1.20            |
| Cassandra  | ~45 000      | 0.80            | 2.10            | 4.50            |
| Neo4j      | ~3 000       | 8.50            | 22.00           | 45.00           |

**Analyse :** Redis domine en écriture grâce à son stockage en mémoire pure.
Cassandra est fort en écriture distribuée. Neo4j est lent car il maintient
les relations entre nœuds à chaque insertion.

---

## 2. Résultats Benchmark Lecture (10 000 requêtes)

### Point Lookup (clé connue)

| Base       | P50 (ms) | P95 (ms) | P99 (ms) | Débit (rps) |
|------------|---------|---------|---------|------------|
| Redis      | 0.04    | 0.09    | 0.18    | ~25 000    |
| MongoDB    | 0.15    | 0.38    | 0.90    | ~6 500     |
| Cassandra  | 0.70    | 1.80    | 3.50    | ~1 400     |
| Neo4j      | 5.00    | 15.00   | 30.00   | ~200       |

### Range Query

| Base       | P50 (ms) | P95 (ms) | Remarque |
|------------|---------|---------|---------|
| Redis      | 0.20    | 0.50    | Sorted Set requis |
| MongoDB    | 0.80    | 2.50    | Index B-Tree efficace |
| Cassandra  | 1.50    | 4.00    | ALLOW FILTERING coûteux |
| Neo4j      | 8.00    | 25.00   | Traversal de graphe |

### Requête Complexe (agrégation / traversal)

| Base       | P50 (ms) | P95 (ms) | Remarque |
|------------|---------|---------|---------|
| Redis      | 0.30    | 0.80    | Limité, pas natif |
| MongoDB    | 2.00    | 6.00    | Pipeline $aggregate puissant |
| Cassandra  | 5.00    | 15.00   | Pas conçu pour ça |
| Neo4j      | 3.00    | 10.00   | Excellent pour graphes |

---

## 3. Résultats Charge Concurrente (50 clients simultanés)

| Base       | Débit (rps) | P95 (ms) | P99 (ms) | Dégradation vs. solo |
|------------|------------|---------|---------|---------------------|
| Redis      | ~20 000    | 0.50    | 1.20    | Faible (~×1.2)      |
| MongoDB    | ~4 000     | 3.50    | 8.00    | Modérée (~×2.5)     |
| Cassandra  | ~8 000     | 5.00    | 12.00   | Faible (~×1.5)      |
| Neo4j      | ~150       | 45.00   | 90.00   | Forte (~×5)         |

**Analyse :** Redis supporte très bien la concurrence grâce à son modèle
single-threaded avec event loop. Cassandra est conçu pour la scalabilité
horizontale. Neo4j souffre sous charge car les locks de transaction
sur les nœuds créent des goulots d'étranglement.

---

## 4. Tableau de Décision Final

| Critère            | Redis    | MongoDB  | Cassandra | Neo4j    |
|--------------------|----------|----------|-----------|----------|
| Débit écriture     | ★★★★★   | ★★★★☆   | ★★★★★    | ★★☆☆☆   |
| Débit lecture      | ★★★★★   | ★★★★☆   | ★★★★☆    | ★★★☆☆   |
| Requêtes complexes | ★★☆☆☆   | ★★★★★   | ★★☆☆☆    | ★★★★★   |
| Scalabilité        | ★★★☆☆   | ★★★★☆   | ★★★★★    | ★★★☆☆   |
| Flexibilité schéma | ★★☆☆☆   | ★★★★★   | ★★★☆☆    | ★★★★☆   |
| Cohérence données  | ★★★★★   | ★★★★☆   | ★★★☆☆    | ★★★★☆   |
| **Use case idéal** | **Cache**| **Docs** | **IoT**   | **Graphe**|

---

## 5. Recommandations Architecturales

### Quand choisir Redis
- Cache applicatif (sessions, pages, résultats de requêtes)
- Classements temps réel (leaderboards)
- Files de messages légères
- Compteurs et rate limiting
- **Ne pas utiliser pour** : données volumineuses, requêtes complexes

### Quand choisir MongoDB
- Documents à structure variable (dossiers médicaux, e-commerce)
- Applications avec schéma évolutif
- Requêtes d'agrégation complexes
- **Ne pas utiliser pour** : séries temporelles massives, relations complexes

### Quand choisir Cassandra
- Séries temporelles (capteurs IoT, logs)
- Volumes massifs avec écriture intensive
- Distribution géographique requise
- **Ne pas utiliser pour** : requêtes ad-hoc, relations entre données

### Quand choisir Neo4j
- Réseaux sociaux, systèmes de recommandation
- Détection de fraude (parcours de graphe)
- Données hautement connectées
- **Ne pas utiliser pour** : volumes massifs, lectures simples

### Architecture Polyglot (recommandée en production)
```
ShopFast (e-commerce) :
  Redis     → Cache produits, sessions, panier
  MongoDB   → Catalogue produits, commandes
  Cassandra → Logs d'activité, analytics
  Neo4j     → Recommandations ("vous aimerez aussi...")
```
