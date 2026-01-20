# --- Global State ---
from collections import Counter

DECKS = {
    'fibonacci': ['0', '1', '2', '3', '5', '8', '13', '21', '∞', '?', '☕'],
    'modified': ['0', '0.5', '1', '2', '3', '5', '8', '13', '20', '40', '100', '∞', '?', '☕'],
    'tshirt': ['XS', 'S', 'M', 'L', 'XL', 'XXL', '?', '☕'],
    'powers': ['0', '1', '2', '4', '8', '16', '32', '64', '?', '☕']
}

def get_initial_room_state(deck_type='fibonacci'):

    selected_deck = DECKS.get(deck_type, DECKS['fibonacci'])

    return {
        'active': False,
        'ticket_key': "Waiting...",
        'is_public': True,
        'votes': {},
        'revealed': False,
        'admin_sid': None,
        'participants': {},
        'queue': [],
        'timer_end': None,
        'deck_config': selected_deck
    }

def _get_public_state(room_id, state):
    user_list = []
    online_names = set()

    vote_counts = {} 
    numeric_votes = []
    raw_values = []
    min_val = None
    max_val = None
    average = None
    agreement = 0

    if state['revealed']:
        # Iterate over the VOTES directly (The source of truth)
        for voter_name, vote_data in state['votes'].items():
            val_str = str(vote_data['value'])
            
            # Add to graph data
            vote_counts[val_str] = vote_counts.get(val_str, 0) + 1
            
            raw_values.append(val_str)
            if val_str.replace('.', '', 1).isdigit():
                numeric_votes.append(float(val_str))
        
        count_votes = len(raw_values)
        if count_votes > 0:
            if numeric_votes:
                min_val = min(numeric_votes)
                max_val = max(numeric_votes)
                average = round(sum(numeric_votes) / len(numeric_votes), 1)
            
            if raw_values:
                most_common = Counter(raw_values).most_common(1)
                if most_common:
                    top_vote_count = most_common[0][1]
                    agreement = int((top_vote_count / count_votes) * 100)

    for sid, p in state['participants'].items():
        online_names.add(p['name'])
        vote_data = state['votes'].get(p['name'])
        display_val = None
        is_min = False
        is_max = False

        if p['role'] == 'observer':
            display_val = "👀"
        elif vote_data:
            if state['revealed']:
                raw_val = vote_data['value']
                display_val = raw_val

                if str(raw_val).replace('.', '', 1).isdigit():
                    float_val = float(raw_val)
                    if float_val == min_val: is_min = True
                    if float_val == max_val: is_max = True
            else:
                display_val = "✅"

        user_list.append({
            'name': p['name'],
            'role': p['role'],
            'avatar': p.get('avatar', '👤'),
            'display_value': display_val,
            'is_min': is_min,
            'is_max': is_max,
            'status': 'online'
        })

    for voter_name, vote_data in state['votes'].items():
        if voter_name not in online_names:
            # This person voted but is gone. Show them!
            
            display_val = None
            is_min = False
            is_max = False
            
            if state['revealed']:
                raw_val = vote_data['value']
                display_val = raw_val
                # Re-run min/max check for this offline user
                if str(raw_val).replace('.', '', 1).isdigit():
                    float_val = float(raw_val)
                    if float_val == min_val: is_min = True
                    if float_val == max_val: is_max = True
            else:
                display_val = "✅"

            user_list.append({
                'name': voter_name,
                'role': 'voter',
                'avatar': '👻',
                'display_value': display_val,
                'is_min': is_min,
                'is_max': is_max,
                'status': 'offline'
            })

    return {
        'room_id': room_id,
        'active': state['active'],
        'ticket_key': state['ticket_key'],
        'is_public': state['is_public'],
        'revealed': state['revealed'],
        'participants': user_list,
        'distribution': vote_counts,
        'admin_sid': state['admin_sid'],
        'queue': state['queue'],
        'timer_end': state.get('timer_end'),
        'deck': state['deck_config'],
        'stats': {
            'average': average,
            'agreement': agreement,
            'min': min_val,
            'max': max_val
        }
    }
