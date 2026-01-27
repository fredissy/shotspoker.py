from src import app, redis_client
from flask import jsonify

@app.route('/health')
def health_check():

    status = {
        "status": "ok",
        "redis": "ok"
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

    return jsonify(status), http_code
