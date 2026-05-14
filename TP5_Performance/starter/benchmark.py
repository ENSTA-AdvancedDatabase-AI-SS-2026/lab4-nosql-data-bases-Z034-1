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


# ─── Utilitaires de mesure ────────────────────────────────────────────────────

def measure_latency(fn: Callable, iterations: int = 1000) -> dict:
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        latencies.append((time.perf_counter() - start) * 1000)

    latencies.sort()

    return {
        "mean_ms": statistics.mean(latencies),
        "p50_ms": latencies[int(0.50 * len(latencies))],
        "p95_ms": latencies[int(0.95 * len(latencies))],
        "p99_ms": latencies[int(0.99 * len(latencies))],
        "max_ms": max(latencies),
        "throughput_rps": 1000 / statistics.mean(latencies)
    }


def print_results(name: str, results: dict):
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}")
    for k, v in results.items():
        print(f"  {k:20s}: {v:.2f}")


# ─── Ex1 : Benchmark Écriture ─────────────────────────────────────────────────

def benchmark_write_redis(n: int = 100_000):
    r = redis.Redis(host='localhost', port=6379)
    pipe = r.pipeline()

    def write():
        pipe.set(f"key:{time.time_ns()}", "value")
        pipe.execute()

    results = measure_latency(write, iterations=min(n, 1000))
    print_results("Redis WRITE", results)


def benchmark_write_mongodb(n: int = 100_000):
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    db = client["benchmark"]
    col = db["data"]

    docs = [{"_id": i, "value": i} for i in range(n)]

    start = time.time()
    col.insert_many(docs, ordered=False)
    elapsed = time.time() - start

    print_results("MongoDB WRITE", {
        "total_time_s": elapsed,
        "throughput_rps": n / elapsed
    })


def benchmark_write_cassandra(n: int = 100_000):
    cluster = Cluster(["localhost"])
    session = cluster.connect("benchmark")

    prepared = session.prepare("""
        INSERT INTO data (id, value) VALUES (?, ?)
    """)

    batch = []
    start = time.time()

    for i in range(n):
        batch.append((i, i))

        if len(batch) == 50:
            stmt = session.prepare("INSERT INTO data (id, value) VALUES (?, ?)")
            for b in batch:
                session.execute(stmt, b)
            batch = []

    elapsed = time.time() - start

    print_results("Cassandra WRITE", {
        "total_time_s": elapsed,
        "throughput_rps": n / elapsed
    })


# ─── Ex2 : Benchmark Lecture ─────────────────────────────────────────────────

def benchmark_read_redis():
    r = redis.Redis(host='localhost', port=6379)

    def point_lookup():
        r.get("key:1")

    def range_query():
        r.zrange("sorted", 0, 100)

    def complex_query():
        pipe = r.pipeline()
        pipe.get("key:1")
        pipe.get("key:2")
        pipe.get("key:3")
        pipe.execute()

    print_results("Redis READ - point", measure_latency(point_lookup, 1000))
    print_results("Redis READ - range", measure_latency(range_query, 1000))
    print_results("Redis READ - complex", measure_latency(complex_query, 1000))


def benchmark_read_mongodb():
    client = MongoClient("mongodb://admin:admin123@localhost:27017/")
    col = client["benchmark"]["data"]

    def point_lookup():
        col.find_one({"_id": 1})

    def range_query():
        col.find({"_id": {"$lt": 100}})

    def complex_query():
        list(col.aggregate([
            {"$match": {"_id": {"$lt": 100}}},
            {"$group": {"_id": None, "sum": {"$sum": "$value"}}}
        ]))

    print_results("MongoDB READ - point", measure_latency(point_lookup, 1000))
    print_results("MongoDB READ - range", measure_latency(range_query, 1000))
    print_results("MongoDB READ - complex", measure_latency(complex_query, 500))


# ─── Ex3 : Charge concurrente ─────────────────────────────────────────────────

def benchmark_concurrent(db_fn: Callable, n_clients: int = 50, requests_per_client: int = 200):
    latencies = []

    def worker():
        for _ in range(requests_per_client):
            start = time.perf_counter()
            db_fn()
            latencies.append((time.perf_counter() - start) * 1000)

    threads = []

    start_global = time.time()

    for _ in range(n_clients):
        t = threading.Thread(target=worker)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start_global

    latencies.sort()

    results = {
        "total_requests": n_clients * requests_per_client,
        "mean_ms": statistics.mean(latencies),
        "p95_ms": latencies[int(0.95 * len(latencies))],
        "throughput_rps": len(latencies) / elapsed
    }

    print_results("CONCURRENCY TEST", results)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 Benchmark NoSQL - Comparatif des 4 technologies")
    print("="*60)

    N = 10_000

    print(f"\n📝 Benchmark Écriture ({N:,} enregistrements)")
    benchmark_write_redis(N)
    benchmark_write_mongodb(N)
    benchmark_write_cassandra(N)

    print(f"\n📖 Benchmark Lecture (1,000 requêtes)")
    benchmark_read_redis()
    benchmark_read_mongodb()

    print(f"\n⚡ Test Charge Concurrente (50 clients)")
    benchmark_concurrent(lambda: None)  # placeholder safe

    print("\n✅ Benchmark terminé ! Consultez RAPPORT.md pour l'analyse.")
