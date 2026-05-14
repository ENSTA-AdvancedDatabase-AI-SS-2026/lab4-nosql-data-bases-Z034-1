/**
 * TP2 - Exercice 3 : Pipelines d'Agrégation
 * Use Case : Statistiques médicales HealthCare DZ
 */

use("medical_db");

// ─── 3.1 : Distribution des diagnostics par wilaya ────────────────────────────
print("=== 3.1 : Top diagnostics par wilaya ===");

const diagParWilaya = db.patients.aggregate([

  // Étape 1 - Dérouler consultations
  {
    $unwind: "$consultations"
  },

  // Étape 2 - Grouper par wilaya + diagnostic
  {
    $group: {

      _id: {
        wilaya: "$adresse.wilaya",
        diagnostic: "$consultations.diagnostic"
      },

      count: {
        $sum: 1
      }
    }
  },

  // Étape 3 - Trier
  {
    $sort: {
      count: -1
    }
  },

  // Étape 4 - Limiter
  {
    $limit: 20
  }
]).toArray();

// printjson(diagParWilaya);


// ─── 3.2 : Médicament le plus prescrit par spécialité ─────────────────────────
print("\n=== 3.2 : Top médicaments par spécialité ===");

const medsParSpecialite = db.patients.aggregate([

  // Dérouler consultations
  {
    $unwind: "$consultations"
  },

  // Dérouler médicaments
  {
    $unwind: "$consultations.medicaments"
  },

  // Grouper par spécialité + médicament
  {
    $group: {

      _id: {
        specialite: "$consultations.medecin.specialite",
        medicament: "$consultations.medicaments.nom"
      },

      total: {
        $sum: 1
      }
    }
  },

  // Trier
  {
    $sort: {
      "_id.specialite": 1,
      total: -1
    }
  },

  // Garder top 1 par spécialité
  {
    $group: {

      _id: "$_id.specialite",

      medicamentPlusPrescrit: {
        $first: "$_id.medicament"
      },

      nombrePrescriptions: {
        $first: "$total"
      }
    }
  }
]).toArray();


// ─── 3.3 : Évolution mensuelle des consultations ──────────────────────────────
print("\n=== 3.3 : Consultations par mois (12 derniers mois) ===");

const evolutionMensuelle = db.patients.aggregate([

  {
    $unwind: "$consultations"
  },

  {
    $match: {
      "consultations.date": {
        $gte: new Date(
          new Date().setFullYear(
            new Date().getFullYear() - 1
          )
        )
      }
    }
  },

  // Grouper par année + mois
  {
    $group: {

      _id: {

        annee: {
          $year: "$consultations.date"
        },

        mois: {
          $month: "$consultations.date"
        }
      },

      totalConsultations: {
        $sum: 1
      }
    }
  },

  // Trier
  {
    $sort: {
      "_id.annee": 1,
      "_id.mois": 1
    }
  },

  // Formatter YYYY-MM
  {
    $project: {

      _id: 0,

      mois: {
        $concat: [
          { $toString: "$_id.annee" },
          "-",
          {
            $cond: [
              { $lt: ["$_id.mois", 10] },
              {
                $concat: [
                  "0",
                  { $toString: "$_id.mois" }
                ]
              },
              { $toString: "$_id.mois" }
            ]
          }
        ]
      },

      totalConsultations: 1
    }
  }
]).toArray();


// ─── 3.4 : Patients à risque multiple ────────────────────────────────────────
print("\n=== 3.4 : Profil patients à risque élevé ===");

const patientsRisque = db.patients.aggregate([

  {
    $match: {

      antecedents: {
        $all: ["Diabète type 2", "HTA"]
      },

      dateNaissance: {
        $lte: new Date(
          new Date().getFullYear() - 60,
          0,
          1
        )
      }
    }
  },

  // Calcul âge + nb consultations
  {
    $addFields: {

      age: {
        $subtract: [
          new Date().getFullYear(),
          { $year: "$dateNaissance" }
        ]
      },

      nbConsultations: {
        $size: "$consultations"
      }
    }
  },

  // Statistiques globales
  {
    $group: {

      _id: null,

      nombrePatients: {
        $sum: 1
      },

      moyenneConsultations: {
        $avg: "$nbConsultations"
      },

      ageMoyen: {
        $avg: "$age"
      }
    }
  }
]).toArray();


// ─── 3.5 : Rapport médecins ───────────────────────────────────────────────────
print("\n=== 3.5 : Top 5 médecins & taux de ré-consultation ===");

const rapportMedecins = db.patients.aggregate([

  {
    $unwind: "$consultations"
  },

  // Grouper par médecin
  {
    $group: {

      _id: "$consultations.medecin.nom",

      totalConsultations: {
        $sum: 1
      },

      patientsUniques: {
        $addToSet: "$_id"
      }
    }
  },

  // Calculs
  {
    $addFields: {

      nbPatientsUniques: {
        $size: "$patientsUniques"
      },

      tauxReconsultation: {

        $multiply: [

          {
            $divide: [

              {
                $subtract: [
                  "$totalConsultations",
                  { $size: "$patientsUniques" }
                ]
              },

              { $size: "$patientsUniques" }
            ]
          },

          100
        ]
      }
    }
  },

  // Trier
  {
    $sort: {
      totalConsultations: -1
    }
  },

  // Top 5
  {
    $limit: 5
  }
]).toArray();

printjson(rapportMedecins);
