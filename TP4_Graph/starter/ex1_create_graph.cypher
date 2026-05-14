// TP4 - Exercice 1 : Création du graphe UniConnect DZ

// Effacer la base pour partir propre
MATCH (n) DETACH DELETE n;

// ─── 1.1 : Contraintes d'unicité ─────────────────────────────────────────────
CREATE CONSTRAINT etudiant_id IF NOT EXISTS FOR (e:Etudiant) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT cours_code IF NOT EXISTS FOR (c:Cours) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT competence_nom IF NOT EXISTS FOR (c:Competence) REQUIRE c.nom IS UNIQUE;


// ─── 1.2 : Créer les compétences ──────────────────────────────────────────────
UNWIND [
  {nom: "Python", categorie: "Programmation"},
  {nom: "Java", categorie: "Programmation"},
  {nom: "SQL", categorie: "Bases de Données"},
  {nom: "NoSQL", categorie: "Bases de Données"},
  {nom: "Machine Learning", categorie: "IA"},
  {nom: "Deep Learning", categorie: "IA"},
  {nom: "React", categorie: "Web"},
  {nom: "Docker", categorie: "DevOps"},
  {nom: "Linux", categorie: "Systèmes"},
  {nom: "Réseaux", categorie: "Infrastructure"}
] AS comp
MERGE (:Competence {nom: comp.nom, categorie: comp.categorie});


// ─── 1.3 : Créer les cours ────────────────────────────────────────────────────
UNWIND [
  {code: "INFO401", intitule: "Bases de Données Avancées", credits: 6, dept: "Informatique"},
  {code: "INFO402", intitule: "Intelligence Artificielle", credits: 6, dept: "Informatique"},
  {code: "INFO403", intitule: "Développement Web", credits: 4, dept: "Informatique"},
  {code: "INFO404", intitule: "Systèmes Distribués", credits: 5, dept: "Informatique"},
  {code: "INFO405", intitule: "Cloud Computing", credits: 4, dept: "Informatique"}
] AS cours
MERGE (:Cours {
  code: cours.code,
  intitule: cours.intitule,
  credits: cours.credits,
  departement: cours.dept
});


// ─── 1.4 : Créer les étudiants ────────────────────────────────────────────────
UNWIND [
  {id: "E001", prenom: "Ahmed", nom: "Bensalem", universite: "USTHB",
   filiere: "Informatique", annee: 3, ville: "Alger"},
  {id: "E002", prenom: "Fatima", nom: "Ouali", universite: "USTHB",
   filiere: "Informatique", annee: 3, ville: "Alger"},
  {id: "E003", prenom: "Yacine", nom: "Meziane", universite: "USTHB",
   filiere: "Mathématiques", annee: 2, ville: "Alger"},
  {id: "E004", prenom: "Sara", nom: "Kaci", universite: "UMBB",
   filiere: "Informatique", annee: 3, ville: "Boumerdes"},
  {id: "E005", prenom: "Omar", nom: "Haddad", universite: "USTO",
   filiere: "GL", annee: 4, ville: "Oran"},
  {id: "E006", prenom: "Lina", nom: "Bouzid", universite: "UMC",
   filiere: "Télécoms", annee: 2, ville: "Constantine"},
  {id: "E007", prenom: "Rami", nom: "Djeradi", universite: "UBMA",
   filiere: "Informatique", annee: 3, ville: "Annaba"},
  {id: "E008", prenom: "Nour", nom: "Sahli", universite: "USTHB",
   filiere: "Informatique", annee: 1, ville: "Alger"},
  {id: "E009", prenom: "Imane", nom: "Benali", universite: "UMBB",
   filiere: "Mathématiques", annee: 3, ville: "Boumerdes"},
  {id: "E010", prenom: "Karim", nom: "Ait Ali", universite: "USTO",
   filiere: "Informatique", annee: 2, ville: "Oran"}
  // (TP NOTE: répéter le pattern jusqu’à E050 dans un vrai rendu)
] AS data
MERGE (e:Etudiant {id: data.id})
SET e += data;


// ─── 1.5 : Créer les relations ────────────────────────────────────────────────

// CONNAIT (relations sociales)
MATCH (a:Etudiant), (b:Etudiant)
WHERE a.id <> b.id AND rand() < 0.08
MERGE (a)-[:CONNAIT {depuis: 2023, contexte: "cours"}]->(b);


// SUIT (cours)
MATCH (e:Etudiant), (c:Cours)
WHERE rand() < 0.6
MERGE (e)-[:SUIT {semestre: 2, note: toInteger(10 + rand()*10)}]->(c);


// MAITRISE (compétences)
MATCH (e:Etudiant), (comp:Competence)
WHERE rand() < 0.5
MERGE (e)-[:MAITRISE {niveau: toInteger(1 + rand()*5)}]->(comp);


// MEMBRE_DE (clubs fictifs)
MERGE (:Club {nom: "Club IA USTHB", universite: "USTHB", domaine: "IA"});
MERGE (:Club {nom: "Google DSC", universite: "USTHB", domaine: "Tech"});
MERGE (:Club {nom: "Robotics Club", universite: "USTO", domaine: "Robotique"});

MATCH (e:Etudiant), (c:Club)
WHERE rand() < 0.3
MERGE (e)-[:MEMBRE_DE {role: "member"}]->(c);


// Vérification
MATCH (n)
RETURN labels(n)[0] AS type, count(n) AS total
ORDER BY total DESC;

MATCH ()-[r]->()
RETURN type(r) AS relation, count(r) AS total
ORDER BY total DESC;
