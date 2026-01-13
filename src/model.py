from src import db
from datetime import datetime

# --- Database Models ---
# Note: For a real multi-team app, you would add 'room_id' to these models
# to filter history by team. For now, history remains global.
class TicketSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(36), nullable=False)
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
