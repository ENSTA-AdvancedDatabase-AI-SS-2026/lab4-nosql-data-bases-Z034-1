"""
TP3 - Exercice 2 : Ingestion de données IoT
Use Case : SmartGrid DZ - 10 000 capteurs, 5 minutes de mesures
"""
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement, BatchType
import uuid
import random
from datetime import datetime, timedelta
import time

# Configuration
CASSANDRA_HOST = 'localhost'
KEYSPACE = 'smartgrid'
NB_CAPTEURS = 10000
MINUTES_HISTORIQUE = 5

WILAYAS = ["Alger", "Oran", "Constantine", "Annaba", "Blida"]
COMMUNES = {
    "Alger": ["Bab Ezzouar", "Hydra", "El Harrach", "Dar El Beida"],
    "Oran": ["Bir El Djir", "Es Senia", "Arzew"],
    "Constantine": ["El Khroub", "Ain Smara", "Hamma Bouziane"],
    "Annaba": ["El Bouni", "El Hadjar", "Seraidi"],
    "Blida": ["Bougara", "Boufarik", "Larbaa"],
}

def connect():
    """Connexion au cluster Cassandra"""
    cluster = Cluster([CASSANDRA_HOST])
    session = cluster.connect(KEYSPACE)
    return session, cluster


def generate_mesure(capteur_id, wilaya, commune, timestamp):
    """Générer une mesure réaliste pour un capteur"""
    tension_base = 220  # Volts (réseau algérien)
    
    return {
        "capteur_id": capteur_id,
        "date_jour": timestamp.date(),
        "timestamp": timestamp,
        "wilaya": wilaya,
        "commune": commune,
        "tension_v": round(tension_base + random.gauss(0, 5), 2),
        "courant_a": round(random.uniform(0.5, 15.0), 2),
        "puissance_kw": round(random.uniform(0.1, 3.3), 3),
        "frequence_hz": round(50 + random.gauss(0, 0.1), 2),
        "temperature": round(random.uniform(20, 65), 1),
        "alerte": random.random() < 0.05,
    }


def insert_single(session, mesure):
    """
    Insérer une seule mesure dans mesures_par_capteur
    Utiliser une prepared statement
    """
    prepared = session.prepare("""
        INSERT INTO mesures_par_capteur (
            capteur_id,
            date_jour,
            timestamp,
            wilaya,
            commune,
            tension_v,
            courant_a,
            puissance_kw,
            frequence_hz,
            temperature,
            alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        USING TTL 7776000
    """)

    session.execute(prepared, (
        mesure["capteur_id"],
        mesure["date_jour"],
        mesure["timestamp"],
        mesure["wilaya"],
        mesure["commune"],
        mesure["tension_v"],
        mesure["courant_a"],
        mesure["puissance_kw"],
        mesure["frequence_hz"],
        mesure["temperature"],
        mesure["alerte"],
    ))


def insert_batch(session, mesures: list):
    """
    Insérer un batch de mesures de manière efficace
    Utiliser UNLOGGED BATCH pour les séries temporelles
    Faire des batches de max 50 items
    """
    prepared = session.prepare("""
        INSERT INTO mesures_par_capteur (
            capteur_id,
            date_jour,
            timestamp,
            wilaya,
            commune,
            tension_v,
            courant_a,
            puissance_kw,
            frequence_hz,
            temperature,
            alerte
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        USING TTL 7776000
    """)

    batch = BatchStatement(batch_type=BatchType.UNLOGGED)

    for m in mesures:
        batch.add(prepared, (
            m["capteur_id"],
            m["date_jour"],
            m["timestamp"],
            m["wilaya"],
            m["commune"],
            m["tension_v"],
            m["courant_a"],
            m["puissance_kw"],
            m["frequence_hz"],
            m["temperature"],
            m["alerte"],
        ))

    session.execute(batch)


def run_ingestion(session):
    """
    Générer et insérer NB_CAPTEURS × MINUTES_HISTORIQUE mesures
    """
    print(f"Démarrage ingestion : {NB_CAPTEURS} capteurs × {MINUTES_HISTORIQUE} min")
    start = time.time()

    # 1. Générer capteurs
    capteurs = []
    for i in range(NB_CAPTEURS):
        wilaya = random.choice(WILAYAS)
        commune = random.choice(COMMUNES[wilaya])

        capteurs.append({
            "capteur_id": uuid.uuid4(),
            "wilaya": wilaya,
            "commune": commune
        })

    total_inserted = 0
    now = datetime.utcnow()

    # 2. Générer mesures temporelles
    for minute in range(MINUTES_HISTORIQUE):
        timestamp = now - timedelta(minutes=minute)

        batch_buffer = []

        for capteur in capteurs:
            mesure = generate_mesure(
                capteur["capteur_id"],
                capteur["wilaya"],
                capteur["commune"],
                timestamp
            )

            batch_buffer.append(mesure)

            # flush every 50
            if len(batch_buffer) == 50:
                insert_batch(session, batch_buffer)
                total_inserted += len(batch_buffer)
                batch_buffer = []

        # flush remaining per minute
        if batch_buffer:
            insert_batch(session, batch_buffer)
            total_inserted += len(batch_buffer)

    elapsed = time.time() - start

    print(f"\n✅ {total_inserted:,} mesures insérées en {elapsed:.1f}s")
    print(f"   Débit : {total_inserted/elapsed:,.0f} mesures/seconde")


if __name__ == "__main__":
    session, cluster = connect()
    run_ingestion(session)
    cluster.shutdown()
