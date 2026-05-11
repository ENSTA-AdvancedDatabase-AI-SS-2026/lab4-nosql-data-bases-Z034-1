"""Tests pour l'exercice 2 - Sessions utilisateur"""
import pytest
import redis
import time
import sys
sys.path.insert(0, '..')
from ex2_sessions import *

@pytest.fixture(autouse=True)
def clean_redis():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.flushdb()
    yield r
    r.flushdb()

def test_create_session_returns_token(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    assert token is not None
    assert len(token) > 0

def test_get_session_returns_data(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim", "wilaya": "Alger"})
    session = get_session(r, token)
    assert session is not None
    assert session["user_id"] == "user:1"
    assert session["name"] == "Karim"

def test_get_nonexistent_session(clean_redis):
    r = clean_redis
    assert get_session(r, "fake-token-xyz") is None

def test_session_has_ttl(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    ttl = get_session_ttl(r, token)
    assert 0 < ttl <= 1800  # 30 minutes max

def test_session_is_valid(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    assert is_session_valid(r, token) is True

def test_invalid_token_not_valid(clean_redis):
    r = clean_redis
    assert is_session_valid(r, "nonexistent-token") is False

def test_delete_session(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    delete_session(r, token)
    assert get_session(r, token) is None
    assert is_session_valid(r, token) is False

def test_refresh_session_extends_ttl(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    # Réduire le TTL manuellement
    r.expire(f"session:{token}", 60)
    assert get_session_ttl(r, token) <= 60
    # Refresh doit remettre à 1800
    result = refresh_session(r, token)
    assert result is True
    assert get_session_ttl(r, token) > 60

def test_refresh_nonexistent_session(clean_redis):
    r = clean_redis
    assert refresh_session(r, "fake-token") is False

def test_get_session_slides_ttl(clean_redis):
    r = clean_redis
    token = create_session(r, "user:1", {"name": "Karim"})
    r.expire(f"session:{token}", 100)
    get_session(r, token)  # Accès → doit renouveler le TTL
    assert get_session_ttl(r, token) > 100

def test_unique_tokens(clean_redis):
    r = clean_redis
    t1 = create_session(r, "user:1", {"name": "Karim"})
    t2 = create_session(r, "user:1", {"name": "Karim"})
    assert t1 != t2
