import time
from flask_socketio import emit
from src import socketio
from src.state import _get_public_state
from src.store import change_room

@socketio.on('start_timer')
def start_timer(data):
    room_id = data['room_id']
    duration = data.get('duration', 30) # Default 30 seconds
    with change_room(room_id) as state:
        if not state: return
        state['timer_end'] = time.time() + duration

    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('stop_timer')
def stop_timer(data):
    room_id = data['room_id']
    with change_room(room_id) as state:
        if not state: return
        state['timer_end'] = None

    emit('state_update', _get_public_state(room_id, state), to=room_id)
