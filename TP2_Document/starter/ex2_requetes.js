/**
 * TP2 - Exercice 2 : Requêtes MongoDB
 * Use Case : HealthCare DZ - Dossiers Médicaux
 */

use("medical_db");

// ─── 2.1 : Trouver tous les patients diabétiques de plus de 50 ans à Alger ───

db.patients.find({

  antecedents: /Diabète/i,

  dateNaissance: {
    $lte: new Date(
      new Date().getFullYear() - 50,
      0,
      1
    )
  },

  "adresse.wilaya": "Alger"
});


// ─── 2.2 : Patients allergiques à la Pénicilline avec au moins 3 consultations ───

db.patients.find({

  allergies: "Pénicilline",

  consultations: {
    $exists: true
  },

  $expr: {
    $gte: [
      { $size: "$consultations" },
      3
    ]
  }
});


// ─── 2.3 : Projection : Nom, prénom, et dernière consultation seulement ──────

db.patients.find(
  {},

  {
    _id: 0,

    nom: 1,
    prenom: 1,

    consultations: {
      $slice: -1
    }
  }
);


// ─── 2.4 : Patients sans antécédents dont la tension systolique > 140 ────────
// en dernière consultation

db.patients.find({

  antecedents: {
    $size: 0
  },

  "consultations.tension.systolique": {
    $gt: 140
  }
});


// ─── 2.5 : Recherche textuelle sur les diagnostics ────────────────────────────

// Création index text
db.patients.createIndex({
  "consultations.diagnostic": "text"
});


// Recherche
db.patients.find({

  $text: {
    $search: "Hypertension"
  }
});
