"""
Goal: Go through an entire playlist on Spotify, check their audio-features for instrumentalness,
and put those with low instrumentalness in a new playlist named "electronic vocals",
and those with high instrumentalness in a new playlist named "electronic instrumental".

I imagine the spotify API rate limiting will slow me down. To avoid re-fetching tracks,
store the audio-features of each track in a local database.

spotipy library to interact with the Spotify API.

sqlalchemy library to interact with the local database.

"""
import logging
import spotipy
import time
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy import create_engine, Column, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Spotify API Credentials
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-playback-state playlist-modify-public playlist-modify-private"

# Initialize Spotify API client
logger.info("Initializing Spotify API client")
auth_manager = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE,
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Initialize SQLAlchemy
logger.info("Initializing SQLAlchemy")
engine = create_engine("sqlite:///audio_features.db")
Base = declarative_base()


class AudioFeature(Base):
    """
    Represents the audio features of a track, specifically the instrumentalness attribute.
    This class is used to store and retrieve audio features from the local database.
    """

    __tablename__ = "audio_features"
    id: str = Column(String, primary_key=True)
    instrumentalness: float = Column(Float)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def get_playlist_tracks(playlist_id: str) -> List[dict]:
    """
    Get all the tracks from a playlist
    """
    logger.info(f"Fetching tracks from playlist {playlist_id}")
    results = sp.playlist_tracks(playlist_id)
    tracks = results["items"]
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])
    logger.info(f"Fetched {len(tracks)} tracks from playlist {playlist_id}")
    return tracks


def store_audio_features(track_id: str, instrumentalness: float) -> None:
    """
    Store audio features in the database
    """
    logger.info(f"Storing audio features for track {track_id}")
    audio_feature = session.query(AudioFeature).filter_by(id=track_id).first()
    if audio_feature is None:
        audio_feature = AudioFeature(id=track_id, instrumentalness=instrumentalness)
        session.add(audio_feature)
    else:
        audio_feature.instrumentalness = instrumentalness
    session.commit()
    logger.info(f"Stored audio features for track {track_id}")


def get_audio_features(track_id: str) -> Optional[AudioFeature]:
    """
    Retrieve audio features from the database
    """
    logger.info(f"Retrieving audio features for track from db {track_id}")
    return session.query(AudioFeature).filter_by(id=track_id).first()


def classify_tracks(tracks: List[dict]) -> Tuple[List[str], List[str]]:
    """
    Classify tracks into playlists based on instrumentalness
    """
    logger.info("Classifying tracks based on instrumentalness")
    electronic_vocals = []
    electronic_instrumental = []
    index = 1
    for track in tracks:
        track_id = track["track"]["id"]
        retry_attempts = 0
        audio_features_db = get_audio_features(track_id)
        if audio_features_db is None:
            while True:
                try:
                    logger.info(
                        f"Retrieving audio features for track from API {track_id}"
                    )
                    audio_features_api = sp.audio_features(track_id)[0]
                    break
                except spotipy.exceptions.SpotifyException as e:
                    if e.http_status == 429:
                        retry_attempts += 1
                        retry_after = min(
                            2**retry_attempts,
                            120,
                        )  # Exponential backoff with a cap
                        logger.warning(
                            f"Error occurred. Retrying after {retry_after} seconds. Attempt {retry_attempts}"
                        )
                        time.sleep(retry_after)
        if audio_features_db is None:
            instrumentalness = audio_features_api["instrumentalness"]
            store_audio_features(track_id, instrumentalness)
        else:
            instrumentalness = audio_features_db.instrumentalness

        logger.info(
            f"index: {index} Instrumentalness for track {track_id}: {instrumentalness}:"
        )
        index += 1

        if instrumentalness < 0.25:
            electronic_vocals.append(track_id)
        elif instrumentalness > 0.75:
            electronic_instrumental.append(track_id)

    logger.info(f"Classified {len(electronic_vocals)} tracks as electronic vocals")
    logger.info(
        f"Classified {len(electronic_instrumental)} tracks as electronic instrumental"
    )
    return electronic_vocals, electronic_instrumental


def main() -> None:
    """
    Main function to process a Spotify playlist, classify tracks based on instrumentalness,
    and create new playlists for electronic vocals and electronic instrumental tracks.
    """
    # Get playlist
    playlist_id = ""
    logger.info(f"Processing playlist {playlist_id}")
    tracks = get_playlist_tracks(playlist_id)

    # Classify tracks
    electronic_vocals, electronic_instrumental = classify_tracks(tracks)

    # Get user ID
    user_id = sp.me()["id"]

    # Create playlists
    logger.info("Creating new playlists")
    electronic_vocals_playlist = sp.user_playlist_create(
        user_id, f"Electronic Vocals {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    electronic_instrumental_playlist = sp.user_playlist_create(
        user_id,
        f"Electronic Instrumental {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    )

    # Add tracks to playlists
    logger.info("Adding tracks to new playlists")
    if electronic_vocals:
        for i in range(0, len(electronic_vocals), 100):
            sp.playlist_add_items(
                electronic_vocals_playlist["id"], electronic_vocals[i : i + 100]
            )
            time.sleep(1)
        logger.info("Tracks added to electronic vocals playlist successfully")
    else:
        logger.info("No tracks to add to electronic vocals playlist")
    if electronic_instrumental:
        for i in range(0, len(electronic_instrumental), 100):
            sp.playlist_add_items(
                electronic_instrumental_playlist["id"],
                electronic_instrumental[i : i + 100],
            )
            time.sleep(1)
        logger.info("Tracks added to electronic instrumental playlist successfully")
    else:
        logger.info("No tracks to add to electronic instrumental playlist")


if __name__ == "__main__":
    main()
