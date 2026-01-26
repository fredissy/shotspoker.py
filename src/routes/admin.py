from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from src import app, socketio, redis_client
from src.store import get_room, room_exists, _memory_store, _memory_store_lock

# Helper to format time
def format_ts(ts):
    if not ts: return "-"
    return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

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
    
    # Add storage mode info for admin visibility
    storage_mode = 'Redis' if app.config['USE_REDIS'] else 'In-Memory'
    
    return render_template('admin.html.j2', rooms=rooms_data, storage_mode=storage_mode)

@app.route('/admin/delete/<room_id>', methods=['POST'])
def delete_room(room_id):
    if room_exists(room_id):
        # 1. Notify all users in that room to leave
        socketio.emit('room_closed', {'msg': 'Room deleted by admin'}, to=room_id)
        
        # 2. Delete from storage (Redis or memory)
        delete_room_data(room_id)
        
    return redirect(url_for('admin_panel'))