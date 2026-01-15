import json
from src import redis_client

ROOM_TTL = 604800 # Expire rooms after 7 days

def get_room(room_id):
    """Load room state from Redis."""
    raw = redis_client.get(f"room:{room_id}")
    if raw:
        return json.loads(raw)
    return None

def save_room(room_id, state):
    """Save room state to Redis."""
    redis_client.set(f"room:{room_id}", json.dumps(state), ex=ROOM_TTL)

def room_exists(room_id):
    return redis_client.exists(f"room:{room_id}")
