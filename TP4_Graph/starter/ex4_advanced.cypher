
// TP4 - Exercice 4 : Requêtes Avancées

USE smartconnect;


// ─────────────────────────────────────────────
// 4.1 Trouver un tuteur
// "Master + Python + note > 14 en BDD"
// ─────────────────────────────────────────────

MATCH (tuteur:Etudiant)-[:SUIT]->(c:Cours {code: "INFO401"})
WHERE tuteur.annee >= 4

MATCH (tuteur)-[:MAITRISE]->(comp:Competence {nom: "Python"})
MATCH (tuteur)-[s:SUIT]->(c2:Cours {code: "INFO401"})
WHERE s.note > 14

RETURN tuteur.prenom AS tuteur,
       tuteur.universite AS universite,
       s.note AS note_BDD
ORDER BY s.note DESC;


// ─────────────────────────────────────────────
// 4.2 Réseau alumni dans une entreprise
// "Qui travaille chez Sonatrach dans mon réseau (≤3 sauts)"
// ─────────────────────────────────────────────

MATCH (moi:Etudiant {prenom: "Ahmed"})-[:CONNAIT*1..3]-(alumni:Etudiant)
MATCH (alumni)-[:A_STAGE_CHEZ|A_TRAVAILLE_CHEZ]->(e:Entreprise {nom: "Sonatrach"})
RETURN DISTINCT alumni.prenom AS personne,
       length(shortestPath((moi)-[:CONNAIT*]-(alumni))) AS distance;


// ─────────────────────────────────────────────
// 4.3 Détection de ponts (bridge nodes)
// Étudiants connectant plusieurs communautés
// ─────────────────────────────────────────────

MATCH (e:Etudiant)-[:CONNAIT]-(n:Etudiant)
WITH e, count(DISTINCT n) AS degre
WHERE degre > 5
MATCH (e)-[:CONNAIT]-(c:Etudiant)
WITH e, collect(DISTINCT c.universite) AS univ_distinctes
WHERE size(univ_distinctes) > 1
RETURN e.prenom AS pont,
       e.universite AS universite,
       size(univ_distinctes) AS nb_universites;


// ─────────────────────────────────────────────
// 4.4 Analyse temporelle
// Croissance du réseau par année
// ─────────────────────────────────────────────

MATCH (:Etudiant)-[r:CONNAIT]->(:Etudiant)
RETURN r.depuis AS annee,
       count(r) AS nouvelles_connexions
ORDER BY annee;


// ─────────────────────────────────────────────
// 4.5 Score de similarité (Jaccard)
// Étudiants similaires à Ahmed
// ─────────────────────────────────────────────

MATCH (a:Etudiant {prenom: "Ahmed"})
MATCH (e:Etudiant)
WHERE a <> e

OPTIONAL MATCH (a)-[:SUIT]->(c:Cours)<-[:SUIT]-(e)
WITH a, e, collect(DISTINCT c) AS cours_communs

OPTIONAL MATCH (a)-[:MAITRISE]->(k:Competence)<-[:MAITRISE]-(e)
WITH a, e, cours_communs, collect(DISTINCT k) AS comp_communes

WITH e,
     size(cours_communs) AS inter,
     size([(a)-[:SUIT]->(c:Cours) | c]) +
     size([(e)-[:SUIT]->(c:Cours) | c]) AS union_courses,
     size(comp_communes) AS inter_comp,
     size([(a)-[:MAITRISE]->(k:Competence) | k]) +
     size([(e)-[:MAITRISE]->(k:Competence) | k]) AS union_comp

WITH e,
     (toFloat(inter + inter_comp) /
     toFloat(union_courses + union_comp + 0.1)) AS jaccard_score

RETURN e.prenom AS etudiant,
       jaccard_score AS similarite
ORDER BY similarite DESC
LIMIT 10;
