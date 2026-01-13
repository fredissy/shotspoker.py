import os
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

# Calculate path to templates folder in the root directory
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Import models to ensure they are registered with SQLAlchemy
from src import model

# Import routes/events to ensure they are registered
from src.routes import main
from src.routes import rooms
from src.routes import votes

with app.app_context():
    db.create_all()
