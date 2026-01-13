from flask import render_template, request
from src import app
from src.model import TicketSession

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():

    filter_room_id = request.args.get('room_id')
    query = TicketSession.query

    if filter_room_id:
        query = query.filter_by(room_id=filter_room_id)
    
    sessions = query.order_by(TicketSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions)
