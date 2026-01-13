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

    state['votes'][request.sid] = {'value': int(data['vote_value'])}
    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('reveal_vote')
def reveal_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    # Admin Check
    if state['active'] and request.sid != state['admin_sid']:
        return

    state['revealed'] = True

    if state['votes']:
        # 1. Create the Session Record
        new_session = TicketSession(
            room_id=room_id,  # <--- Saving the Room ID
            ticket_key=state['ticket_key'],
            is_public=state['is_public']
        )
        db.session.add(new_session)
        db.session.commit() # Commit to get the new_session.id

        # 2. Save Individual Votes
        total_value = 0
        vote_count = 0

        # We need the SID to look up the User Name from 'participants'
        for sid, vote_data in state['votes'].items():
            participant = state['participants'].get(sid)
            # Fallback if user disconnected right before reveal
            user_name = participant['name'] if participant else "Unknown"
            val = vote_data['value']

            vote_entry = Vote(
                user_name=user_name,
                value=val,
                session_id=new_session.id
            )
            db.session.add(vote_entry)
            
            total_value += val
            vote_count += 1
        
        # 3. Calculate Average
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
