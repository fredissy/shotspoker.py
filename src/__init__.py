import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

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

app.config['REDIS_URL'] = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

redis_client = Redis.from_url(app.config['REDIS_URL'])

socketio = SocketIO(app,
                    message_queue=app.config['REDIS_URL'],
                    async_mode='gevent')

from src import model
from src.routes import main, rooms, votes, timer, healthcheck

with app.app_context():
    db.create_all()
