import random
import re
from utils.constants import adjectives, nouns

# Helper function to create YouTube Music playlist
def create_ytmusic_playlist(ytmusic, name, description):
    try:
        name = re.sub(r'<|>', '', name)
        description = re.sub(r'<|>', '', description)
        return ytmusic.create_playlist(name, description)
    except Exception as e:
        return f"Error creating YouTube Music playlist: {e}"

# Helper function to add songs to YouTube Music playlist
def add_songs_to_ytmusic_playlist(ytmusic, yt_playlist_id, songs):
    try:
        yt_songs = []
        count = 0
        for song in songs:
            yt_song = ytmusic.search(song.get('track').get('name') + " " + song.get('track').get('artists')[0].get('name'))
            if yt_song and yt_song[0]['videoId']:
                yt_songs.append(yt_song[0]['videoId'])
                count += 1
                if count == 20:
                    ytmusic.add_playlist_items(yt_playlist_id, yt_songs)
                    yt_songs = []
                    count = 0
        if yt_songs:
            ytmusic.add_playlist_items(yt_playlist_id, yt_songs)
    except Exception as e:
        return f"Error adding songs to YouTube Music playlist: {e}"

# Helper function to get songs from a playlist
def get_spotify_playlist_songs_helper(sp, playlist_id):
    try:
        data = sp.playlist_items(playlist_id, offset=0)
        next = data.get('next')
        songs = data['items']
        while next:
            data = sp.next(data)
            next = data.get('next')
            songs += data['items']
        return songs
    except Exception as e:
        return f"Error getting Spotify playlist songs: {e}"
    
def get_spotify_playlists_helper(sp, limit=50):
    try:
        data = sp.current_user_playlists(limit=limit)
        next = data.get('next')
        playlists = data['items']
        while next:
            data = sp.next(data)
            next = data.get('next')
            playlists += data['items']
        return playlists
    except Exception as e:
        return f"Error getting Spotify playlists: {e}"

def generate_random_name():
    try:
        random_adjective = random.choice(adjectives)
        random_noun = random.choice(nouns)
        return f"{random_adjective}-{random_noun}"
    except Exception as e:
        return f"Error generating random name: {e}"