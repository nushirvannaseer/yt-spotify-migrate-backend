# spotify.py
import os
import json
from flask import Blueprint, redirect, request, session, jsonify
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
from spotipy.cache_handler import CacheHandler
from utils.helpers import create_ytmusic_playlist, add_songs_to_ytmusic_playlist, generate_random_name, get_spotify_playlist_songs_helper

# Load environment variables
load_dotenv()

# Create a Blueprint for Spotify-related routes
spotify_bp = Blueprint('spotify', __name__)

# Spotify OAuth setup
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

class NoOpCacheHandler(CacheHandler):
    def get_cached_token(self):
        return None  # Always return None to indicate no cached token

    def save_token_to_cache(self, token_info):
        pass  # Do nothing, effectively disabling caching


sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-library-read playlist-modify-private playlist-modify-public playlist-read-collaborative",
    cache_path=None,
    cache_handler=NoOpCacheHandler(),
    show_dialog=True
)

# Route to initiate Spotify login
@spotify_bp.route('/login')
def spotify_login():
    try:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Callback route to handle Spotify's response
@spotify_bp.route('/callback')
def spotify_callback():
    try:
        token_info = sp_oauth.get_access_token(request.args["code"])
        session["spotify_token_info"] = token_info
        sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
        sp_user = sp.current_user()

        session["current_user"] = {
            "name": sp_user.get('display_name'),
            "id": sp_user.get('id'),
            "image": (sp_user.get('images')[1 if len(sp_user.get('images')) > 1 else 0].get('url')) if sp_user.get('images') else None
        }
        
        return redirect(os.getenv("FRONTEND_URL"))  # Redirect to frontend after login
    except Exception as e:
        del session['spotify_token_info']
        return jsonify({"error": str(e)}), 500

@spotify_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    try:
        refresh_token = request.json.get('refresh_token')
        
        # Request a new access token using the refresh token
        token_info = sp_oauth.refresh_access_token(refresh_token)
        
        # Update the session with the new access token
        session["spotify_token_info"] = token_info
        
        return jsonify({
            "access_token": token_info['access_token'],
            "expires_in": token_info['expires_in'],
            "expires_at": token_info['expires_at']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get Spotify playlists
@spotify_bp.route('/playlists')
def get_spotify_playlists():
    try:
        token_info = session.get("spotify_token_info", None)
        if not token_info:
            return redirect("/spotify-login")

        sp = spotipy.Spotify(auth=token_info["access_token"])
        playlists = sp.current_user_playlists()
        return jsonify(playlists)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get songs from a Spotify playlist
@spotify_bp.route('/playlist-songs')
def get_spotify_playlist_songs():
    try:
        playlist_id = request.args.get('playlistId')
        sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
        playlist_name = sp.playlist(playlist_id).get('name')
        songs = get_spotify_playlist_songs_helper(sp, playlist_id)
        trimmed_songs = []
        for song in songs:
            trimmed_songs.append({
                "id": song.get('track').get('id'),
                "name": song.get('track').get('name'),
                "artist": song.get('track').get('artists')[0].get('name'),
                "album": song.get('track').get('album').get('name'),
                "image": song.get('track').get('album').get('images')[0].get('url'),
                "url": song.get('track').get('external_urls').get('spotify')
            })
        return jsonify({"playlist_name": playlist_name, "songs": trimmed_songs})
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

# Route to migrate Spotify playlist to YouTube Music
@spotify_bp.route('/migrate-spotify-playlist')
def migrate_spotify_playlist():
    try:
        playlist_id = request.args.get('playlistId')
        sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
        playlist = sp.playlist(playlist_id)
        songs = get_spotify_playlist_songs_helper(sp, playlist_id)

        ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))

        try:
            yt_playlist_id = create_ytmusic_playlist(ytmusic, playlist.get('name'), playlist.get('description'))
            add_songs_to_ytmusic_playlist(ytmusic, yt_playlist_id, songs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return jsonify({"yt_playlist_id": yt_playlist_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@spotify_bp.route('/migrate-songs', methods=['POST'])
def migrate_multiple_songs():
    try:
        body = request.get_json()
        songs = body.get('songs')
        yt_playlist_name = body.get('yt_playlist_name') if body.get('yt_playlist_name') else None
        ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))
        yt_playlist_id = create_ytmusic_playlist(ytmusic, yt_playlist_name if yt_playlist_name else generate_random_name(), "These songs were migrated to Spotify using Movezic")

        count = 0
        added_songs = []
        for song in songs:
            ytmusic_song_id = ytmusic.search(song.get('name') + " " + song.get('artist'))[0]['videoId']
            if ytmusic_song_id:
                added_songs.append(ytmusic_song_id)
                count += 1
                if count == 20:
                    ytmusic.add_playlist_items(yt_playlist_id, added_songs)
                    added_songs = []
                    count = 0
        if added_songs:
            ytmusic.add_playlist_items(yt_playlist_id, added_songs)
        return jsonify({"yt_playlist_id": yt_playlist_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
