import webbrowser

import spotipy
from googleapiclient.discovery import build
from spotipy.oauth2 import SpotifyOAuth

# Spotify API Credentials
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-playback-state"

# YouTube API Credentials
YOUTUBE_API_KEY = ""

# Initialize Spotify API client
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
    )
)

# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def get_current_spotify_song():
    # Check currently playing song on Spotify
    current_track = sp.current_playback()
    if current_track and current_track["is_playing"]:
        track_name = current_track["item"]["name"]
        artist_name = current_track["item"]["artists"][0]["name"]
        return track_name, artist_name
    return None, None


def find_music_video_on_youtube(track_name, artist_name):
    # Query YouTube for an official music video
    search_query = f"{artist_name} {track_name} official music video"
    request = youtube.search().list(
        q=search_query,
        part="snippet",
        type="video",
        videoCategoryId="10",  # Category ID for Music
        maxResults=1,
    )
    response = request.execute()
    if response["items"]:
        video_id = response["items"][0]["id"]["videoId"]
        return f"https://www.youtube.com/watch?v={video_id}"
    return None


# Main execution
track_name, artist_name = get_current_spotify_song()
if track_name and artist_name:
    print(f"Currently playing: {track_name} by {artist_name}")
    video_url = find_music_video_on_youtube(track_name, artist_name)
    if video_url:
        print(f"Opening video: {video_url}")
        webbrowser.open(video_url)
    else:
        print("No official music video found.")
else:
    print("No song currently playing.")
