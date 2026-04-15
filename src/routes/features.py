"""
Feature notification and version management routes.
"""
import os
import json
from flask import jsonify, current_app, request
from src import app

def load_feature_releases():
    """
    Load feature releases from features.json.
    Supports the new `releases` array format and the legacy timestamp-keyed object format.
    """
    try:
        features_file = os.path.join(current_app.root_path, '..', 'features.json')
        if not os.path.exists(features_file):
            return []

        with open(features_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        releases = []
        if isinstance(raw_data, dict) and isinstance(raw_data.get('releases'), list):
            for release in raw_data['releases']:
                releases.append({
                    'id': str(release.get('id')),
                    'released_at': int(release.get('released_at')) if release.get('released_at') is not None else None,
                    'version_name': release.get('version_name'),
                    'features': release.get('features', []),
                })
        elif isinstance(raw_data, dict):
            for release_id, release_data in raw_data.items():
                try:
                    released_at = int(release_id)
                except (TypeError, ValueError):
                    released_at = None
                releases.append({
                    'id': str(release_id),
                    'released_at': released_at,
                    'version_name': release_data.get('version_name'),
                    'features': release_data.get('features', []),
                })

        releases.sort(key=lambda release: release.get('released_at') or 0)
        return releases
    except Exception as e:
        current_app.logger.error(f"Error loading feature releases: {e}")
        return []


def get_latest_feature_version():
    releases = load_feature_releases()
    if not releases:
        return None
    return releases[-1].get('id')


def get_features_since_version(since_version=None):
    releases = load_feature_releases()
    if since_version is None:
        return releases

    matching_release = next((release for release in releases if release.get('id') == since_version), None)
    if matching_release is not None:
        since_timestamp = matching_release.get('released_at')
    else:
        try:
            since_timestamp = int(since_version)
        except (TypeError, ValueError):
            since_timestamp = None

    if since_timestamp is not None:
        return [
            release for release in releases
            if release.get('released_at') is not None and release.get('released_at') > since_timestamp
        ]

    return [
        release for release in releases
        if release.get('id') != since_version
    ]


@app.route('/api/version')
def version_info():
    """
    Return current feature version and optionally features since a version.
    Query parameter 'since' can be used to get new feature releases.
    """
    current_version = get_latest_feature_version()
    since_version = request.args.get('since')
    
    response = {
        'version': current_version,
        'feature_version': current_version,
    }

    if current_version is not None:
        latest_release = next(
            (release for release in load_feature_releases() if release.get('id') == current_version),
            None
        )
        if latest_release is not None and latest_release.get('released_at') is not None:
            response['released_at'] = latest_release.get('released_at')

    new_features = get_features_since_version(since_version) if since_version else get_features_since_version()
    response['new_features'] = new_features
    response['has_new_features'] = len(new_features) > 0

    return jsonify(response)

@app.route('/api/features')
def all_features():
    """
    Return all available features grouped by version.
    """
    releases = get_features_since_version()
    current_version = get_latest_feature_version()
    return jsonify({
        'features': releases,
        'current_version': current_version,
        'feature_version': current_version
    })