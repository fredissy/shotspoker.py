from flask import request
from flask_socketio import emit
from src import socketio, db
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

    # Save to DB (Persistence)
    # Note: We are saving to a global table.
    # Ideally, you'd add 'room_id' to the TicketSession model.
    votes_list = state['votes'].values()
    if votes_list:
        new_session = TicketSession(ticket_key=state['ticket_key'], is_public=state['is_public'])
        db.session.add(new_session)
        db.session.commit()

        total, count = 0, 0
        for v in votes_list:
            # Look up name from participants using the SID logic or store name in vote
            # Simplified: we just grab the value here.
            # In a real app, map SID -> Name for the DB record.
            # For this demo, we'll skip saving individual names to DB to keep code short,
            # or you can look up the user name from state['participants']
            pass # (Add your DB saving logic here)
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
