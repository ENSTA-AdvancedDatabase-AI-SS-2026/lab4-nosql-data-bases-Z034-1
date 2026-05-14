/**
 * TP2 - Exercice 4 : Index et Optimisation
 */

use("medical_db");

// ─── 4.1 : Créer les index appropriés ────────────────────────────────────────

// Index 1 : Recherche fréquente par wilaya + antécédents
// Optimise les requêtes filtrant par wilaya et pathologie
db.patients.createIndex({
  "adresse.wilaya": 1,
  antecedents: 1
});

// Index 2 : Recherche par date de consultation
// Optimise les recherches chronologiques sur consultations
db.patients.createIndex({
  "consultations.date": -1
});

// Index 3 : Texte sur diagnostics pour recherche full-text
// Permet la recherche textuelle avec $text
db.patients.createIndex({
  "consultations.diagnostic": "text"
});

// Index 4 : Analyses par patient (lookup)
// Optimise les jointures via patient_id
db.analyses.createIndex({
  patient_id: 1
});


// ─── 4.2 : Comparer avec explain() ────────────────────────────────────────────

// Requête de test
const requeteTest = {
  "adresse.wilaya": "Alger",
  antecedents: "Diabète type 2"
};

print("=== AVANT index ===");

// Suppression temporaire de l'index pour test
db.patients.dropIndex({
  "adresse.wilaya": 1,
  antecedents: 1
});

const avantIndex = db.patients.find(requeteTest)
  .explain("executionStats");

print("Documents retournés :",
  avantIndex.executionStats.nReturned);

print("Documents examinés :",
  avantIndex.executionStats.totalDocsExamined);

print("Temps exécution (ms) :",
  avantIndex.executionStats.executionTimeMillis);


// Recréation index
db.patients.createIndex({
  "adresse.wilaya": 1,
  antecedents: 1
});


print("\n=== APRÈS index ===");

const apresIndex = db.patients.find(requeteTest)
  .explain("executionStats");

print("Documents retournés :",
  apresIndex.executionStats.nReturned);

print("Documents examinés :",
  apresIndex.executionStats.totalDocsExamined);

print("Temps exécution (ms) :",
  apresIndex.executionStats.executionTimeMillis);


// ─── 4.3 : Index composé complexe ────────────────────────────────────────────

// Requête complexe : wilaya + diagnostic + date consultation
// L'ordre est important :
// 1. wilaya → filtre le plus fréquent
// 2. diagnostic → second filtre
// 3. date → tri/recherche chronologique

db.patients.createIndex({

  "adresse.wilaya": 1,

  "consultations.diagnostic": 1,

  "consultations.date": -1
});


// ─── 4.4 : Index TTL pour archivage ───────────────────────────────────────────

// 5 ans = 5 * 365 * 24 * 60 * 60
db.analyses.createIndex(

  { date: 1 },

  {
    expireAfterSeconds: 157680000
  }
);

print("\n✅ Index créés avec succès");
