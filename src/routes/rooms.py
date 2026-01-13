from flask import request, session
from flask_socketio import emit, join_room
from src import socketio
from src.state import rooms, _get_public_state

@socketio.on('connect')
def handle_connect():
    # 1. Read identity from the Server-Side Session (Cookie)
    user_name = session.get('user_name')
    room_id = session.get('room_id')
    user_role = session.get('user_role')

    # 2. If valid session, auto-join the socket room
    if user_name and room_id and room_id in rooms:
        join_room(room_id)
        
        # Add to participants list in memory
        state = rooms[room_id]
        state['participants'][request.sid] = {
            'name': user_name, 
            'role': user_role
        }
        
        # If this is the only user, make them admin (simple logic)
        if len(state['participants']) == 1:
            state['admin_sid'] = request.sid

        # Broadcast update
        emit('state_update', _get_public_state(room_id), to=room_id)
        
    else:
        # User has no session cookie (or server restarted), disconnect them
        return False 

@socketio.on('disconnect')
def handle_disconnect():
    # Clean up logic
    for room_id, state in rooms.items():
        if request.sid in state['participants']:
            del state['participants'][request.sid]
            emit('state_update', _get_public_state(room_id), to=room_id)
            break