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

    min_val = None
    max_val = None

    if state['revealed']:
        numeric_votes = []
        for v in state['votes'].values():
            val_str = str(v['value'])
            if val_str.replace('.', '', 1).isdigit():
                numeric_votes.append(float(val_str))
        
        if numeric_votes:
            min_val = min(numeric_votes)
            max_val = max(numeric_votes)

    for sid, p in state['participants'].items():
        vote_data = state['votes'].get(p['name'])
        status = "Waiting"
        display_val = None
        is_min = False
        is_max = False

        if p['role'] == 'observer':
            display_val = "👀"
        elif vote_data:
            if state['revealed']:
                raw_val = vote_data['value']
                display_val = raw_val
                vote_counts[display_val] = vote_counts.get(display_val, 0) + 1

                if str(raw_val).replace('.', '', 1).isdigit():
                    float_val = float(raw_val)
                    if float_val == min_val: is_min = True
                    if float_val == max_val: is_max = True
            else:
                display_val = "✅"

        user_list.append({
            'name': p['name'],
            'role': p['role'],
            'display_value': display_val,
            'is_min': is_min,
            'is_max': is_max
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
