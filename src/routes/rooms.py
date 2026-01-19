from flask import request, session
from flask_socketio import emit, join_room
from src import socketio
from src.state import _get_public_state
from src.store import get_room, room_exists, save_room

@socketio.on('connect')
def handle_connect():
    # 1. Read identity from the Server-Side Session (Cookie)
    user_name = session.get('user_name')
    room_id = session.get('room_id')
    user_role = session.get('user_role')
    user_avatar = session.get('user_avatar', '👤')

    # 2. If valid session, auto-join the socket room
    if user_name and room_id and room_exists(room_id):
        join_room(room_id)
        
        state = get_room(room_id)

        # Fix possible stale sessions: remove any existing entries for this user
        stale_sids = [sid for sid, p in state['participants'].items() if p['name'] == user_name]
        for sid in stale_sids:
            del state['participants'][sid]
        
        # Add to participants list in memory
        state['participants'][request.sid] = {
            'name': user_name, 
            'avatar': user_avatar,
            'role': user_role
        }
        
        # If this is the only user, make them admin (simple logic)
        if len(state['participants']) == 1:
            state['admin_sid'] = request.sid

        save_room(room_id, state)

        # Broadcast update
        emit('state_update', _get_public_state(room_id, state), to=room_id)
        
    else:
        # User has no session cookie (or server restarted), disconnect them
        return False 

@socketio.on('disconnect')
def handle_disconnect():
    room_id = session.get('room_id')
    
    if room_id:
        state = get_room(room_id)
        
        # 3. Check if room exists and user is in it
        if state and request.sid in state['participants']:
            del state['participants'][request.sid]
            
            # 4. Save the updated state back to Redis
            save_room(room_id, state)
            emit('state_update', _get_public_state(room_id, state), to=room_id)
