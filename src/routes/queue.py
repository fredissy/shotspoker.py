from flask_socketio import emit
from src.state import _get_public_state
from src.store import get_room, change_room
from src import socketio
from src.utils import clean_jira_key

@socketio.on('queue_add')
def queue_add(data):
    room_id = data['room_id']
    new_tickets = data.get('tickets', [])
    
    with change_room(room_id) as state:
        if not state: return

        # Append only new unique tickets to avoid duplicates
        # We use a set for fast lookup of current queue
        current_set = set(state['queue'])
        queue_urls = state.setdefault('queue_urls', {})
        
        for ticket in new_tickets:
            raw_ticket = ticket.strip()
            clean_ticket = clean_jira_key(raw_ticket)[:50]
            if clean_ticket and clean_ticket not in current_set:
                state['queue'].append(clean_ticket)
                current_set.add(clean_ticket) # Update local set for next iteration
            if clean_ticket and raw_ticket.startswith(('http://', 'https://')):
                queue_urls[clean_ticket] = raw_ticket
                
    emit('state_update', _get_public_state(room_id, state), to=room_id)

@socketio.on('queue_remove')
def queue_remove(data):
    room_id = data['room_id']
    ticket_to_remove = data.get('ticket')
    
    with change_room(room_id) as state:
        if not state: return
        
        if ticket_to_remove in state['queue']:
            state['queue'].remove(ticket_to_remove)
            state.get('queue_urls', {}).pop(ticket_to_remove, None)
            
    emit('state_update', _get_public_state(room_id, state), to=room_id)
