from flask import request, session
from flask_socketio import emit
from src import socketio, db
from src.state import _get_public_state
from src.model import TicketSession, Vote
from src.store import get_room, save_room
from src.utils import clean_jira_key, get_allowed_custom_emojis
from markupsafe import escape

ALLOWED_CUSTOM_IMAGES = get_allowed_custom_emojis()

@socketio.on('start_vote')
def start_vote(data):
    room_id = data['room_id']
    state = get_room(room_id)
    if not state: return

    clean_key = clean_jira_key(data['ticket_key'])

    state['active'] = True
    state['ticket_key'] = clean_key
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
    state['votes'] = {}
    state['revealed'] = False
    save_room(room_id, state)
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('send_reaction')
def send_reaction(data):
    # Constants for emoji validation and truncation
    MAX_STANDARD_EMOJI_LENGTH = 10  # Max length for standard Unicode emojis
    MAX_EMOJI_LENGTH = 100  # Max length for truncation (includes custom emoji paths)
    
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
    elif len(emoji) <= MAX_STANDARD_EMOJI_LENGTH:
        is_valid = True
        
    if not is_valid: return
    
    safe_emoji = escape(emoji)[:MAX_EMOJI_LENGTH]
    sender_name = participant.get('name') or session.get('user_name', 'Anon')
    # Broadcast the reaction to everyone (including the sender)
    emit('trigger_reaction', {
        'emoji': safe_emoji,
        'sender': sender_name
    }, to=room_id)
