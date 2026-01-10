# --- Global State ---
# Structure: { 'room_uuid': { active: False, ticket_key: '...', ... } }
rooms = {}

def get_initial_room_state():
    return {
        'active': False,
        'ticket_key': "Waiting...",
        'is_public': True,
        'votes': {},
        'revealed': False,
        'admin_sid': None,
        'participants': {}
    }

def _get_public_state(room_id):
    state = rooms[room_id]

    user_list = []
    vote_counts = {}

    for sid, p in state['participants'].items():
        vote_data = state['votes'].get(sid)
        status = "Waiting"
        display_val = None

        if p['role'] == 'observer':
            display_val = "👀"
        elif vote_data:
            if state['revealed']:
                display_val = vote_data['value']
                vote_counts[display_val] = vote_counts.get(display_val, 0) + 1
            else:
                display_val = "✅"

        user_list.append({
            'name': p['name'],
            'role': p['role'],
            'display_value': display_val,
        })

    return {
        'room_id': room_id, # useful for UI
        'active': state['active'],
        'ticket_key': state['ticket_key'],
        'is_public': state['is_public'],
        'revealed': state['revealed'],
        'participants': user_list,
        'distribution': vote_counts,
        'admin_sid': state['admin_sid']
    }
