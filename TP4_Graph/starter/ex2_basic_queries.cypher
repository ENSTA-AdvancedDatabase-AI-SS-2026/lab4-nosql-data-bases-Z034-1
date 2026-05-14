
// Ex2 — Requêtes de base

USE smartconnect; // (optionnel selon config)

// ─────────────────────────────────────────────
// 2.1 Trouver tous les amis d'Ahmed (1 saut)
// ─────────────────────────────────────────────
MATCH (a:Etudiant {prenom: "Ahmed"})-[:CONNAIT]-(ami:Etudiant)
RETURN ami.prenom, ami.nom, ami.universite;


// ─────────────────────────────────────────────
// 2.2 Amis d'amis d'Ahmed (2 sauts)
// exclure ses amis directs
// ─────────────────────────────────────────────
MATCH (a:Etudiant {prenom: "Ahmed"})-[:CONNAIT*2]-(suggestion:Etudiant)
WHERE NOT (a)-[:CONNAIT]-(suggestion)
AND a <> suggestion
RETURN DISTINCT suggestion.prenom, suggestion.nom
LIMIT 10;


// ─────────────────────────────────────────────
// 2.3 Étudiants qui suivent les mêmes cours que Fatima
// mais ne la connaissent pas
// ─────────────────────────────────────────────
MATCH (f:Etudiant {prenom: "Fatima"})-[:SUIT]->(c:Cours)<-[:SUIT]-(e:Etudiant)
WHERE NOT (f)-[:CONNAIT]-(e)
AND f <> e
RETURN DISTINCT e.prenom, e.universite;


// ─────────────────────────────────────────────
// 2.4 Clubs les plus populaires
// (par nombre de membres)
// ─────────────────────────────────────────────
MATCH (e:Etudiant)-[:MEMBRE_DE]->(c:Club)
RETURN c.nom AS club, count(e) AS nb_membres
ORDER BY nb_membres DESC;


// ─────────────────────────────────────────────
// 2.5 Profil complet d’un étudiant
// amis + cours + compétences + clubs
// ─────────────────────────────────────────────
MATCH (e:Etudiant {prenom: "Ahmed"})
OPTIONAL MATCH (e)-[:CONNAIT]-(amis:Etudiant)
OPTIONAL MATCH (e)-[:SUIT]->(cours:Cours)
OPTIONAL MATCH (e)-[:MAITRISE]->(comp:Competence)
OPTIONAL MATCH (e)-[:MEMBRE_DE]->(club:Club)
RETURN e.prenom,
       collect(DISTINCT amis.prenom) AS amis,
       collect(DISTINCT cours.intitule) AS cours,
       collect(DISTINCT comp.nom) AS competences,
       collect(DISTINCT club.nom) AS clubs;
