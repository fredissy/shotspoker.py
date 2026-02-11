import os
from dotenv import load_dotenv
from flask import Flask, request
from flask_babel import Babel
from flask_migrate import Migrate
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

app.config['REDIS_URL'] = os.environ.get('REDIS_URL', '')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', None)
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', None)


def get_locale():
    # You can add logic here to check session or user preference
    return request.accept_languages.best_match(['en', 'es'])


app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
babel = Babel(app, locale_selector=get_locale)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Try to connect to Redis, fallback to in-memory if unavailable
redis_client = None
use_redis = False

if app.config['REDIS_URL']:
    try:
        from redis import Redis
        redis_client = Redis.from_url(app.config['REDIS_URL'])
        # Test connection
        redis_client.ping()
        use_redis = True
        print("✓ Using Redis for state storage and SocketIO message queue")
    except Exception as e:
        print(f"⚠ Redis connection failed: {e}")
        print("✓ Falling back to in-memory storage (single instance only)")
        redis_client = None
        use_redis = False
else:
    print("✓ No REDIS_URL configured, using in-memory storage (single instance only)")

# Store the flag in app config for easy access
app.config['USE_REDIS'] = use_redis

# Initialize SocketIO with or without message queue
if use_redis:
    socketio = SocketIO(app,
                        message_queue=app.config['REDIS_URL'],
                        async_mode='gevent')
else:
    # No message queue - single instance mode
    socketio = SocketIO(app, async_mode='gevent')

from src import model
from src.routes import main, rooms, votes, timer, healthcheck, queue, roles, admin
