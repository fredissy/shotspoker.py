import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

# Calculate path to templates folder in the root directory
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)

database_url = os.environ.get('DATABASE_URL', 'sqlite:///poker.db')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'p}^Pa11FNghwe-Ua_-^i')

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='eventlet')

# Import models to ensure they are registered with SQLAlchemy
from src import model

# Import routes/events to ensure they are registered
from src.routes import main, rooms, votes, timer

with app.app_context():
    db.create_all()
