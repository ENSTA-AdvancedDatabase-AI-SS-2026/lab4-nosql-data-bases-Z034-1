"""Tests pour l'exercice 3 - Cache-Aside"""
import pytest
import redis
import time
import sys
sys.path.insert(0, '..')
from ex3_cache import *

@pytest.fixture(autouse=True)
def clean_redis():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()

def test_cache_miss_returns_product(clean_redis):
    r = clean_redis
    product = get_product_cached(r, 1)
    assert product is not None
    assert product["id"] == 1
    assert product["name"] == "Samsung Galaxy A54"

def test_cache_hit_returns_same_data(clean_redis):
    r = clean_redis
    p1 = get_product_cached(r, 1)
    p2 = get_product_cached(r, 1)
    assert p1 == p2

def test_cache_miss_stores_in_redis(clean_redis):
    r = clean_redis
    get_product_cached(r, 1)
    cached = r.get("product_cache:1")
    assert cached is not None

def test_cache_hit_is_faster(clean_redis):
    r = clean_redis
    # MISS
    t0 = time.time()
    get_product_cached(r, 1)
    miss_time = time.time() - t0

    # HIT
    t0 = time.time()
    get_product_cached(r, 1)
    hit_time = time.time() - t0

    assert hit_time < miss_time

def test_cache_ttl_is_set(clean_redis):
    r = clean_redis
    get_product_cached(r, 1, ttl=600)
    ttl = r.ttl("product_cache:1")
    assert 0 < ttl <= 600

def test_nonexistent_product_returns_none(clean_redis):
    r = clean_redis
    result = get_product_cached(r, 999)
    assert result is None

def test_invalidate_removes_cache(clean_redis):
    r = clean_redis
    get_product_cached(r, 1)
    assert r.exists("product_cache:1")
    invalidate_product_cache(r, 1)
    assert not r.exists("product_cache:1")

def test_after_invalidation_next_call_is_miss(clean_redis):
    r = clean_redis
    get_product_cached(r, 1)       # MISS → stores in cache
    invalidate_product_cache(r, 1) # Delete cache
    # Next call must go to DB again (slow ~2s)
    t0 = time.time()
    get_product_cached(r, 1)
    elapsed = time.time() - t0
    assert elapsed >= 1.5  # Should be slow (DB call)
