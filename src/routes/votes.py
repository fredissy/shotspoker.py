from flask import request
from flask_socketio import emit
from src import socketio, db
from src import state
from src.state import rooms, _get_public_state
from src.model import TicketSession, Vote

# --- Voting Logic (Now Room Aware) ---

@socketio.on('start_vote')
def start_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    state['active'] = True
    state['ticket_key'] = data['ticket_key']
    state['is_public'] = data['is_public']
    state['votes'] = {}
    state['revealed'] = False
    # Admin can change dynamically, or we stick to original creator.
    # Let's update admin to whoever started the vote to be flexible.
    state['admin_sid'] = request.sid

    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('cast_vote')
def cast_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    if not state['active'] or state['revealed']: return

    # Observer Check
    participant = state['participants'].get(request.sid)
    if participant and participant['role'] == 'observer': return

    user_name = participant['name']

    state['votes'][user_name] = {'value': data['vote_value']}
    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('reveal_vote')
def reveal_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
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

            vote_entry = Vote(
                user_name=user_name, # We already have the name!
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

    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('reset')
def reset(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    if state['active'] and request.sid != state['admin_sid']:
        return

    state['active'] = False
    state['ticket_key'] = "Waiting..."
    state['votes'] = {}
    state['revealed'] = False
    emit('state_update', _get_public_state(room_id), to=room_id)
