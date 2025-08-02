import spotipy
import sys
import time
import re
import logging
from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Spotify API Credentials
SPOTIPY_CLIENT_ID = ""
SPOTIPY_CLIENT_SECRET = ""
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "playlist-read-private playlist-read-collaborative"

# Initialize Spotify API client
logger.info("Initializing Spotify API client")
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
    )
)

# Initialize SQLAlchemy
logger.info("Initializing SQLAlchemy")
engine = create_engine("sqlite:///artist_data.db")
Base = declarative_base()

# Static set of artist IDs to exclude from analysis
EXCLUDED_ARTIST_IDS = {
    "09w3ZVwt5NBtwS2wZgBfwQ",
    "4jRHHjjzgLIshyPc58TNsW",
    "1AA2rqygbiWb7fpU4FoLne",
    "3NZDZSNhQZtU8NnfBeZI3t",
}


class ArtistData(Base):
    """
    Represents artist data including popularity and follower count.
    This class is used to store and retrieve artist data from the local database.
    """

    __tablename__ = "artist_data"

    id: str = Column(String, primary_key=True)
    name: str = Column(String)
    popularity: int = Column(Integer)
    followers: int = Column(Integer)
    last_updated: datetime = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def find_playlist_by_name(playlist_name):
    """Find a playlist by name and return its ID"""
    playlists = sp.current_user_playlists()

    for playlist in playlists["items"]:
        if playlist["name"].lower() == playlist_name.lower():
            return playlist["id"]

    return None


def is_playlist_id(s):
    """Check if string looks like a Spotify playlist ID"""
    return bool(re.fullmatch(r"[A-Za-z0-9]{22}", s))


def get_playlist_id(playlist_arg):
    """Get playlist ID from name or use ID directly"""
    if is_playlist_id(playlist_arg):
        return playlist_arg
    else:
        return find_playlist_by_name(playlist_arg)


def store_artist_data(
    artist_id: str, name: str, popularity: int, followers: int
) -> None:
    """Store artist data in the database"""
    logger.info(f"Storing artist data for {name} (ID: {artist_id})")
    artist_data = session.query(ArtistData).filter_by(id=artist_id).first()
    if artist_data is None:
        artist_data = ArtistData(
            id=artist_id,
            name=name,
            popularity=popularity,
            followers=followers,
            last_updated=datetime.utcnow(),
        )
        session.add(artist_data)
    else:
        artist_data.name = name
        artist_data.popularity = popularity
        artist_data.followers = followers
        artist_data.last_updated = datetime.utcnow()
    session.commit()
    # logger.info(f"Stored artist data for {name}")


def get_artist_data(artist_id: str) -> Optional[ArtistData]:
    """Retrieve artist data from the database"""
    # logger.info(f"Retrieving artist data from db for ID: {artist_id}")
    return session.query(ArtistData).filter_by(id=artist_id).first()


def search_artist_by_name(artist_name):
    """Search for artist by name and return follower count"""
    try:
        results = sp.search(q=artist_name, type="artist", limit=1)
        if results["artists"]["items"]:
            artist = results["artists"]["items"][0]
            return {
                "popularity": artist.get("popularity", 0),
                "followers": artist.get("followers", {}).get("total", 0),
                "name": artist.get("name", "Unknown"),
                "id": artist.get("id", "Unknown"),
            }
    except Exception as e:
        logger.error(f"Error searching for artist '{artist_name}': {e}")
    return {"popularity": 0, "followers": 0, "name": artist_name, "id": "Unknown"}


def get_artists_batch(artist_ids, batch_size=50):
    """Get artist data in batches with caching"""
    artists_data = {}
    total_batches = (len(artist_ids) + batch_size - 1) // batch_size

    logger.info(f"Fetching artist data in {total_batches} batches...")

    for i in range(0, len(artist_ids), batch_size):
        batch = artist_ids[i : i + batch_size]
        batch_num = (i // batch_size) + 1

        logger.info(
            f"  Batch {batch_num}/{total_batches}: Processing {len(batch)} artists..."
        )

        # Check cache first
        uncached_ids = []
        for artist_id in batch:
            cached_data = get_artist_data(artist_id)
            if cached_data:
                artists_data[artist_id] = {
                    "popularity": cached_data.popularity,
                    "followers": cached_data.followers,
                    "name": cached_data.name,
                }
                logger.info(
                    f"    Cached: {cached_data.name} - {cached_data.followers} followers"
                )
            else:
                uncached_ids.append(artist_id)

        # Fetch uncached artists from API
        if uncached_ids:
            try:
                artists = sp.artists(uncached_ids)

                returned_count = len(artists["artists"])
                logger.info(f"    Received {returned_count} artists from API")

                if returned_count != len(uncached_ids):
                    logger.warning(
                        f"    WARNING: Expected {len(uncached_ids)} artists, got {returned_count}"
                    )

                for artist in artists["artists"]:
                    if artist:  # Check if artist data is not None
                        artist_id = artist["id"]
                        name = artist.get("name", "Unknown")
                        popularity = artist.get("popularity", 0)
                        followers = artist.get("followers", {}).get("total", 0)

                        # Store in cache
                        store_artist_data(artist_id, name, popularity, followers)

                        # Add to results
                        artists_data[artist_id] = {
                            "popularity": popularity,
                            "followers": followers,
                            "name": name,
                        }

                        logger.info(f"    API: {name} - {followers} followers")
                    else:
                        logger.warning(
                            f"    WARNING: Received None artist data for ID in batch"
                        )

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(
                    f"    ERROR: Could not fetch data for batch {batch_num}: {e}"
                )
                # Add default values for failed requests
                for artist_id in uncached_ids:
                    if artist_id not in artists_data:
                        artists_data[artist_id] = {
                            "popularity": 0,
                            "followers": 0,
                            "name": "Unknown",
                        }

    logger.info(f"Total artists processed: {len(artists_data)}")
    return artists_data


def parse_release_date(release_date_str):
    """Parse release date string and return datetime object"""
    if not release_date_str:
        return None

    try:
        # Handle different date formats: "YYYY-MM-DD", "YYYY-MM", "YYYY"
        if len(release_date_str) == 4:  # YYYY
            return datetime.strptime(release_date_str, "%Y")
        elif len(release_date_str) == 7:  # YYYY-MM
            return datetime.strptime(release_date_str, "%Y-%m")
        elif len(release_date_str) == 10:  # YYYY-MM-DD
            return datetime.strptime(release_date_str, "%Y-%m-%d")
        else:
            return None
    except ValueError:
        return None


def get_playlist_tracks_with_metrics(playlist_id):
    """Get all tracks from a playlist with popularity and artist metrics"""
    tracks_with_metrics = []

    logger.info("Fetching playlist tracks...")

    # Get playlist tracks
    results = sp.playlist_tracks(playlist_id)
    tracks = results["items"]

    # Handle pagination if playlist has more than 100 tracks
    while results["next"]:
        results = sp.next(results)
        tracks.extend(results["items"])

    logger.info(f"Found {len(tracks)} total track items")

    # Collect all unique artist IDs and track data
    artist_ids = set()
    track_data = []

    for item in tracks:
        track = item["track"]
        if track:  # Skip None tracks (can happen with deleted songs)
            artist_id = track["artists"][0]["id"]
            artist_name = track["artists"][0]["name"]

            # Skip tracks from excluded artists
            if artist_id in EXCLUDED_ARTIST_IDS:
                logger.info(
                    f"Skipping excluded artist: {artist_name} (ID: {artist_id})"
                )
                continue

            artist_ids.add(artist_id)
            track_data.append(
                {"track": track, "artist_id": artist_id, "artist_name": artist_name}
            )

    logger.info(f"Found {len(artist_ids)} unique artists")

    # Get artist data in batches (with caching)
    artists_data = get_artists_batch(list(artist_ids))

    # Build artist name to best data mapping (consolidate duplicate artists)
    artist_name_to_best_data = {}
    for artist_id, data in artists_data.items():
        name = data.get("name", "Unknown")
        followers = data.get("followers", 0)
        popularity = data.get("popularity", 0)

        # If we haven't seen this artist name, or this entry has better data
        if name not in artist_name_to_best_data:
            artist_name_to_best_data[name] = {
                "followers": followers,
                "popularity": popularity,
                "artist_id": artist_id,
            }
        else:
            # Keep the entry with the highest follower count (or popularity as tiebreaker)
            current = artist_name_to_best_data[name]
            if followers > current["followers"] or (
                followers == current["followers"] and popularity > current["popularity"]
            ):
                artist_name_to_best_data[name] = {
                    "followers": followers,
                    "popularity": popularity,
                    "artist_id": artist_id,
                }

    logger.info(
        f"Consolidated {len(artist_name_to_best_data)} unique artists from {len(artists_data)} artist IDs"
    )
    logger.info(f"Artist name to best data mapping (sample):")
    for name, data in list(artist_name_to_best_data.items())[:10]:
        logger.info(
            f"  {name}: {data['followers']} followers, {data['popularity']} popularity"
        )

    # Build final track list with metrics
    processed_count = 0
    skipped_count = 0

    for item in track_data:
        track = item["track"]
        artist_id = item["artist_id"]
        artist_name = item["artist_name"]

        # Skip tracks without a Spotify URL or malformed data
        try:
            spotify_url = track["external_urls"]["spotify"]
        except (KeyError, TypeError):
            skipped_count += 1
            continue

        # Get the best data for this artist name (consolidated across all IDs)
        best_data = artist_name_to_best_data.get(
            artist_name, {"followers": 0, "popularity": 0, "artist_id": artist_id}
        )
        followers = best_data["followers"]
        artist_popularity = best_data["popularity"]

        # If followers is still 0, try searching by name as fallback
        if followers == 0:
            logger.info(f"Searching for artist by name: {artist_name}")
            search_result = search_artist_by_name(artist_name)
            if search_result["followers"] > 0:
                followers = search_result["followers"]
                artist_popularity = search_result.get("popularity", 0)
                logger.info(f"Found {artist_name} via search: {followers} followers")

        # Parse release date
        album_release_date = None
        if track.get("album") and track["album"].get("release_date"):
            album_release_date = parse_release_date(track["album"]["release_date"])

        track_info = {
            "name": track.get("name", "Unknown"),
            "artist": artist_name,
            "artist_id": best_data["artist_id"],  # Use the best artist ID
            "track_popularity": track.get("popularity", 0),
            "artist_popularity": artist_popularity,
            "artist_followers": followers,
            "spotify_url": spotify_url,
            "album": track["album"]["name"]
            if track.get("album") and "name" in track["album"]
            else "Unknown",
            "release_date": album_release_date,
            "release_date_str": track["album"].get("release_date", "Unknown")
            if track.get("album")
            else "Unknown",
        }
        tracks_with_metrics.append(track_info)
        processed_count += 1

    logger.info(f"Processed {processed_count} tracks, skipped {skipped_count} tracks")
    return tracks_with_metrics


def get_sorted_songs(tracks, sort_by="track_popularity", count=20, order="least"):
    """Get songs sorted by specified metric"""
    if sort_by == "track_popularity":
        key = "track_popularity"
        metric_name = "Track Popularity"
    elif sort_by == "artist_popularity":
        key = "artist_popularity"
        metric_name = "Artist Popularity"
    elif sort_by == "artist_followers":
        key = "artist_followers"
        metric_name = "Artist Followers"
    elif sort_by == "release_date":
        key = "release_date"
        metric_name = "Release Date"
    else:
        raise ValueError(f"Invalid sort_by option: {sort_by}")

    # Filter out tracks without release dates for release_date sorting
    if sort_by == "release_date":
        tracks_with_dates = [t for t in tracks if t.get("release_date") is not None]
        tracks_without_dates = [t for t in tracks if t.get("release_date") is None]

        if tracks_without_dates:
            logger.info(
                f"Found {len(tracks_without_dates)} tracks without release dates"
            )

        if not tracks_with_dates:
            logger.warning("No tracks with valid release dates found!")
            return [], metric_name, False

        tracks = tracks_with_dates

    reverse = order == "most"
    sorted_tracks = sorted(tracks, key=lambda x: x[key], reverse=reverse)

    return sorted_tracks[:count], metric_name, reverse


def format_number(num):
    """Format large numbers with K, M, B suffixes"""
    if num >= 1000000000:
        return f"{num / 1000000000:.1f}B"
    elif num >= 1000000:
        return f"{num / 1000000:.1f}M"
    elif num >= 1000:
        return f"{num / 1000:.1f}K"
    else:
        return str(num)


def format_date(date_obj):
    """Format date object for display"""
    if not date_obj:
        return "Unknown"

    if date_obj.year and not date_obj.month:
        return str(date_obj.year)
    elif date_obj.year and date_obj.month and not date_obj.day:
        return date_obj.strftime("%B %Y")
    else:
        return date_obj.strftime("%B %d, %Y")


def list_available_playlists():
    """List all available playlists"""
    playlists = sp.current_user_playlists()
    print("Available playlists:")
    for i, playlist in enumerate(playlists["items"], 1):
        print(f"  {i:2d}. {playlist['name']}")
    return playlists["items"]


def print_usage():
    """Print usage instructions"""
    print("Usage:")
    print(
        "  python spotify_least_popular.py [playlist_name_or_id] [sort_by] [count] [order]"
    )
    print("\nArguments:")
    print(
        "  playlist_name_or_id - Name or Spotify ID of the playlist (default: 'chill')"
    )
    print("  sort_by             - Sorting method (default: 'track_popularity')")
    print(
        "                        Options: 'track_popularity', 'artist_popularity', 'artist_followers', 'release_date'"
    )
    print("  count               - Number of songs to return (default: 20)")
    print("  order               - 'most' or 'least' (default: 'least')")
    print("                        For release_date: 'most' = newest, 'least' = oldest")
    print("\nExamples:")
    print("  python spotify_least_popular.py")
    print("  python spotify_least_popular.py rock artist_popularity 10 most")
    print(
        "  python spotify_least_popular.py 5Q2NTHzXiXJaDAouEsoJs4 artist_followers 30 least"
    )
    print(
        "  python spotify_least_popular.py rock release_date 15 least  # oldest tracks"
    )


def main():
    # Parse command line arguments
    playlist_arg = "chill"
    sort_by = "track_popularity"
    count = 20
    order = "least"

    if len(sys.argv) > 1:
        playlist_arg = sys.argv[1]
    if len(sys.argv) > 2:
        sort_by = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            count = int(sys.argv[3])
        except ValueError:
            print("Error: count must be a number")
            print_usage()
            return
    if len(sys.argv) > 4:
        order = sys.argv[4].lower()
        if order not in ["most", "least"]:
            print("Error: order must be 'most' or 'least'")
            print_usage()
            return

    # Validate sort_by option
    valid_sort_options = [
        "track_popularity",
        "artist_popularity",
        "artist_followers",
        "release_date",
    ]
    if sort_by not in valid_sort_options:
        print(f"Error: Invalid sort_by option '{sort_by}'")
        print(f"Valid options: {', '.join(valid_sort_options)}")
        print_usage()
        return

    print(f"Searching for playlist: '{playlist_arg}'")
    print(f"Sorting by: {sort_by}")
    print(f"Returning top {count} songs")
    print(f"Order: {order}")

    # Find the playlist
    playlist_id = get_playlist_id(playlist_arg)

    if not playlist_id:
        print(f"Playlist '{playlist_arg}' not found!")
        print()
        print_usage()
        print()
        list_available_playlists()
        return

    print(f"Found playlist: '{playlist_arg}' (ID: {playlist_id})")

    # Get all tracks with metrics
    print("Fetching tracks and metrics data...")
    tracks = get_playlist_tracks_with_metrics(playlist_id)

    if not tracks:
        print("No tracks found in the playlist!")
        return

    print(f"Found {len(tracks)} tracks in the playlist")

    # Get sorted songs
    sorted_songs, metric_name, reverse = get_sorted_songs(tracks, sort_by, count, order)

    if not sorted_songs:
        print("No tracks found matching the criteria!")
        return

    # Display results
    sort_direction = "highest" if reverse else "lowest"
    if sort_by == "release_date":
        sort_direction = "newest" if reverse else "oldest"

    print(
        f"\nTop {count} songs with {sort_direction} {metric_name} from '{playlist_arg}':"
    )
    print("=" * 100)

    for i, track in enumerate(sorted_songs, 1):
        print(f"{i:2d}. {track['name']} - {track['artist']}")
        print(f"     Album: {track['album']}")
        if sort_by == "release_date":
            print(
                f"     Release Date: {format_date(track['release_date'])} ({track['release_date_str']})"
            )
        print(f"     Track Popularity: {track['track_popularity']}/100")
        print(f"     Artist Popularity: {track['artist_popularity']}/100")
        print(f"     Artist Followers: {format_number(track['artist_followers'])}")
        print(f"     Spotify URL: {track['spotify_url']}")
        print("-" * 100)

    # Summary statistics
    if sort_by == "track_popularity":
        values = [track["track_popularity"] for track in sorted_songs]
    elif sort_by == "artist_popularity":
        values = [track["artist_popularity"] for track in sorted_songs]
    elif sort_by == "artist_followers":
        values = [track["artist_followers"] for track in sorted_songs]
    elif sort_by == "release_date":
        values = [
            track["release_date"] for track in sorted_songs if track["release_date"]
        ]

    if values:
        if sort_by == "release_date":
            # For dates, show oldest and newest
            oldest = min(values)
            newest = max(values)
            print(f"\nSummary for {metric_name}:")
            print(f"Oldest: {format_date(oldest)}")
            print(f"Newest: {format_date(newest)}")
        elif sort_by == "artist_followers":
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            print(f"\nSummary for {metric_name}:")
            print(f"Average: {format_number(avg_value)}")
            print(f"Lowest: {format_number(min_value)}")
            print(f"Highest: {format_number(max_value)}")
        else:
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            print(f"\nSummary for {metric_name}:")
            print(f"Average: {avg_value:.1f}/100")
            print(f"Lowest: {min_value}/100")
            print(f"Highest: {max_value}/100")


if __name__ == "__main__":
    main()
