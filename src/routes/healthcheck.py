from sqlalchemy import text  # <--- Make sure to add this import at the top
from src import app, db, redis_client
from flask import jsonify

@app.route('/health')
def health_check():

    status = {
        "status": "ok",
        "redis": "ok",
        "db": "ok"
    }
    http_code = 200

    # 1. Check Redis (Critical for SocketIO)
    try:
        redis_client.ping()
    except Exception as e:
        status['redis'] = 'down'
        status['redis_error'] = str(e)
        status['status'] = 'error'
        http_code = 503

    # 2. Check Database (Critical for History)
    try:
        # Run a simple "SELECT 1" to ensure connection is alive
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        status['db'] = 'down'
        status['db_error'] = str(e)
        status['status'] = 'error'
        http_code = 503

    return jsonify(status), http_code
