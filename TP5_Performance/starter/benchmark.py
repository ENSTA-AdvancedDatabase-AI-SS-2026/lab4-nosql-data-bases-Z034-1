"""
TP5 - Benchmark Comparatif NoSQL
Mesurer les performances de Redis, MongoDB, Cassandra, Neo4j
"""
import time
import statistics
import json
from typing import Callable, List, Tuple
import redis
from pymongo import MongoClient
from cassandra.cluster import Cluster
from neo4j import GraphDatabase
import threading
import psutil
import os


# ─── Utilitaires de mesure ────────────────────────────────────────────────────

def measure_latency(fn: Callable, iterations: int = 1000) -> dict:
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - start) * 1000)

    latencies.sort()

    return {
        "mean_ms":        statistics.mean(latencies),
        "p50_ms":         latencies[int(0.50 * len(latencies))],
        "p95_ms":         latencies[int(0.95 * len(latencies))],
        "p99_ms":         latencies[int(0.99 * len(latencies))],
        "max_ms":         max(latencies),
        "throughput_rps": 1000 / statistics.mean(latencies)
    }


def measure_resources(fn: Callable) -> dict:
    """Mesure CPU et mémoire pendant l'exécution d'une fonction."""
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    cpu_before = psutil.cpu_percent(interval=None)

    fn()

    mem_after = process.memory_info().rss / 1024 / 1024
    cpu_after = psutil.cpu_percent(interval=0.1)

    return {
        "mem_before_mb": round(mem_before, 2),
        "mem_after_mb":  round(mem_after, 2),
        "mem_delta_mb":  round(mem_after - mem_before, 2),
        "cpu_percent":   round(cpu_after, 2),
    }


def print_results(name: str, results: dict):
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    for k, v in results.items():
        print(f"  {k:25s}: {v:.2f}")


def print_section(title: str):
    print(f"\n{'#'*60}")
    print(f"  {title}")
    print(f"{'#'*60}")


# ─── Connexions ───────────────────────────────────────────────────────────────

def get_redis():
    return redis.Redis(host='localhost', port=6379, decode_responses=True)

def get_mongo():
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    return client["benchmark"]

def get_cassandra():
    cluster = Cluster(["localhost"])
    return cluster.connect()

def get_neo4j():
    return GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))


# ─── Setup des bases pour le benchmark ───────────────────────────────────────

def setup_cassandra(session):
    """Crée le keyspace et la table benchmark dans Cassandra."""
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS benchmark
        WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}
    """)
    session.set_keyspace("benchmark")
    session.execute("DROP TABLE IF EXISTS data")
    session.execute("""
        CREATE TABLE data (
            id    INT PRIMARY KEY,
            value INT,
            label TEXT
        )
    """)


def setup_neo4j(driver):
    """Crée les contraintes et nettoie la base Neo4j."""
    with driver.session() as session:
        session.run("MATCH (n:BenchNode) DETACH DELETE n")
        session.run("CREATE CONSTRAINT bench_id IF NOT EXISTS FOR (n:BenchNode) REQUIRE n.id IS UNIQUE")


def setup_redis(r):
    r.flushdb()


def setup_mongo(db):
    db.data.drop()


# ─── Ex1 : Benchmark Écriture ─────────────────────────────────────────────────

def benchmark_write_redis(n: int = 100_000):
    print_section(f"Ex1 — Écriture Redis ({n:,} enregistrements)")
    r = get_redis()
    setup_redis(r)

    # Mesure ressources
    def bulk_write():
        pipe = r.pipeline()
        for i in range(n):
            pipe.set(f"bench:key:{i}", json.dumps({"id": i, "value": i, "label": f"item_{i}"}))
            if i % 1000 == 0:
                pipe.execute()
                pipe = r.pipeline()
        pipe.execute()

    resources = measure_resources(bulk_write)

    # Mesure latence sur requêtes individuelles
    def single_write():
        r.set(f"bench:key:{time.time_ns()}", "value")

    latency = measure_latency(single_write, iterations=1000)

    print_results("Redis WRITE - latence unitaire", latency)
    print_results("Redis WRITE - ressources", resources)
    return {**latency, **resources}


def benchmark_write_mongodb(n: int = 100_000):
    print_section(f"Ex1 — Écriture MongoDB ({n:,} enregistrements)")
    db = get_mongo()
    setup_mongo(db)

    docs = [{"_id": i, "value": i, "label": f"item_{i}"} for i in range(n)]

    def bulk_write():
        db.data.insert_many(docs, ordered=False)

    resources = measure_resources(bulk_write)

    # Latence unitaire
    db.data2.drop()
    def single_write():
        db.data2.insert_one({"value": time.time_ns()})

    latency = measure_latency(single_write, iterations=1000)

    print_results("MongoDB WRITE - latence unitaire", latency)
    print_results("MongoDB WRITE - ressources", resources)
    return {**latency, **resources}


def benchmark_write_cassandra(n: int = 100_000):
    print_section(f"Ex1 — Écriture Cassandra ({n:,} enregistrements)")
    session = get_cassandra()
    setup_cassandra(session)

    prepared = session.prepare("INSERT INTO data (id, value, label) VALUES (?, ?, ?)")

    def bulk_write():
        batch_size = 50
        for i in range(0, n, batch_size):
            for j in range(i, min(i + batch_size, n)):
                session.execute(prepared, (j, j, f"item_{j}"))

    resources = measure_resources(bulk_write)

    def single_write():
        session.execute(prepared, (int(time.time_ns() % 1e9), 0, "bench"))

    latency = measure_latency(single_write, iterations=500)

    print_results("Cassandra WRITE - latence unitaire", latency)
    print_results("Cassandra WRITE - ressources", resources)
    return {**latency, **resources}


def benchmark_write_neo4j(n: int = 10_000):
    """Neo4j: limité à 10k pour les graphes (nœuds + relations)."""
    print_section(f"Ex1 — Écriture Neo4j ({n:,} nœuds)")
    driver = get_neo4j()
    setup_neo4j(driver)

    def bulk_write():
        with driver.session() as session:
            for i in range(0, n, 500):
                batch = [{"id": j, "value": j} for j in range(i, min(i + 500, n))]
                session.run("""
                    UNWIND $batch AS row
                    CREATE (n:BenchNode {id: row.id, value: row.value})
                """, batch=batch)

    resources = measure_resources(bulk_write)

    def single_write():
        with driver.session() as session:
            session.run("CREATE (n:BenchNode {id: $id, value: 0})", id=int(time.time_ns() % 1e9))

    latency = measure_latency(single_write, iterations=200)

    print_results("Neo4j WRITE - latence unitaire", latency)
    print_results("Neo4j WRITE - ressources", resources)
    return {**latency, **resources}


# ─── Ex2 : Benchmark Lecture ─────────────────────────────────────────────────

def benchmark_read_redis():
    print_section("Ex2 — Lecture Redis")
    r = get_redis()

    # Point lookup
    def point_lookup():
        r.get("bench:key:42")

    # Range query (Sorted Set)
    r.delete("bench:sorted")
    for i in range(1000):
        r.zadd("bench:sorted", {f"item:{i}": i})

    def range_query():
        r.zrange("bench:sorted", 0, 100, withscores=True)

    # Complex : pipeline multi-get
    def complex_query():
        pipe = r.pipeline()
        for i in range(10):
            pipe.get(f"bench:key:{i}")
        pipe.execute()

    r1 = measure_latency(point_lookup, 1000)
    r2 = measure_latency(range_query,  1000)
    r3 = measure_latency(complex_query, 1000)

    print_results("Redis READ - point lookup",  r1)
    print_results("Redis READ - range query",   r2)
    print_results("Redis READ - complex query", r3)
    return r1, r2, r3


def benchmark_read_mongodb():
    print_section("Ex2 — Lecture MongoDB")
    db = get_mongo()

    # Index pour accélérer les range queries
    db.data.create_index("value")

    def point_lookup():
        db.data.find_one({"_id": 42})

    def range_query():
        list(db.data.find({"value": {"$gte": 0, "$lt": 100}}))

    def complex_query():
        list(db.data.aggregate([
            {"$match":  {"value": {"$lt": 1000}}},
            {"$group":  {"_id": None, "total": {"$sum": "$value"}, "count": {"$sum": 1}}},
            {"$project": {"avg": {"$divide": ["$total", "$count"]}}}
        ]))

    r1 = measure_latency(point_lookup,  1000)
    r2 = measure_latency(range_query,   1000)
    r3 = measure_latency(complex_query,  500)

    print_results("MongoDB READ - point lookup",  r1)
    print_results("MongoDB READ - range query",   r2)
    print_results("MongoDB READ - complex query", r3)
    return r1, r2, r3


def benchmark_read_cassandra():
    print_section("Ex2 — Lecture Cassandra")
    session = get_cassandra()
    session.set_keyspace("benchmark")

    prepared_point = session.prepare("SELECT * FROM data WHERE id = ?")
    prepared_range = session.prepare("SELECT * FROM data WHERE id >= ? AND id < ? ALLOW FILTERING")

    def point_lookup():
        session.execute(prepared_point, (42,))

    def range_query():
        list(session.execute(prepared_range, (0, 100)))

    def complex_query():
        list(session.execute("SELECT COUNT(*) FROM data"))

    r1 = measure_latency(point_lookup, 1000)
    r2 = measure_latency(range_query,   500)
    r3 = measure_latency(complex_query, 200)

    print_results("Cassandra READ - point lookup",  r1)
    print_results("Cassandra READ - range query",   r2)
    print_results("Cassandra READ - complex query", r3)
    return r1, r2, r3


def benchmark_read_neo4j():
    print_section("Ex2 — Lecture Neo4j")
    driver = get_neo4j()

    def point_lookup():
        with driver.session() as session:
            session.run("MATCH (n:BenchNode {id: 42}) RETURN n").single()

    def range_query():
        with driver.session() as session:
            session.run("MATCH (n:BenchNode) WHERE n.value < 100 RETURN n").data()

    def complex_query():
        with driver.session() as session:
            session.run("""
                MATCH (n:BenchNode)
                RETURN COUNT(n) AS total, AVG(n.value) AS avg_value
            """).single()

    r1 = measure_latency(point_lookup, 500)
    r2 = measure_latency(range_query,  200)
    r3 = measure_latency(complex_query, 200)

    print_results("Neo4j READ - point lookup",  r1)
    print_results("Neo4j READ - range query",   r2)
    print_results("Neo4j READ - complex query", r3)
    return r1, r2, r3


# ─── Ex3 : Charge Concurrente ─────────────────────────────────────────────────

def benchmark_concurrent(db_name: str, db_fn: Callable,
                         n_clients: int = 50, requests_per_client: int = 200):
    print_section(f"Ex3 — Charge Concurrente {db_name} ({n_clients} clients × {requests_per_client} req)")
    latencies = []
    lock = threading.Lock()

    def worker():
        for _ in range(requests_per_client):
            start = time.perf_counter()
            try:
                db_fn()
            except Exception:
                pass
            elapsed = (time.perf_counter() - start) * 1000
            with lock:
                latencies.append(elapsed)

    threads = [threading.Thread(target=worker) for _ in range(n_clients)]
    start_global = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed_total = time.time() - start_global

    latencies.sort()
    results = {
        "total_requests":  float(n_clients * requests_per_client),
        "elapsed_s":       elapsed_total,
        "mean_ms":         statistics.mean(latencies),
        "p50_ms":          latencies[int(0.50 * len(latencies))],
        "p95_ms":          latencies[int(0.95 * len(latencies))],
        "p99_ms":          latencies[int(0.99 * len(latencies))],
        "throughput_rps":  len(latencies) / elapsed_total,
    }
    print_results(f"{db_name} CONCURRENT", results)
    return results


# ─── Ex4 : Rapport de Recommandation ─────────────────────────────────────────

def print_recommendation_report(write_results: dict, read_results: dict, concurrent_results: dict):
    print_section("Ex4 — Rapport de Recommandation")

    header = f"{'Critère':<28} {'Redis':>10} {'MongoDB':>10} {'Cassandra':>10} {'Neo4j':>10}"
    sep    = "-" * len(header)

    def fmt(d, key):
        v = d.get(key)
        return f"{v:>10.1f}" if v is not None else f"{'N/A':>10}"

    print(f"\n{header}")
    print(sep)

    # Débit écriture
    row = f"{'Débit écriture (rps)':<28}"
    for db in ["redis", "mongodb", "cassandra", "neo4j"]:
        row += fmt(write_results.get(db, {}), "throughput_rps")
    print(row)

    # Latence lecture P50
    row = f"{'Latence lecture P50 (ms)':<28}"
    for db in ["redis", "mongodb", "cassandra", "neo4j"]:
        row += fmt(read_results.get(db, {}), "p50_ms")
    print(row)

    # Latence lecture P99
    row = f"{'Latence lecture P99 (ms)':<28}"
    for db in ["redis", "mongodb", "cassandra", "neo4j"]:
        row += fmt(read_results.get(db, {}), "p99_ms")
    print(row)

    # Charge concurrente P95
    row = f"{'Conc. P95 (ms)':<28}"
    for db in ["redis", "mongodb", "cassandra", "neo4j"]:
        row += fmt(concurrent_results.get(db, {}), "p95_ms")
    print(row)

    # Throughput concurrent
    row = f"{'Conc. Débit (rps)':<28}"
    for db in ["redis", "mongodb", "cassandra", "neo4j"]:
        row += fmt(concurrent_results.get(db, {}), "throughput_rps")
    print(row)

    print(sep)

    print("""
┌─────────────────────────────────────────────────────────────────────┐
│                    TABLEAU DE DÉCISION FINAL                        │
├──────────────────┬────────┬──────────┬───────────┬──────────────────┤
│ Critère          │ Redis  │ MongoDB  │ Cassandra │ Neo4j            │
├──────────────────┼────────┼──────────┼───────────┼──────────────────┤
│ Débit écriture   │ ★★★★★ │ ★★★★☆   │ ★★★★★    │ ★★☆☆☆           │
│ Débit lecture    │ ★★★★★ │ ★★★★☆   │ ★★★★☆    │ ★★★☆☆           │
│ Requêtes complexes│ ★★☆☆☆ │ ★★★★★  │ ★★☆☆☆    │ ★★★★★           │
│ Scalabilité      │ ★★★☆☆ │ ★★★★☆   │ ★★★★★    │ ★★★☆☆           │
│ Flexibilité      │ ★★☆☆☆ │ ★★★★★   │ ★★★☆☆    │ ★★★★☆           │
│ Cohérence        │ ★★★★★ │ ★★★★☆   │ ★★★☆☆    │ ★★★★☆           │
├──────────────────┼────────┼──────────┼───────────┼──────────────────┤
│ Use case idéal   │ Cache  │ Documents│ IoT/Logs  │ Graphe/Relations │
│                  │Sessions│ Médical  │ Séries    │ Réseau social    │
│                  │ Files  │ E-comm.  │ temporell.│ Recommandations  │
└──────────────────┴────────┴──────────┴───────────┴──────────────────┘

RECOMMANDATIONS :
  → Redis     : Utilisez pour le cache, sessions, classements temps réel (ShopFast TP1)
  → MongoDB   : Utilisez pour les dossiers complexes avec schéma flexible (HealthCare TP2)
  → Cassandra : Utilisez pour les séries temporelles à fort volume (IoT TP3)
  → Neo4j     : Utilisez pour les relations complexes (réseau social TP4)
  → Hybride   : En production, combinez plusieurs bases selon le besoin (polyglot persistence)
""")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Benchmark NoSQL - Comparatif des 4 technologies")
    print("=" * 60)

    N = 10_000

    write_results     = {}
    read_results      = {}
    concurrent_results = {}

    # ── Ex1 : Écriture ──
    print(f"\n📝 Benchmark Écriture ({N:,} enregistrements)")
    try:
        write_results["redis"]     = benchmark_write_redis(N)
    except Exception as e:
        print(f"  ⚠️  Redis write skipped: {e}")

    try:
        write_results["mongodb"]   = benchmark_write_mongodb(N)
    except Exception as e:
        print(f"  ⚠️  MongoDB write skipped: {e}")

    try:
        write_results["cassandra"] = benchmark_write_cassandra(N)
    except Exception as e:
        print(f"  ⚠️  Cassandra write skipped: {e}")

    try:
        write_results["neo4j"]     = benchmark_write_neo4j(min(N, 5000))
    except Exception as e:
        print(f"  ⚠️  Neo4j write skipped: {e}")

    # ── Ex2 : Lecture ──
    print(f"\n📖 Benchmark Lecture (1 000 requêtes par type)")
    try:
        r1, r2, r3 = benchmark_read_redis()
        read_results["redis"] = r1   # point lookup comme référence
    except Exception as e:
        print(f"  ⚠️  Redis read skipped: {e}")

    try:
        r1, r2, r3 = benchmark_read_mongodb()
        read_results["mongodb"] = r1
    except Exception as e:
        print(f"  ⚠️  MongoDB read skipped: {e}")

    try:
        r1, r2, r3 = benchmark_read_cassandra()
        read_results["cassandra"] = r1
    except Exception as e:
        print(f"  ⚠️  Cassandra read skipped: {e}")

    try:
        r1, r2, r3 = benchmark_read_neo4j()
        read_results["neo4j"] = r1
    except Exception as e:
        print(f"  ⚠️  Neo4j read skipped: {e}")

    # ── Ex3 : Concurrence ──
    print(f"\n⚡ Test Charge Concurrente (50 clients × 200 requêtes)")
    r = get_redis()
    try:
        concurrent_results["redis"] = benchmark_concurrent(
            "Redis", lambda: r.get("bench:key:42"), n_clients=50, requests_per_client=200
        )
    except Exception as e:
        print(f"  ⚠️  Redis concurrent skipped: {e}")

    try:
        db = get_mongo()
        concurrent_results["mongodb"] = benchmark_concurrent(
            "MongoDB", lambda: db.data.find_one({"_id": 42}), n_clients=50, requests_per_client=200
        )
    except Exception as e:
        print(f"  ⚠️  MongoDB concurrent skipped: {e}")

    try:
        session = get_cassandra()
        session.set_keyspace("benchmark")
        stmt = session.prepare("SELECT * FROM data WHERE id = ?")
        concurrent_results["cassandra"] = benchmark_concurrent(
            "Cassandra", lambda: session.execute(stmt, (42,)), n_clients=20, requests_per_client=100
        )
    except Exception as e:
        print(f"  ⚠️  Cassandra concurrent skipped: {e}")

    try:
        driver = get_neo4j()
        concurrent_results["neo4j"] = benchmark_concurrent(
            "Neo4j", lambda: driver.session().run("MATCH (n:BenchNode {id:42}) RETURN n").single(),
            n_clients=10, requests_per_client=50
        )
    except Exception as e:
        print(f"  ⚠️  Neo4j concurrent skipped: {e}")

    # ── Ex4 : Rapport ──
    print_recommendation_report(write_results, read_results, concurrent_results)

    print("\n✅ Benchmark terminé ! Consultez RAPPORT.md pour l'analyse complète.")
