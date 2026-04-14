"""
Feature notification and version management routes.
"""
import os
import json
from flask import jsonify, current_app, request
from src import app

def get_app_version():
    """
    Get the current application version based on build timestamp.
    Uses the modification time of app.py as the version identifier.
    """
    try:
        app_py_path = os.path.join(current_app.root_path, '..', 'app.py')
        if os.path.exists(app_py_path):
            return str(int(os.path.getmtime(app_py_path)))
        else:
            # Fallback to current timestamp if app.py not found
            import time
            return str(int(time.time()))
    except Exception:
        # Ultimate fallback
        import time
        return str(int(time.time()))

def get_features_since_version(since_version=None):
    """
    Get all features added since a specific version timestamp.
    Returns features in chronological order (oldest first).
    """
    try:
        features_file = os.path.join(current_app.root_path, '..', 'features.json')
        
        if not os.path.exists(features_file):
            return []
            
        with open(features_file, 'r', encoding='utf-8') as f:
            all_features = json.load(f)
        
        if since_version is None:
            # Return all features if no version specified
            versions = sorted(all_features.keys(), key=int)
            return [all_features[v] for v in versions]
        
        # Filter features newer than the specified version
        since_timestamp = int(since_version)
        new_features = []
        
        for version_timestamp, feature_data in all_features.items():
            if int(version_timestamp) > since_timestamp:
                new_features.append({
                    'version': version_timestamp,
                    **feature_data
                })
        
        # Sort by version timestamp (oldest first)
        new_features.sort(key=lambda x: int(x['version']))
        return new_features
        
    except Exception as e:
        current_app.logger.error(f"Error loading features: {e}")
        return []

@app.route('/api/version')
def version_info():
    """
    Return current application version and optionally features since a version.
    Query parameter 'since' can be used to get new features.
    """
    current_version = get_app_version()
    since_version = request.args.get('since')
    
    response = {
        'version': current_version,
        'timestamp': int(current_version)
    }
    
    if since_version:
        new_features = get_features_since_version(since_version)
        response['new_features'] = new_features
        response['has_new_features'] = len(new_features) > 0
    
    return jsonify(response)

@app.route('/api/features')
def all_features():
    """
    Return all available features grouped by version.
    """
    features = get_features_since_version()
    return jsonify({
        'features': features,
        'current_version': get_app_version()
    })