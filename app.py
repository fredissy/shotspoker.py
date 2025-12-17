import os
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app)

# --- Database Models (Bonus: Persistence) ---
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

# Create DB tables
with app.app_context():
    db.create_all()

# --- Global State (In-memory for active session) ---
current_state = {
    'active': False,
    'ticket_key': "Waiting...",
    'is_public': True,
    'votes': {}, 
    'revealed': False,
    'admin_sid': None  # <--- NEW: Track who started the vote
}

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    # Fetch completed sessions, newest first
    sessions = TicketSession.query.order_by(TicketSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions)

# --- Socket Events ---
@socketio.on('connect')
def handle_connect():
    # Send current state to new user
    emit('state_update', _get_public_state())

@socketio.on('start_vote')
def start_vote(data):
    # Anyone can START a vote, becoming the new Admin
    current_state['active'] = True
    current_state['ticket_key'] = data['ticket_key']
    current_state['is_public'] = data['is_public']
    current_state['votes'] = {}
    current_state['revealed'] = False
    current_state['admin_sid'] = request.sid
    
    emit('state_update', _get_public_state(), broadcast=True)
    emit('notification', {'msg': f"Vote started by Admin (ID: {request.sid[-4:]})"}, broadcast=True)

@socketio.on('cast_vote')
def cast_vote(data):
    if not current_state['active'] or current_state['revealed']:
        return
    
    user_name = data['user_name']
    vote_val = int(data['vote_value'])
    
    # Store vote
    current_state['votes'][request.sid] = {'name': user_name, 'value': vote_val}
    
    # Notify everyone that THIS user voted (without revealing value)
    emit('state_update', _get_public_state(), broadcast=True)

@socketio.on('reveal_vote')
def reveal_vote():
    if current_state['active'] and request.sid != current_state['admin_sid']:
        emit('notification', {'msg': "⛔ Only the vote starter can reveal results!"})
        return

    if not current_state['active']:
        return

    current_state['revealed'] = True
    
    # --- Save to DB (Persistence) ---
    votes_list = current_state['votes'].values()
    if votes_list:
        new_session = TicketSession(
            ticket_key=current_state['ticket_key'],
            is_public=current_state['is_public']
        )
        db.session.add(new_session)
        db.session.commit()
        
        total = 0
        count = 0
        for v in votes_list:
            vote_entry = Vote(user_name=v['name'], value=v['value'], session_id=new_session.id)
            db.session.add(vote_entry)
            total += v['value']
            count += 1
        
        if count > 0:
            new_session.final_average = total / count
        db.session.commit()
    # --------------------------------

    emit('state_update', _get_public_state(), broadcast=True)

@socketio.on('reset')
def reset():
    if current_state['active'] and request.sid != current_state['admin_sid']:
            emit('notification', {'msg': "⛔ Only the vote starter can reset!"})
            return

    current_state['active'] = False
    current_state['ticket_key'] = "Waiting..."
    current_state['votes'] = {}
    current_state['revealed'] = False
    emit('state_update', _get_public_state(), broadcast=True)

def _get_public_state():
    """
    Sanitizes the state sent to clients.
    If not revealed, hides vote values.
    """
    public_votes = []
    vote_counts = {} # For pie chart (distribution)
    
    for v in current_state['votes'].values():
        val = v['value']
        # If not revealed, mask the value
        display_val = val if current_state['revealed'] else "?"
        public_votes.append({'name': v['name'], 'value': display_val})
        
        # Calculate distribution for charts (only if revealed)
        if current_state['revealed']:
            vote_counts[val] = vote_counts.get(val, 0) + 1

    return {
        'active': current_state['active'],
        'ticket_key': current_state['ticket_key'],
        'is_public': current_state['is_public'],
        'revealed': current_state['revealed'],
        'votes': public_votes,
        'distribution': vote_counts,
        'admin_sid': current_state['admin_sid']
    }

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
