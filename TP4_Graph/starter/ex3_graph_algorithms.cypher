// TP4 - Exercice 3 : Algorithmes de Graphe avec GDS
// Prérequis : Plugin Graph Data Science installé (inclus dans docker-compose)


// ─── 3.1 : Plus court chemin ──────────────────────────────────────────────────
// "Comment Ahmed peut-il rencontrer Yasmina ?"
MATCH p = shortestPath(
  (a:Etudiant {prenom: "Ahmed"})-[:CONNAIT*..10]-(b:Etudiant {prenom: "Yasmina"})
)
RETURN [n IN nodes(p) | n.prenom + " (" + n.universite + ")"] AS chemin,
       length(p) AS nb_intermediaires;


// ─── 3.2 : Centralité de degré ────────────────────────────────────────────────
// Créer la projection du graphe en mémoire
CALL gds.graph.project(
  'reseau_social',
  'Etudiant',
  'CONNAIT'
);

// Top 10 étudiants les plus connectés
CALL gds.degree.stream('reseau_social')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).prenom AS etudiant,
       gds.util.asNode(nodeId).universite AS universite,
       score AS nb_connexions
ORDER BY nb_connexions DESC
LIMIT 10;


// ─── 3.3 : Détection de communautés (Louvain) ────────────────────────────────
// Exécuter Louvain
CALL gds.louvain.stream('reseau_social')
YIELD nodeId, communityId
WITH communityId, collect(gds.util.asNode(nodeId).prenom) AS membres
RETURN communityId,
       size(membres) AS taille,
       membres[0..5] AS exemple_membres
ORDER BY taille DESC;


// ─── 3.4 : Recommandation de contacts ────────────────────────────────────────
// Score = amis communs * 3 + cours communs * 2 + même filière ? 1

MATCH (moi:Etudiant {prenom: "Ahmed"})
MATCH (autre:Etudiant)
WHERE moi <> autre
AND NOT (moi)-[:CONNAIT]-(autre)

// amis en commun
OPTIONAL MATCH (moi)-[:CONNAIT]-(ami:Etudiant)-[:CONNAIT]-(autre)
WITH moi, autre, count(DISTINCT ami) AS amis_communs

// cours communs
OPTIONAL MATCH (moi)-[:SUIT]->(c:Cours)<-[:SUIT]-(autre)
WITH moi, autre, amis_communs, count(DISTINCT c) AS cours_communs

// même filière
WITH moi, autre, amis_communs, cours_communs,
     CASE WHEN moi.filiere = autre.filiere THEN 1 ELSE 0 END AS meme_filiere

WITH autre,
     (amis_communs * 3 + cours_communs * 2 + meme_filiere) AS score
RETURN autre.prenom AS suggestion, score
ORDER BY score DESC
LIMIT 5;


// ─── 3.5 : Chemin de compétences ─────────────────────────────────────────────
// "Quels cours mènent à Machine Learning ?"
MATCH path = (debut:Cours)-[:REQUIERT*]->(but:Competence {nom: "Machine Learning"})
RETURN [n IN nodes(path) |
  CASE
    WHEN n:Cours THEN n.intitule
    ELSE n.nom
  END
] AS parcours_apprentissage;


// Nettoyage
CALL gds.graph.drop('reseau_social');
