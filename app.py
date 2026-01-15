from gevent import monkey
monkey.patch_all()
from src import app, socketio

if __name__ == "__main__":
    print("🚀 Starting Local Development Server...")
    # debug=True allows hot-reloading when you change code
    socketio.run(app, debug=True, port=5000)
