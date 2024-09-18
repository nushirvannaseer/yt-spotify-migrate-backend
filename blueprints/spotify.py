# spotify.py
import os
import json
from flask import Blueprint, redirect, request, session, jsonify
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
from utils.helpers import create_ytmusic_playlist, add_songs_to_ytmusic_playlist

# Load environment variables
load_dotenv()

# Create a Blueprint for Spotify-related routes
spotify_bp = Blueprint('spotify', __name__)

# Spotify OAuth setup
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-library-read playlist-modify-private playlist-modify-public playlist-read-collaborative"
)

# Route to initiate Spotify login
@spotify_bp.route('/login')
def spotify_login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

# Callback route to handle Spotify's response
@spotify_bp.route('/callback')
def spotify_callback():
    token_info = sp_oauth.get_access_token(request.args["code"])
    session["spotify_token_info"] = token_info
    return redirect(os.getenv("FRONTEND_URL"))  # Redirect to frontend after login

# Route to get Spotify playlists
@spotify_bp.route('/playlists')
def get_spotify_playlists():
    token_info = session.get("spotify_token_info", None)
    if not token_info:
        return redirect("/spotify-login")

    sp = spotipy.Spotify(auth=token_info["access_token"])
    playlists = sp.current_user_playlists()
    return jsonify(playlists)

# Route to get songs from a Spotify playlist
@spotify_bp.route('/playlist-songs')
def get_spotify_playlist_songs():
    playlist_id = request.args.get('playlistId')
    songs = get_spotify_playlist_songs_helper(playlist_id)
    return jsonify(songs)

# Helper function to get songs from a playlist
def get_spotify_playlist_songs_helper(playlist_id):
    sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
    data = sp.playlist_items(playlist_id, offset=0)
    next = data.get('next')
    songs = data['items']
    while next:
        data = sp.next(data)
        next = data.get('next')
        songs += data['items']
    return songs

# Route to migrate Spotify playlist to YouTube Music
@spotify_bp.route('/migrate-spotify-playlist')
def migrate_spotify_playlist():
    playlist_id = request.args.get('playlistId')
    sp = spotipy.Spotify(auth=session["spotify_token_info"]["access_token"])
    playlist = sp.playlist(playlist_id)
    songs = get_spotify_playlist_songs_helper(playlist_id)

    ytmusic = ytmusicapi.YTMusic(json.dumps(session["google_token_info"]))

    try:
        yt_playlist_id = create_ytmusic_playlist(ytmusic, playlist.get('name'), playlist.get('description'))
        add_songs_to_ytmusic_playlist(ytmusic, yt_playlist_id, songs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return "Playlist migrated successfully!"
