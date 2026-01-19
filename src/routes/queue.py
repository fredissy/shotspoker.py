from flask_socketio import emit
from src.state import _get_public_state
from src.store import get_room, change_room
from src import socketio, db

@socketio.on('queue_add')
def queue_add(data):
    room_id = data['room_id']
    new_tickets = data.get('tickets', [])
    
    with change_room(room_id) as state:
        if not state: return

        # Append only new unique tickets to avoid duplicates
        # We use a set for fast lookup of current queue
        current_set = set(state['queue'])
        
        for ticket in new_tickets:
            clean_ticket = ticket.strip()
            if clean_ticket and clean_ticket not in current_set:
                state['queue'].append(clean_ticket)
                current_set.add(clean_ticket) # Update local set for next iteration
                
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('queue_remove')
def queue_remove(data):
    room_id = data['room_id']
    ticket_to_remove = data.get('ticket')
    
    with change_room(room_id) as state:
        if not state: return
        
        if ticket_to_remove in state['queue']:
            state['queue'].remove(ticket_to_remove)
            
    emit('state_update', _get_public_state(room_id, state), to=room_id)
