import json
from contextlib import contextmanager
from src import redis_client

ROOM_TTL = 604800 # 7 days

def get_room(room_id):
    """Load room state from Redis (Read-Only)."""
    raw = redis_client.get(f"room:{room_id}")
    if raw:
        return json.loads(raw)
    return None

def save_room(room_id, state):
    """Save room state to Redis (Direct Write)."""
    redis_client.set(f"room:{room_id}", json.dumps(state), ex=ROOM_TTL)

def room_exists(room_id):
    return redis_client.exists(f"room:{room_id}")

@contextmanager
def change_room(room_id):
    """
    Context Manager that safely locks the room, loads state, 
    yields it for modification, and automatically saves it back.
    """
    lock_key = f"lock:room:{room_id}"
    # Wait up to 2 seconds to get lock, lock expires after 5 seconds
    lock = redis_client.lock(lock_key, timeout=5, blocking_timeout=2)
    
    acquired = lock.acquire()
    if not acquired:
        # If we can't get the lock (busy), return None to signal failure
        yield None
        return

    try:
        state = get_room(room_id)
        if state:
            # Yield the state to the `with` block for modification
            yield state
            # Auto-save after the block finishes
            save_room(room_id, state)
        else:
            yield None
    finally:
        lock.release()