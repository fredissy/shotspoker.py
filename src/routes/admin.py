from datetime import datetime, timedelta
from functools import wraps
from flask import Response, render_template, redirect, request, url_for
from src import app, socketio, redis_client
from sqlalchemy import func
from src.store import get_room, room_exists, _memory_store, _memory_store_lock
from src.model import TicketSession, Vote, db

def format_ts(ts):
    if not ts: return "-"
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
def check_auth(username, password):
    """Checks if username/password combination is valid."""
    return username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def get_all_room_ids():
    """Get all room IDs from Redis or memory."""
    if app.config['USE_REDIS']:
        # Scan Redis for all keys starting with "room:"
        room_ids = []
        for key in redis_client.scan_iter("room:*"):
            room_key = key.decode('utf-8')
            room_id = room_key.replace("room:", "")
            room_ids.append(room_id)
        return room_ids
    else:
        # Get from in-memory store
        with _memory_store_lock:
            room_ids = []
            for key in _memory_store.keys():
                if key.startswith("room:"):
                    room_id = key.replace("room:", "")
                    room_ids.append(room_id)
            return room_ids

def delete_room_data(room_id):
    """Delete room data from Redis or memory."""
    if app.config['USE_REDIS']:
        redis_client.delete(f"room:{room_id}")
    else:
        # Delete from in-memory store
        key = f"room:{room_id}"
        with _memory_store_lock:
            if key in _memory_store:
                del _memory_store[key]

@app.route('/admin')
@requires_auth
def admin_panel():
    rooms_data = []
    
    # Get all room IDs from appropriate storage
    room_ids = get_all_room_ids()
    
    for room_id in room_ids:
        state = get_room(room_id)
        if state:
            # Calculate counts
            participant_count = len(state.get('participants', {}))
            
            rooms_data.append({
                'id': room_id,
                'participants': participant_count,
                'created_at': format_ts(state.get('created_at')),
                'last_updated': format_ts(state.get('last_updated')),
                'ticket': state.get('ticket_key', '-')
            })
    
    # Sort by most recently updated
    rooms_data.sort(key=lambda x: x['last_updated'], reverse=True)

    search_ticket = request.args.get('ticket', '').strip()
    ticket_history = []

    if search_ticket:
        # Query DB for sessions matching the ticket key (case-insensitive partial match)
        sessions = TicketSession.query.filter(
            TicketSession.ticket_key.ilike(f"%{search_ticket}%")
        ).order_by(TicketSession.timestamp.desc()).all()
        
        for s in sessions:
            ticket_history.append({
                'id': s.id,
                'room_id': s.room_id,
                'ticket_key': s.ticket_key,
                'timestamp': s.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'final_average': round(s.final_average, 2) if s.final_average else '-',
                # Extract individual votes for this session
                'votes': [{'user': v.user_name, 'value': v.value} for v in s.votes]
            })
    
    # Add storage mode info for admin visibility
    storage_mode = 'Redis' if app.config['USE_REDIS'] else 'In-Memory'

    # 2. Global Stats
    total_sessions = db.session.query(func.count(TicketSession.id)).scalar() or 0
    total_votes = db.session.query(func.count(Vote.id)).scalar() or 0

    # 3. Chart Data: Sessions per day for the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Note: Exact date extraction depends slightly on your DB dialect (Postgres uses cast to Date)
    daily_sessions = db.session.query(
        func.cast(TicketSession.timestamp, db.Date).label('date'),
        func.count(TicketSession.id).label('count')
    ).filter(
        TicketSession.timestamp >= seven_days_ago
    ).group_by(
        func.cast(TicketSession.timestamp, db.Date)
    ).order_by('date').all()

    # Format for Chart.js
    chart_labels = [row.date.strftime('%b %d') for row in daily_sessions]
    chart_data = [row.count for row in daily_sessions]
    
    return render_template('admin.html.j2',
                           rooms=rooms_data,
                           storage_mode=storage_mode,
                           total_sessions=total_sessions,
                           total_votes=total_votes,
                           chart_labels=chart_labels,
                           chart_data=chart_data,
                           search_ticket=search_ticket,
                           ticket_history=ticket_history
                           )

@app.route('/admin/delete/<room_id>', methods=['POST'])
@requires_auth
def delete_room(room_id):
    if room_exists(room_id):
        # 1. Notify all users in that room to leave
        socketio.emit('room_closed', {'msg': 'Room deleted by admin'}, to=room_id)
        
        # 2. Delete from storage (Redis or memory)
        delete_room_data(room_id)
        
    return redirect(url_for('admin_panel'))