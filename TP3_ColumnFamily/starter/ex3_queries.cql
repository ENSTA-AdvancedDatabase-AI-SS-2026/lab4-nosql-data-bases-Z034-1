-- Ex3 — Requêtes CQL

USE smartgrid;

-- 3.1 Mesures d'un capteur spécifique sur les dernières 6 heures
SELECT *
FROM mesures_par_capteur
WHERE capteur_id = ?
  AND date_jour = ?
  AND timestamp >= ?
  AND timestamp <= ?;


-- 3.2 Dernière mesure de chaque capteur d'une wilaya
-- (utiliser clustering DESC + LIMIT 1 côté lecture applicative)

SELECT *
FROM mesures_par_wilaya
WHERE wilaya = 'Alger'
  AND date_jour = dateOf(now())
ORDER BY timestamp DESC
LIMIT 1;


-- 3.3 Capteurs en alerte dans la wilaya "Alger" aujourd'hui
SELECT *
FROM alertes_par_wilaya
WHERE wilaya = 'Alger'
  AND date_jour = dateOf(now())
  AND alerte = true;


-- 3.4 Consommation totale par heure sur une journée
SELECT heure, SUM(puissance_kw)
FROM agregats_horaires
WHERE wilaya = 'Alger'
  AND date_jour = dateOf(now())
GROUP BY heure;


-- 3.5 Détection d'anomalie tension (<200V ou >240V)
SELECT capteur_id, timestamp, tension_v
FROM mesures_par_capteur
WHERE capteur_id = ?
  AND date_jour = ?
  AND timestamp >= ?;


-- 3.6 Top 10 capteurs les plus actifs cette semaine
SELECT capteur_id, total_mesures
FROM activite_capteurs_semaine
WHERE semaine = ?
LIMIT 10;


-- 3.7 ALLOW FILTERING
-- Exemple (à éviter)
SELECT *
FROM mesures_par_capteur
WHERE tension_v < 200 ALLOW FILTERING;

-- Problème : scan complet de partition + mauvaise performance
