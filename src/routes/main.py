import uuid
from flask import jsonify, redirect, render_template, request, session, url_for
from src import app
from src.model import TicketSession
from src.state import get_initial_room_state, rooms

# --- Routes ---
@app.route('/')
def index():
    # 1. Server-Side Check: If logged in, redirect immediately
    if 'room_id' in session and 'user_name' in session:
        room_id = session['room_id']
        # Ensure room still exists in memory (in case server restarted)
        if room_id in rooms:
            return redirect(url_for('room', room_id=room_id))
    
    # Otherwise, show login
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    action = data.get('action') # 'create' or 'join'
    name = data.get('name')
    role = data.get('role')
    room_id = data.get('room_id')

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Logic for Creating a Room
    if action == 'create':
        room_id = str(uuid.uuid4())
        rooms[room_id] = get_initial_room_state()
    
    # Logic for Joining a Room
    elif action == 'join':
        if not room_id or room_id not in rooms:
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
        return redirect(url_for('index'))
        
    return render_template('vote.html', room_id=room_id, user_role=session.get('user_role'))

@app.route('/history')
def history():

    filter_room_id = request.args.get('room_id')
    query = TicketSession.query

    if filter_room_id:
        query = query.filter_by(room_id=filter_room_id)
    
    sessions = query.order_by(TicketSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions, current_room=filter_room_id)
