import json
import threading
import time
from contextlib import contextmanager
from src import redis_client, app

ROOM_TTL = 604800 # 7 days

# In-memory storage fallback
_memory_store = {}
_memory_locks = {}
_memory_store_lock = threading.Lock()

def _get_memory_lock(room_id):
    """Get or create a lock for a room in memory."""
    with _memory_store_lock:
        if room_id not in _memory_locks:
            _memory_locks[room_id] = threading.Lock()
        return _memory_locks[room_id]

def _cleanup_expired_memory():
    """Remove expired entries from memory store."""
    current_time = time.time()
    with _memory_store_lock:
        expired = [k for k, v in _memory_store.items() 
                   if v.get('expires_at', float('inf')) < current_time]
        for key in expired:
            del _memory_store[key]

def get_room(room_id):
    """Load room state from Redis or memory (Read-Only)."""
    if app.config['USE_REDIS']:
        raw = redis_client.get(f"room:{room_id}")
        if raw:
            return json.loads(raw)
        return None
    else:
        # In-memory fallback
        _cleanup_expired_memory()
        key = f"room:{room_id}"
        with _memory_store_lock:
            entry = _memory_store.get(key)
            if entry and entry.get('expires_at', float('inf')) > time.time():
                return entry['data']
            return None

def save_room(room_id, state):
    """Save room state to Redis or memory (Direct Write)."""
    if app.config['USE_REDIS']:
        redis_client.set(f"room:{room_id}", json.dumps(state), ex=ROOM_TTL)
    else:
        # In-memory fallback
        key = f"room:{room_id}"
        with _memory_store_lock:
            _memory_store[key] = {
                'data': state,
                'expires_at': time.time() + ROOM_TTL
            }

def room_exists(room_id):
    """Check if room exists in Redis or memory."""
    if app.config['USE_REDIS']:
        return redis_client.exists(f"room:{room_id}")
    else:
        _cleanup_expired_memory()
        key = f"room:{room_id}"
        with _memory_store_lock:
            entry = _memory_store.get(key)
            return entry is not None and entry.get('expires_at', float('inf')) > time.time()

@contextmanager
def change_room(room_id):
    """
    Context Manager that safely locks the room, loads state, 
    yields it for modification, and automatically saves it back.
    Works with both Redis and in-memory storage.
    """
    if app.config['USE_REDIS']:
        # Redis implementation (existing code)
        lock_key = f"lock:room:{room_id}"
        lock = redis_client.lock(lock_key, timeout=5, blocking_timeout=2)
        
        acquired = lock.acquire()
        if not acquired:
            yield None
            return

        try:
            state = get_room(room_id)
            if state:
                yield state
                save_room(room_id, state)
            else:
                yield None
        finally:
            lock.release()
    else:
        # In-memory implementation
        room_lock = _get_memory_lock(room_id)
        acquired = room_lock.acquire(timeout=2)
        
        if not acquired:
            yield None
            return
        
        try:
            state = get_room(room_id)
            if state:
                yield state
                save_room(room_id, state)
            else:
                yield None
        finally:
            room_lock.release()