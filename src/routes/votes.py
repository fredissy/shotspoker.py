from flask import request, session
from flask_socketio import emit
from src import socketio, db
from src.state import _get_public_state
from src.model import TicketSession, Vote
from src.store import change_room, get_room
from src.utils import clean_jira_key, get_allowed_custom_emojis, STANDARD_EMOJIS
from markupsafe import escape

ALLOWED_CUSTOM_IMAGES = get_allowed_custom_emojis()


@socketio.on('start_vote')
def start_vote(data):
    room_id = data['room_id']
    raw_key = data['ticket_key'].strip()
    clean_key = clean_jira_key(raw_key)[:50]

    with change_room(room_id) as state:
        if not state: return
        state['active'] = True
        state['ticket_key'] = clean_key
        state['ticket_url'] = raw_key if raw_key.startswith(('http://', 'https://')) else None
        state['is_public'] = data['is_public']
        state['votes'] = {}
        state['revealed'] = False
        state['admin_sid'] = request.sid

        if state['ticket_key'] in state['queue']:
            state['queue'].remove(state['ticket_key'])

    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('cast_vote')
def cast_vote(data):
    room_id = data['room_id']
    with change_room(room_id) as state:
        if not state or not state['active'] or state['revealed']: return

        participant = state['participants'].get(request.sid)
        if not participant or participant['role'] == 'observer': return

        state['votes'][participant['name']] = {'value': data['vote_value']}

    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('reveal_vote')
def reveal_vote(data):
    room_id = data['room_id']
    with change_room(room_id) as state:
        if not state or state['revealed']: return

        state['revealed'] = True

        if state['votes']:
            new_session = TicketSession(
                room_id=room_id,
                ticket_key=state['ticket_key'],
                is_public=state['is_public']
            )
            db.session.add(new_session)
            db.session.flush()

            total_value = 0
            vote_count = 0

            for user_name, vote_data in state['votes'].items():
                val = vote_data['value']
                vote_entry = Vote(
                    user_name=escape(user_name)[:100],
                    value=str(val),
                    session_id=new_session.id
                )
                db.session.add(vote_entry)

                if str(val).replace('.', '', 1).isdigit():
                    total_value += float(val)
                    vote_count += 1

            if vote_count > 0:
                new_session.final_average = total_value / vote_count
            db.session.commit()

    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('reset')
def reset(data):
    room_id = data['room_id']
    with change_room(room_id) as state:
        if not state: return

        if state['active'] and request.sid != state['admin_sid']:
            return

        state['active'] = False
        state['ticket_key'] = "Waiting..."
        state['ticket_url'] = None
        state['votes'] = {}
        state['revealed'] = False

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
    
    # Escape the emoji for security (custom emojis are already validated via allowlist)
    safe_emoji = escape(emoji)
    
    sender_name = participant.get('name') or session.get('user_name', 'Anon')
    # Broadcast the reaction to everyone (including the sender)
    emit('trigger_reaction', {
        'emoji': safe_emoji,
        'sender': sender_name
    }, to=room_id)
