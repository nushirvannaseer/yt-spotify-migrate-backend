# ytmusic.py
import json
from flask import Blueprint, request, session, jsonify
import ytmusicapi
import spotipy

from utils.helpers import generate_random_name

# Create a Blueprint for YouTube Music-related routes
ytmusic_bp = Blueprint('ytmusic', __name__)

# Route to get user's YouTube Music playlists
@ytmusic_bp.route('/playlists')
def get_yt_playlists():
    if "google_token_info" not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
        playlists = ytmusic.get_library_playlists()
        return jsonify(playlists)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get songs from a YouTube Music playlist
@ytmusic_bp.route('/playlist-songs')
def get_yt_playlist_songs():
    if "google_token_info" not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        playlist_id = request.args.get('playlistId')
        ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
        playlist = ytmusic.get_playlist(playlist_id)
        
        songs = [{
            'id': song.get('videoId'),
            'title': song.get('title'), 
            'artist': song.get('artists')[0].get('name'), 
            'album': song.get('album').get('name') if song.get('album') else "", 
            'image': song.get('thumbnails')[0].get('url'),
            'url': f"https://music.youtube.com/watch?v={song.get('videoId')}"
        } for song in playlist.get('tracks')]
        
        return jsonify({"playlist_name": playlist.get('title'), "songs": songs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ytmusic_bp.route('/migrate-playlist')
def migrate_playlist():
    if "google_token_info" not in session:
        return jsonify({"error": "User not logged in"}), 401

    try:
        playlist_id = request.args.get('playlistId')
        ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
        yt_playlist = ytmusic.get_playlist(playlist_id)
        sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
        current_sp_user = sp.current_user()
        spotify_playlist = sp.user_playlist_create(current_sp_user.get('id'), name=yt_playlist.get('title'), description=yt_playlist.get('description'))
        songs = []
        for song in yt_playlist.get('tracks'):
            spotify_song = sp.search(q=f"{song.get('title')} {song.get('artists')[0].get('name')}", type='track', limit=10)
            if spotify_song:
                songs.append(spotify_song['tracks']['items'][0]['id'])
            if len(songs) == 5:
                sp.user_playlist_add_tracks(current_sp_user.get('id'), playlist_id=spotify_playlist.get('id'), tracks=songs)
                songs = []
        if songs:
            sp.user_playlist_add_tracks(current_sp_user.get('id'), playlist_id=spotify_playlist.get('id'), tracks=songs)
        return jsonify({"sp_playlist_id": spotify_playlist.get('id')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ytmusic_bp.route('/migrate-selected-songs', methods=['POST'])
def migrate_multiple_songs():
    try:
        body = request.get_json()
        songs = body.get('songs')
        sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
        current_sp_user = sp.current_user()
        sp_playlist_name = body.get('sp_playlist_name') if body.get('sp_playlist_name') else None
        if not sp_playlist_name:
            sp_playlist_name = generate_random_name()
        sp_playlist_id = sp.user_playlist_create(current_sp_user.get('id'), name=sp_playlist_name, description="These songs were migrated to Spotify using Movesic").get('id')
        songs_added = []
        for song in songs:
            spotify_song = sp.search(q=f"{song.get('name')} {song.get('artist')}", type='track', limit=10)
            if spotify_song:
                songs_added.append(spotify_song['tracks']['items'][0]['id'])
            if len(songs_added) == 50:
                sp.user_playlist_add_tracks(current_sp_user.get('id'), playlist_id=sp_playlist_id, tracks=songs_added)
                songs_added = []
        if songs_added:
            sp.user_playlist_add_tracks(current_sp_user.get('id'), playlist_id=sp_playlist_id, tracks=songs_added)
        return jsonify({"sp_playlist_id": sp_playlist_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
