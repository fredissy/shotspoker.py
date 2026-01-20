from flask import request, session
from flask_socketio import emit
from src import socketio
from src.state import _get_public_state
from src.store import change_room

@socketio.on('switch_role')
def switch_role(data):
    room_id = data['room_id']
    new_role = data['role'] # 'voter' or 'observer'
    
    # Validate input
    if new_role not in ['voter', 'observer']:
        return

    with change_room(room_id) as state:
        if not state: return
        
        # 1. Update Participant in Room State
        if request.sid in state['participants']:
            state['participants'][request.sid]['role'] = new_role
            
            # 2. If becoming observer, remove existing vote for current ticket
            user_name = state['participants'][request.sid]['name']
            if new_role == 'observer' and user_name in state['votes']:
                del state['votes'][user_name]

    # 3. Update Session (so it persists on page reload)
    session['user_role'] = new_role
    
    emit('state_update', _get_public_state(room_id, state), to=room_id)
