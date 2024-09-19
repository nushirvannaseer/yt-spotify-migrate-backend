# ytmusic.py
import json
from flask import Blueprint, request, session, jsonify
import ytmusicapi

# Create a Blueprint for YouTube Music-related routes
ytmusic_bp = Blueprint('ytmusic', __name__)

# Route to get user's YouTube Music playlists
@ytmusic_bp.route('/playlists')
def get_yt_playlists():
    if "google_token_info" not in session:
        return jsonify({"error": "User not logged in"}), 401

    ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
    playlists = ytmusic.get_library_playlists()
    return jsonify(playlists)

# Route to get songs from a YouTube Music playlist
@ytmusic_bp.route('/playlist-songs')
def get_yt_playlist_songs():
    if "google_token_info" not in session:
        return jsonify({"error": "User not logged in"}), 401

    playlist_id = request.args.get('playlistId')
    ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
    playlist = ytmusic.get_playlist(playlist_id)
    
    songs = [{
        'id': song.get('videoId'),
        'title': song.get('title'), 
        'artist': song.get('artists')[0].get('name'), 
        'album': song.get('album').get('name') if song.get('album') else "", 
        'image': song.get('thumbnails')[0].get('url')
    } for song in playlist.get('tracks')]
    
    return jsonify({"playlist_name": playlist.get('title'), "songs": songs})
