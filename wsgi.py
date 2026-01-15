from src import app

if __name__ == "__main__":
    # This block is rarely executed in prod, but good for safety
    from src import socketio
    socketio.run(app)
