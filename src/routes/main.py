import random
import uuid
from flask import jsonify, redirect, render_template, request, session, url_for
from src import app
from src.model import TicketSession
from src.store import room_exists, save_room
from src.state import get_initial_room_state, DECKS
import os

WORDS = []
try:
    # Assuming 'res' is at the project root, one level up from 'src'
    names_path = os.path.join(app.root_path, '..', 'res', 'names.txt')
    
    with open(names_path, 'r', encoding='utf-8') as f:
        # Load words, stripping whitespace and empty lines
        WORDS = [line.strip() for line in f if line.strip()]
        
    print(f"Loaded {len(WORDS)} words for room ID generation.")
except Exception as e:
    print(f"Warning: Could not load names.txt ({e}). Fallback to UUIDs.")

# --- Routes ---
@app.route('/')
def index():
    # 1. Server-Side Check: If logged in, redirect immediately
    if 'room_id' in session and 'user_name' in session:
        room_id = session['room_id']
        # Ensure room still exists in memory (in case server restarted)
        if room_exists(room_id):
            return redirect(url_for('room', room_id=room_id))
    
    prefill_room_id = request.args.get('room_id')
    
    # Otherwise, show login
    return render_template('login.html',
                           prefill_room_id=prefill_room_id,
                           decks=DECKS)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    action = data.get('action') # 'create' or 'join'
    name = data.get('name')
    role = data.get('role')
    room_id = data.get('room_id')
    deck_type = data.get('deck_type', 'fibonacci')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Logic for Creating a Room
    if action == 'create':
        room_id = generate_room_id()

        attempts = 0
        while room_exists(room_id) and attempts < 10:
            room_id = generate_room_id()
            attempts += 1

        save_room(room_id, get_initial_room_state(deck_type))
    
    # Logic for Joining a Room
    elif action == 'join':
        if room_id:
            room_id = room_id.strip().lower()

        if not room_id or not room_exists:
            return jsonify({'error': 'Room not found'}), 404
            
    # 2. Set Server-Side Session (Cookie)
    session['room_id'] = room_id
    session['user_name'] = name
    session['user_role'] = role
    
    # Tell frontend where to go
    return jsonify({'redirect': url_for('room', room_id=room_id)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/room/<room_id>')
def room(room_id):
    # Security: If trying to access room URL without session, kick them out
    if 'room_id' not in session or session['room_id'] != room_id:
        return redirect(url_for('index', room_id=room_id))
        
    return render_template('vote.html', room_id=room_id, user_role=session.get('user_role'))


@app.route('/history')
def history():
    filter_room_id = request.args.get('room_id')
    
    # Allow filtering by the current room automatically if not specified
    if not filter_room_id and 'room_id' in session:
        filter_room_id = session['room_id']

    query = TicketSession.query
    if filter_room_id:
        query = query.filter_by(room_id=filter_room_id)
    
    sessions = query.order_by(TicketSession.timestamp.desc()).all()

    return jsonify([{
            'timestamp': s.timestamp.strftime('%Y-%m-%d %H:%M'),
            'ticket_key': s.ticket_key,
            'type': 'Public' if s.is_public else 'Private', # Human readable
            'average': s.final_average,
            # Return list of values for the frontend to format (e.g. ['5', '5', '8'])
            'votes': [v.value for v in s.votes] 
        } for s in sessions])

def generate_room_id():
    """Generates a random 3-word dashed string (e.g. 'apple-bridge-candle')."""
    if len(WORDS) >= 3:
        # Pick 3 unique words from the list
        selected = random.sample(WORDS, 3)
        return "-".join(selected)
    else:
        # Fallback if file is missing or has < 3 words
        return str(uuid.uuid4())