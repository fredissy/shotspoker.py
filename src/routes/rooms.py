import uuid
from flask import request
from flask_socketio import emit, join_room
from src import socketio
from src.state import rooms, get_initial_room_state, _get_public_state

# --- Socket Events for Rooms ---

@socketio.on('create_room')
def create_room(data):
    room_id = str(uuid.uuid4())
    rooms[room_id] = get_initial_room_state()

    # Add creator to the room
    _join_logic(room_id, data['name'], data['role'])

    # Send the Room ID back to the user so they can share it
    emit('room_created', {'room_id': room_id, 'msg': 'Room created! Share this ID.'})

@socketio.on('join_room_request')
def join_room_request(data):
    room_id = data['room_id'].strip()
    if room_id not in rooms:
        emit('error_msg', {'msg': 'Room not found. Check the ID.'})
        return

    _join_logic(room_id, data['name'], data['role'])
    emit('room_joined', {'room_id': room_id})

def _join_logic(room_id, name, role):
    join_room(room_id)  # SocketIO function to put connection in a "room"

    # Update State
    state = rooms[room_id]
    state['participants'][request.sid] = {'name': name, 'role': role}

    # If this is the first user, make them admin
    if len(state['participants']) == 1:
        state['admin_sid'] = request.sid

    # Broadcast ONLY to this room
    emit('state_update', _get_public_state(room_id), to=room_id)


@socketio.on('disconnect')
def handle_disconnect():
    # Find which room this user was in
    for room_id, state in rooms.items():
        if request.sid in state['participants']:
            del state['participants'][request.sid]
            # Clean up empty rooms if desired
            # if not state['participants']: del rooms[room_id]
            emit('state_update', _get_public_state(room_id), to=room_id)
            break
