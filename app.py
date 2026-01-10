import os
import uuid
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room # <--- NEW imports
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# --- Database Models (Unchanged) ---
# Note: For a real multi-team app, you would add 'room_id' to these models
# to filter history by team. For now, history remains global.
class TicketSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_key = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_public = db.Column(db.Boolean, default=True)
    final_average = db.Column(db.Float, nullable=True)
    votes = db.relationship('Vote', backref='session', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.Integer, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('ticket_session.id'), nullable=False)

with app.app_context():
    db.create_all()

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

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    sessions = TicketSession.query.order_by(TicketSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions)

# --- Socket Events ---

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

# --- Voting Logic (Now Room Aware) ---

@socketio.on('start_vote')
def start_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    state['active'] = True
    state['ticket_key'] = data['ticket_key']
    state['is_public'] = data['is_public']
    state['votes'] = {}
    state['revealed'] = False
    # Admin can change dynamically, or we stick to original creator. 
    # Let's update admin to whoever started the vote to be flexible.
    state['admin_sid'] = request.sid 
    
    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('cast_vote')
def cast_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    if not state['active'] or state['revealed']: return
    
    # Observer Check
    participant = state['participants'].get(request.sid)
    if participant and participant['role'] == 'observer': return

    state['votes'][request.sid] = {'value': int(data['vote_value'])}
    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('reveal_vote')
def reveal_vote(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    # Admin Check
    if state['active'] and request.sid != state['admin_sid']:
        return

    state['revealed'] = True
    
    # Save to DB (Persistence)
    # Note: We are saving to a global table. 
    # Ideally, you'd add 'room_id' to the TicketSession model.
    votes_list = state['votes'].values()
    if votes_list:
        new_session = TicketSession(ticket_key=state['ticket_key'], is_public=state['is_public'])
        db.session.add(new_session)
        db.session.commit()
        
        total, count = 0, 0
        for v in votes_list:
            # Look up name from participants using the SID logic or store name in vote
            # Simplified: we just grab the value here. 
            # In a real app, map SID -> Name for the DB record.
            # For this demo, we'll skip saving individual names to DB to keep code short,
            # or you can look up the user name from state['participants']
            pass # (Add your DB saving logic here)
        db.session.commit()

    emit('state_update', _get_public_state(room_id), to=room_id)

@socketio.on('reset')
def reset(data):
    room_id = data['room_id']
    state = rooms.get(room_id)
    if not state: return

    if state['active'] and request.sid != state['admin_sid']:
        return

    state['active'] = False
    state['ticket_key'] = "Waiting..."
    state['votes'] = {}
    state['revealed'] = False
    emit('state_update', _get_public_state(room_id), to=room_id)


def _get_public_state(room_id):
    state = rooms[room_id]
    
    # ... Same logic as before, just using 'state' variable ...
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

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)