-- Ex4 — Compaction et Maintenance

USE smartgrid;

-- 4.1 Choix de stratégie de compaction
-- Pour les séries temporelles → TimeWindowCompactionStrategy (TWCS)
-- Avantage : optimise TTL + suppression par fenêtre de temps

-- Pour tables d'agrégats → SizeTieredCompactionStrategy (STCS)
-- Avantage : bon pour écritures classiques

-- =====================================================
-- 4.2 Configuration TWCS pour mesures_par_capteur
-- =====================================================

ALTER TABLE mesures_par_capteur
WITH compaction = {
  'class': 'TimeWindowCompactionStrategy',
  'compaction_window_unit': 'DAYS',
  'compaction_window_size': 1
};


-- =====================================================
-- 4.3 Vérifier l'utilisation des TTL
-- =====================================================

SELECT *
FROM system_views.dropped_columns;

-- alternative (selon version Cassandra)
SELECT *
FROM system.size_estimates
WHERE keyspace_name = 'smartgrid';


-- =====================================================
-- 4.4 Détection d'une partition "hot"
-- =====================================================
-- Une partition hot = trop de writes sur même clé (wilaya, date, capteur_id)

-- Exemple de détection (approximation via compteur)
SELECT capteur_id, COUNT(*)
FROM mesures_par_capteur
WHERE date_jour = ?
GROUP BY capteur_id;

-- Problème :
-- - déséquilibre de charge
-- - saturation d'un nœud
-- - latence élevée

-- Correction :
-- - ajouter une clé de distribution (ex: bucket horaire)
-- - ou modifier partition key (capteur_id + date + heure)
