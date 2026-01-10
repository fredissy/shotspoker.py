from flask import render_template
from src import app
from src.model import TicketSession

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    sessions = TicketSession.query.order_by(TicketSession.timestamp.desc()).all()
    return render_template('history.html', sessions=sessions)
