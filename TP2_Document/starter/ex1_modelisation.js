/**
 * TP2 - Exercice 1 : Modélisation MongoDB
 * Use Case : HealthCare DZ - Dossiers Médicaux
 */

// Se connecter à la base médicale
use("medical_db");

// ─── 1.1 : Créer la collection avec validation ────────────────────────────────
// TODO: Décommenter et compléter le validator $jsonSchema
db.createCollection("patients", {

  validator: {

    $jsonSchema: {

      bsonType: "object",

      required: [
        "cin",
        "nom",
        "prenom",
        "dateNaissance",
        "sexe",
        "adresse"
      ],

      properties: {

        cin: {
          bsonType: "string",
          description: "National ID is required"
        },

        nom: {
          bsonType: "string",
          description: "Last name is required"
        },

        prenom: {
          bsonType: "string",
          description: "First name is required"
        },

        dateNaissance: {
          bsonType: "date",
          description: "Birth date is required"
        },

        sexe: {
          enum: ["M", "F"],
          description: "Must be M or F"
        },

        adresse: {

          bsonType: "object",

          required: ["wilaya", "commune"],

          properties: {

            wilaya: {
              bsonType: "string"
            },

            commune: {
              bsonType: "string"
            }
          }
        },

        groupeSanguin: {
          bsonType: "string"
        },

        antecedents: {

          bsonType: "array",

          items: {
            bsonType: "string"
          }
        },

        allergies: {

          bsonType: "array",

          items: {
            bsonType: "string"
          }
        },

        consultations: {

          bsonType: "array",

          items: {

            bsonType: "object",

            required: [
              "id",
              "date",
              "diagnostic"
            ],

            properties: {

              id: {
                bsonType: "binData"
              },

              date: {
                bsonType: "date"
              },

              diagnostic: {
                bsonType: "string"
              },

              notes: {
                bsonType: "string"
              },

              medecin: {

                bsonType: "object",

                properties: {

                  nom: {
                    bsonType: "string"
                  },

                  specialite: {
                    bsonType: "string"
                  }
                }
              },

              tension: {

                bsonType: "object",

                properties: {

                  systolique: {
                    bsonType: "int"
                  },

                  diastolique: {
                    bsonType: "int"
                  }
                }
              },

              medicaments: {

                bsonType: "array",

                items: {

                  bsonType: "object",

                  properties: {

                    nom: {
                      bsonType: "string"
                    },

                    dosage: {
                      bsonType: "string"
                    },

                    duree: {
                      bsonType: "string"
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
});

// ─── 1.2 : Insérer des patients avec données algériennes ──────────────────────
// TODO: Insérer au moins 20 patients avec :
// - Prénoms et noms algériens variés
// - Wilayas différentes (Alger, Oran, Constantine, Annaba, Blida...)
// - Pathologies courantes (Diabète, HTA, Asthme, etc.)
// - Au moins 2-5 consultations par patient
// - Dates réalistes sur les 2 dernières années

const patients = [
  {
    cin: "198001012300",
    nom: "Bensalem",
    prenom: "Ahmed",
    dateNaissance: new Date("1980-01-01"),
    sexe: "M",
    adresse: { wilaya: "Alger", commune: "Bab Ezzouar" },
    groupeSanguin: "O+",
    antecedents: ["Diabète type 2", "HTA"],
    allergies: ["Pénicilline"],
    consultations: [
      {
        id: UUID(),
        date: new Date("2024-01-15"),
        medecin: { nom: "Dr. Mansouri", specialite: "Cardiologie" },
        diagnostic: "Hypertension artérielle",
        tension: { systolique: 145, diastolique: 92 },
        medicaments: [
          { nom: "Amlodipine", dosage: "5mg", duree: "30 jours" }
        ],
        notes: "Surveillance tensionnelle recommandée"
      },

      {
        id: UUID(),
        date: new Date("2024-05-10"),
        medecin: { nom: "Dr. Hamidi", specialite: "Endocrinologie" },
        diagnostic: "Diabète type 2",
        tension: { systolique: 138, diastolique: 88 },
        medicaments: [
          { nom: "Metformine", dosage: "850mg", duree: "60 jours" }
        ],
        notes: "Contrôle glycémie"
      }
    ]
  },

  {
    cin: "199403112244",
    nom: "Bouziane",
    prenom: "Yasmine",
    dateNaissance: new Date("1994-03-11"),
    sexe: "F",
    adresse: { wilaya: "Oran", commune: "Es Senia" },
    groupeSanguin: "A+",
    antecedents: ["Asthme"],
    allergies: [],
    consultations: [
      {
        id: UUID(),
        date: new Date("2024-02-20"),
        medecin: { nom: "Dr. Benali", specialite: "Pneumologie" },
        diagnostic: "Crise d'asthme",
        tension: { systolique: 120, diastolique: 78 },
        medicaments: [
          { nom: "Ventoline", dosage: "2 bouffées", duree: "15 jours" }
        ],
        notes: "Éviter les allergènes"
      }
    ]
  },

  {
    cin: "197812014587",
    nom: "Mekki",
    prenom: "Karim",
    dateNaissance: new Date("1978-12-01"),
    sexe: "M",
    adresse: { wilaya: "Constantine", commune: "El Khroub" },
    groupeSanguin: "B+",
    antecedents: ["HTA"],
    allergies: ["Aspirine"],
    consultations: [
      {
        id: UUID(),
        date: new Date("2024-03-18"),
        medecin: { nom: "Dr. Rahmani", specialite: "Cardiologie" },
        diagnostic: "Hypertension",
        tension: { systolique: 150, diastolique: 95 },
        medicaments: [
          { nom: "Losartan", dosage: "50mg", duree: "30 jours" }
        ],
        notes: "Repos conseillé"
      }
    ]
  }
];

// TODO: Ajouter 19 autres patients

for (let i = 4; i <= 20; i++) {

  patients.push({
    cin: "2000000000" + i,
    nom: "Patient" + i,
    prenom: "Test" + i,

    dateNaissance: new Date(
      1970 + i,
      i % 12,
      i
    ),

    sexe: i % 2 === 0 ? "M" : "F",

    adresse: {
      wilaya: ["Alger", "Oran", "Blida", "Annaba"][i % 4],
      commune: "Commune" + i
    },

    groupeSanguin: ["A+", "B+", "O+", "AB+"][i % 4],

    antecedents: i % 2 === 0
      ? ["Diabète"]
      : ["HTA"],

    allergies: [],

    consultations: [
      {
        id: UUID(),

        date: new Date(2024, i % 12, 10),

        medecin: {
          nom: "Dr. Test",
          specialite: "Médecine générale"
        },

        diagnostic: i % 2 === 0
          ? "Diabète"
          : "Hypertension",

        tension: {
          systolique: 120 + i,
          diastolique: 80 + (i % 10)
        },

        medicaments: [
          {
            nom: "Paracétamol",
            dosage: "500mg",
            duree: "7 jours"
          }
        ],

        notes: "Consultation standard"
      }
    ]
  });
}

db.patients.insertMany(patients);

// ─── 1.3 : Collection analyses (référencée) ───────────────────────────────────
// TODO: Créer des analyses pour les patients insérés
// Types : "Glycémie", "NFS", "Lipidogramme", "Créatinine", "ECG"

db.createCollection("analyses");

const analyses = [];

const allPatients = db.patients.find().toArray();

allPatients.forEach(patient => {

  analyses.push({
    patient_id: patient._id,

    date: new Date("2024-06-01"),

    type: "Glycémie",

    resultats: {
      glycemie: 1.35
    },

    laboratoire: "Labo Central Alger",

    valide: true
  });

  analyses.push({
    patient_id: patient._id,

    date: new Date("2024-07-15"),

    type: "ECG",

    resultats: {
      rythme: "Normal"
    },

    laboratoire: "Clinique El Azhar",

    valide: true
  });

  analyses.push({
    patient_id: patient._id,

    date: new Date("2024-08-10"),

    type: "Lipidogramme",

    resultats: {
      cholesterol: 2.1
    },

    laboratoire: "Biolab Constantine",

    valide: true
  });
});

db.analyses.insertMany(analyses);

print("✅ Modélisation terminée. Patients insérés:", db.patients.countDocuments());
print("✅ Analyses insérées:", db.analyses.countDocuments());
