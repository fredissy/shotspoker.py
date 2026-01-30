from src import app, redis_client
from flask import jsonify

@app.route('/health')
def health_check():

    status = {
        "status": "ok",
        "store": "ok",
        "store-type": "redis" if app.config['USE_REDIS'] else "in-memory"
    }
    http_code = 200

    if app.config['USE_REDIS']:
        # 1. Check Redis (Critical for SocketIO)
        try:
            redis_client.ping()
        except Exception as e:
            status['store'] = 'down'
            status['store_error'] = str(e)
            status['status'] = 'error'
            http_code = 503

    return jsonify(status), http_code
