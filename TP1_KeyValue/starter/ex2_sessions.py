"""
TP1 - Exercice 2 : Gestion des Sessions Utilisateur
Use Case : ShopFast - Sessions avec expiration automatique (sliding TTL)
"""
import redis
import uuid
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

SESSION_TTL = 30 * 60  # 30 minutes en secondes


def create_session(r, user_id, user_data: dict):
    """
    Créer une nouvelle session utilisateur
    Clé : "session:{token}" (Hash)
    - Générer un token unique avec uuid4
    - Stocker user_id + user_data dans le Hash
    - Appliquer un TTL de 30 minutes
    - Retourner le token

    >>> token = create_session(r, "user:42", {"name": "Karim", "wilaya": "Alger"})
    """
    token = str(uuid.uuid4())
    key = f"session:{token}"

    payload = {"user_id": user_id, "created_at": int(time.time())}
    payload.update(user_data)

    r.hset(key, mapping=payload)
    r.expire(key, SESSION_TTL)

    return token


def get_session(r, token):
    """
    Récupérer une session et renouveler son TTL (sliding expiration)
    Retourner None si la session n'existe pas ou est expirée
    """
    key = f"session:{token}"
    data = r.hgetall(key)

    if not data:
        return None

    # Sliding expiration : repousser le TTL à chaque accès
    r.expire(key, SESSION_TTL)

    return data


def delete_session(r, token):
    """
    Supprimer une session (déconnexion)
    Clé : "session:{token}"
    """
    r.delete(f"session:{token}")


def is_session_valid(r, token):
    """
    Vérifier si une session existe et est valide
    Retourner True ou False
    """
    return r.exists(f"session:{token}") == 1


def get_session_ttl(r, token):
    """
    Récupérer le TTL restant d'une session en secondes
    Retourner -2 si la clé n'existe pas
    """
    return r.ttl(f"session:{token}")


def refresh_session(r, token):
    """
    Renouveler explicitement le TTL d'une session
    Retourner True si la session existait, False sinon
    """
    key = f"session:{token}"
    if not r.exists(key):
        return False
    r.expire(key, SESSION_TTL)
    return True


if __name__ == "__main__":
    r.flushdb()

    # Créer une session
    token = create_session(r, "user:42", {"name": "Karim", "wilaya": "Alger"})
    print("Token créé :", token)

    # Récupérer la session
    session = get_session(r, token)
    print("Session :", session)

    # TTL restant
    print("TTL restant :", get_session_ttl(r, token), "secondes")

    # Vérifier validité
    print("Session valide :", is_session_valid(r, token))

    # Supprimer
    delete_session(r, token)
    print("Après suppression :", get_session(r, token))
    print("Session valide :", is_session_valid(r, token))
