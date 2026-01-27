import os
from dotenv import load_dotenv
from flask import Flask
from flask_socketio import SocketIO

load_dotenv()

base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, '../templates')
static_dir = os.path.join(base_dir, '../static')

app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'p}^Pa11FNghwe-Ua_-^i')
app.config['REDIS_URL'] = os.environ.get('REDIS_URL', '')
app.config['ADMIN_USERNAME'] = os.environ.get('ADMIN_USERNAME', None)
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD', None)

redis_client = None
use_redis = False

if app.config['REDIS_URL']:
    try:
        from redis import Redis
        redis_client = Redis.from_url(app.config['REDIS_URL'])
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

app.config['USE_REDIS'] = use_redis

# Initialize SocketIO with or without message queue
if use_redis:
    socketio = SocketIO(app, message_queue=app.config['REDIS_URL'], async_mode='gevent')
else:
    socketio = SocketIO(app, async_mode='gevent')

from src.routes import main, rooms, votes, timer, healthcheck, queue, roles, admin
