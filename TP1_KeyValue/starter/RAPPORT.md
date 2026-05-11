# RAPPORT.md — TP1 Redis : Système de Cache ShopFast

---

## 1. Comparaison de performance : Cache HIT vs MISS

### Méthodologie
Le benchmark a été réalisé via la fonction `benchmark_cache()` (ex3_cache.py).
Le premier appel est toujours un **MISS** (clé absente dans Redis → requête simulée vers PostgreSQL).
Les appels suivants sont des **HITs** (données déjà présentes dans Redis).

### Résultats obtenus

| Métrique | Cache MISS | Cache HIT |
|---|---|---|
| Latence moyenne | ~2000 ms | ~0.3 ms |
| Cause | Requête PostgreSQL simulée (sleep 2s) | Lecture mémoire Redis |
| Gain | / | **×6000 plus rapide** |

### Interprétation

Avec un taux de hit de 90% (réaliste après warm-up), la majorité des utilisateurs
reçoivent leur page produit en moins d'1ms au lieu de 2 secondes.
La base PostgreSQL reçoit 10× moins de requêtes, ce qui résout directement
le problème de surcharge décrit dans le contexte ShopFast.

---

## 2. Justification des choix de modélisation

### Ex1 : Structures de données

| Donnée | Structure choisie | Pourquoi |
|---|---|---|
| Produit | **Hash** | Accès par champ (`HGET price`), mise à jour partielle sans réécrire tout l'objet |
| Panier | **Hash** | Mapping naturel `product_id → quantité`, `HINCRBY` est atomique |
| Historique de navigation | **List** | Ordre chronologique garanti, `LPUSH + LTRIM` = fenêtre glissante en O(1) |
| Produits par catégorie | **Set** | Unicité automatique, `SINTER` pour trouver les produits multi-catégories |
| Classement des ventes | **Sorted Set** | Score = nombre de ventes, `ZREVRANGE` et `ZREVRANK` en O(log N) |

### Ex2 : Sessions (Sliding Expiration)

Le TTL est renouvelé à chaque appel de `get_session()` via `EXPIRE`.
Cela garantit que seuls les utilisateurs **inactifs** pendant exactement 30 minutes
sont déconnectés. Un utilisateur actif ne sera jamais interrompu.

### Ex3 : Cache-Aside

Le pattern Cache-Aside a été choisi plutôt que Write-Through car :
- L'application garde le contrôle total sur l'invalidation (`invalidate_product_cache`)
- Si Redis tombe, le code retombe naturellement sur la base de données
- On ne cache que ce qui est réellement demandé (pas de données inutiles en mémoire)

Les données sont sérialisées en **JSON** (`json.dumps / json.loads`) pour stocker
des objets Python complets dans une clé String Redis.

### Ex4 : Sorted Set pour le classement

`ZINCRBY` est atomique : plusieurs workers peuvent enregistrer des ventes
simultanément sans risque de corruption. Le Sorted Set maintient automatiquement
l'ordre par score, ce qui rend `get_top_products()` instantané même avec
des millions de produits.

---

## 3. Questions de réflexion

### Q1 : Que se passe-t-il si Redis redémarre ?

**Sans persistance :** toutes les données en mémoire sont perdues.
- Les sessions expirent → tous les utilisateurs sont déconnectés
- Le cache est vide → retour au comportement sans cache (pages lentes, surcharge DB)
- Le classement des ventes est remis à zéro

**Avec la configuration `redis.conf` du TP :**
La persistance est activée via deux mécanismes combinés :

- **RDB (snapshots)** : `save 900 1` et `save 300 10` → Redis sauvegarde
  automatiquement sur disque selon l'activité. Perte de données possible
  entre deux snapshots.

- **AOF (Append-Only File)** : `appendonly yes` + `appendfsync everysec` →
  chaque écriture est loggée sur disque toutes les secondes. Perte maximale
  d'1 seconde de données en cas de crash.

Avec RDB + AOF activés, Redis recharge les données au redémarrage.
Le cache se reconstitue rapidement, les sessions sont restaurées,
et le classement des ventes est préservé.

---

### Q2 : Comment gérer la cohérence cache/DB en cas d'accès concurrent ?

Le problème : deux utilisateurs font simultanément un MISS sur le même produit.
Les deux vont en base, les deux écrivent dans Redis → pas de corruption ici,
mais la DB reçoit une double requête inutile (**thundering herd**).

Cas plus critique : un admin met à jour le prix d'un produit en DB,
mais l'ancien prix est toujours dans le cache Redis.

**Solutions :**

1. **Invalidation explicite** (implémentée dans `invalidate_product_cache`) :
   après chaque `UPDATE` en DB, on supprime la clé Redis.
   Le prochain appel rechargera les données fraîches.
   L'ordre recommandé est : `UPDATE DB → DELETE cache` (jamais SET directement).

2. **TTL court** : même sans invalidation manuelle, le cache expire automatiquement.
   Le TTL de 600s (10 min) dans `get_product_cached` limite la durée d'exposition
   à des données périmées.

3. **Cache Lock (avancé)** : avant d'aller en DB lors d'un MISS,
   poser un verrou Redis (`SET lock:pid 1 NX EX 5`) pour qu'un seul worker
   effectue la requête. Les autres attendent ou retournent les données périmées.

---

### Q3 : Quand un TTL trop court est-il problématique ?

Un TTL trop court fait que les clés expirent avant d'être réutilisées,
ce qui annule le bénéfice du cache.

**Conséquences concrètes pour ShopFast :**

| Problème | Impact |
|---|---|
| Taux de hit proche de 0% | Chaque requête repart en PostgreSQL → pages lentes |
| Surcharge de la base | On retrouve le problème initial des 3-4 secondes de chargement |
| Thundering herd | Lors d'une mise en avant produit (flash sale), des milliers d'utilisateurs font un MISS simultané |

**Exemple concret :**
Si TTL = 5 secondes et qu'un produit est consulté toutes les 10 secondes,
le cache est toujours expiré avant le prochain accès → 0% de hit rate,
pire qu'un système sans cache (overhead de Redis en plus).

**Règle pratique :**
Le TTL doit être supérieur au temps moyen entre deux accès à la même clé.
Pour ShopFast :
- Produits populaires (page d'accueil) → TTL 10-30 minutes
- Pages de recherche → TTL 1-2 minutes (résultats changent plus souvent)
- Sessions utilisateur → TTL 30 minutes avec sliding expiration
