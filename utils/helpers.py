import re

# Helper function to create YouTube Music playlist
def create_ytmusic_playlist(ytmusic, name, description):
    name = re.sub(r'<|>', '', name)
    description = re.sub(r'<|>', '', description)
    return ytmusic.create_playlist(name, description)

# Helper function to add songs to YouTube Music playlist
def add_songs_to_ytmusic_playlist(ytmusic, yt_playlist_id, songs):
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
