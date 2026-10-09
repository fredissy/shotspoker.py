import hashlib
import threading
import time
from flask import request, session
from flask_socketio import emit
from src import app, socketio, db, redis_client
from src.state import _get_public_state
from src.model import TicketSession, Vote
from src.store import get_room, save_room
from src.utils import clean_jira_key, get_allowed_custom_emojis, STANDARD_EMOJIS
from markupsafe import escape

ALLOWED_CUSTOM_IMAGES = get_allowed_custom_emojis()
_memory_reaction_buckets = {}
_memory_reaction_buckets_lock = threading.Lock()
_memory_reaction_bucket_checks = 0

_REACTION_RATE_LIMIT_SCRIPT = """
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local redis_time = redis.call('TIME')
local now = tonumber(redis_time[1]) + tonumber(redis_time[2]) / 1000000
local values = redis.call('HMGET', KEYS[1], 'tokens', 'updated_at')
local tokens = tonumber(values[1]) or capacity
local updated_at = tonumber(values[2]) or now

tokens = math.min(capacity, tokens + math.max(0, now - updated_at) * refill_rate)
local allowed = 0
if tokens >= 1 then
    tokens = tokens - 1
    allowed = 1
end

redis.call('HSET', KEYS[1], 'tokens', tokens, 'updated_at', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(capacity / refill_rate * 1000))
return allowed
"""


def _allow_reaction(room_id, user_name):
    capacity = app.config['REACTION_RATE_LIMIT_BURST']
    refill_rate = app.config['REACTION_RATE_LIMIT_REFILL_PER_SECOND']
    identity = hashlib.sha256(f'{room_id}\0{user_name}'.encode('utf-8')).hexdigest()
    bucket_key = f'reaction-rate:{identity}'

    if app.config['USE_REDIS']:
        return bool(redis_client.eval(
            _REACTION_RATE_LIMIT_SCRIPT,
            1,
            bucket_key,
            capacity,
            refill_rate
        ))

    global _memory_reaction_bucket_checks
    now = time.monotonic()
    with _memory_reaction_buckets_lock:
        tokens, updated_at = _memory_reaction_buckets.get(bucket_key, (capacity, now))
        tokens = min(capacity, tokens + max(0, now - updated_at) * refill_rate)
        allowed = tokens >= 1
        if allowed:
            tokens -= 1
        _memory_reaction_buckets[bucket_key] = (tokens, now)

        _memory_reaction_bucket_checks += 1
        if _memory_reaction_bucket_checks % 256 == 0:
            expiry = capacity / refill_rate
            expired_keys = [
                key for key, (_, last_updated) in _memory_reaction_buckets.items()
                if now - last_updated >= expiry
            ]
            for key in expired_keys:
                del _memory_reaction_buckets[key]

        return allowed


@socketio.on('start_vote')
def start_vote(data):
    room_id = data['room_id']
    state = get_room(room_id)
    if not state: return

    raw_key = data['ticket_key'].strip()
    clean_key = clean_jira_key(raw_key)[:50]


    state['active'] = True
    state['ticket_key'] = clean_key
    state['ticket_url'] = raw_key if raw_key.startswith(('http://', 'https://')) else None
    state['is_public'] = data['is_public']
    state['votes'] = {}
    state['revealed'] = False
    # Admin can change dynamically, or we stick to original creator.
    # Let's update admin to whoever started the vote to be flexible.
    state['admin_sid'] = request.sid

    if state['ticket_key'] in state['queue']:
        state['queue'].remove(state['ticket_key'])

    save_room(room_id, state)
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('cast_vote')
def cast_vote(data):
    room_id = data['room_id']
    state = get_room(room_id)
    if not state: return

    if not state['active'] or state['revealed']: return

    # Observer Check
    participant = state['participants'].get(request.sid)
    if participant and participant['role'] == 'observer': return

    user_name = participant['name']

    state['votes'][user_name] = {'value': data['vote_value']}
    save_room(room_id, state)
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('reveal_vote')
def reveal_vote(data):
    room_id = data['room_id']
    state = get_room(room_id)
    if not state: return

    state['revealed'] = True

    if state['votes']:
        # 1. Create the Session Record
        new_session = TicketSession(
            room_id=room_id,
            ticket_key=state['ticket_key'],
            is_public=state['is_public']
        )
        db.session.add(new_session)
        db.session.commit()

        # 2. Save Individual Votes
        total_value = 0
        vote_count = 0

        # CHANGE: Iterate over user_names directly
        for user_name, vote_data in state['votes'].items():
            val = vote_data['value']

            safe_name = escape(user_name)
            safe_name = safe_name[:100]

            vote_entry = Vote(
                user_name=safe_name,
                value=str(val),
                session_id=new_session.id
            )
            db.session.add(vote_entry)
            
            # Math logic (skip symbols)
            if str(val).replace('.', '', 1).isdigit():
                total_value += float(val)
                vote_count += 1
        
        if vote_count > 0:
            new_session.final_average = total_value / vote_count
        
        db.session.commit()

    save_room(room_id, state)
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('reset')
def reset(data):
    room_id = data['room_id']
    state = get_room(room_id)
    if not state: return

    if state['active'] and request.sid != state['admin_sid']:
        return

    state['active'] = False
    state['ticket_key'] = "Waiting..."
    state['ticket_url'] = None
    state['votes'] = {}
    state['revealed'] = False
    save_room(room_id, state)
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('send_reaction')
def send_reaction(data):
    room_id = data['room_id']
    
    state = get_room(room_id)
    if not state:
        return
    participant = state['participants'].get(request.sid)
    if not participant:
        return
    emoji = data.get('emoji', '')
    if not isinstance(emoji, str):
        return
    emoji = emoji.strip()
    if not emoji:
        return
    
    is_valid = False
    
    # 1. Dynamic Allowlist Check
    if emoji in ALLOWED_CUSTOM_IMAGES:
        is_valid = True
    elif emoji in STANDARD_EMOJIS:
        is_valid = True
        
    if not is_valid: return

    sender_name = participant.get('name') or session.get('user_name', 'Anon')
    if not isinstance(sender_name, str) or not _allow_reaction(room_id, sender_name):
        return
    
    # Escape the emoji for security (custom emojis are already validated via allowlist)
    safe_emoji = escape(emoji)
    
    # Broadcast the reaction to everyone (including the sender)
    emit('trigger_reaction', {
        'emoji': safe_emoji,
        'sender': sender_name
    }, to=room_id)
