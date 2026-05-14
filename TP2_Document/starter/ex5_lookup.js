/**
 * TP2 - Exercice 5 : $lookup et Données Référencées
 */

use("medical_db");

// ─── 5.1 : Joindre patients et analyses ──────────────────────────────────────
// Récupérer le dossier complet d’un patient

const dossierComplet = db.patients.aggregate([

  {
    $lookup: {

      from: "analyses",

      localField: "_id",

      foreignField: "patient_id",

      as: "analysesPatient"
    }
  },

  {
    $project: {

      nom: 1,
      prenom: 1,
      antecedents: 1,
      consultations: 1,
      analysesPatient: 1
    }
  }
]).toArray();

print("=== 5.1 : Dossiers complets ===");
printjson(dossierComplet);


// ─── 5.2 : Patients dont la glycémie dépasse 1.26 g/L ────────────────────────

const patientsGlycemie = db.patients.aggregate([

  {
    $lookup: {

      from: "analyses",

      localField: "_id",

      foreignField: "patient_id",

      as: "analyses"
    }
  },

  {
    $unwind: "$analyses"
  },

  {
    $match: {

      "analyses.type": "Glycémie",

      "analyses.resultats.glycemie": {
        $gt: 1.26
      }
    }
  },

  {
    $project: {

      _id: 0,

      nom: 1,
      prenom: 1,

      glycemie: "$analyses.resultats.glycemie",

      laboratoire: "$analyses.laboratoire"
    }
  }
]).toArray();

print("\n=== 5.2 : Patients glycémie élevée ===");
printjson(patientsGlycemie);


// ─── 5.3 : Taux d’analyses anormales par wilaya ──────────────────────────────

const statsAnalyses = db.patients.aggregate([

  {
    $lookup: {

      from: "analyses",

      localField: "_id",

      foreignField: "patient_id",

      as: "analyses"
    }
  },

  {
    $unwind: "$analyses"
  },

  // Détection analyses anormales
  {
    $addFields: {

      analyseAnormale: {

        $cond: [

          {
            $or: [

              {
                $gt: [
                  "$analyses.resultats.glycemie",
                  1.26
                ]
              },

              {
                $gt: [
                  "$analyses.resultats.cholesterol",
                  2
                ]
              }
            ]
          },

          1,
          0
        ]
      }
    }
  },

  // Groupement par wilaya
  {
    $group: {

      _id: "$adresse.wilaya",

      totalAnalyses: {
        $sum: 1
      },

      analysesAnormales: {
        $sum: "$analyseAnormale"
      }
    }
  },

  // Calcul taux %
  {
    $project: {

      wilaya: "$_id",

      totalAnalyses: 1,

      analysesAnormales: 1,

      tauxAnormal: {

        $multiply: [

          {
            $divide: [
              "$analysesAnormales",
              "$totalAnalyses"
            ]
          },

          100
        ]
      }
    }
  },

  {
    $sort: {
      tauxAnormal: -1
    }
  }
]).toArray();

print("\n=== 5.3 : Taux d’analyses anormales par wilaya ===");
printjson(statsAnalyses);
