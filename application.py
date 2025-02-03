import spotipy
from flask import Flask, request, url_for, session, redirect, render_template_string
from datetime import datetime
import random
import requests
import pandas as pd
import kagglehub
import re
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Set up Flask app with environment variables
app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = os.getenv('SECRET_KEY')

CLI_ID = os.getenv("CLIENT_ID")
CLI_SEC = os.getenv("CLIENT_SECRET")
API_BASE = 'https://accounts.spotify.com'
REDIRECT_URI = os.getenv("REDIRECT_URI")
SCOPE = 'user-library-read playlist-modify-public playlist-modify-private user-top-read user-read-private user-read-email'
SHOW_DIALOG = True

# Load the Spotify Million Song Dataset
path = kagglehub.dataset_download("notshrirang/spotify-million-song-dataset")
df = pd.read_csv(path + "/spotify_millsongdata.csv")

# Preprocess the dataset
df['text'] = df['text'].fillna('')
df['combined'] = df['artist'] + ' ' + df['song'] + ' ' + df['text']

@app.route('/')
def verify():
    auth_url = f'{API_BASE}/authorize?client_id={CLI_ID}&response_type=code&redirect_uri={REDIRECT_URI}&scope={SCOPE}&show_dialog={SHOW_DIALOG}'
    return redirect(auth_url)

@app.route('/api_callback')
def api_callback():
    session.clear()
    code = request.args.get('code')

    auth_token_url = f"{API_BASE}/api/token"
    res = requests.post(auth_token_url, data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLI_ID,
        "client_secret": CLI_SEC
    })

    res_body = res.json()
    session["toke"] = res_body.get("access_token")
    
    return redirect(url_for('choose_playlist'))

@app.route('/choose_playlist')
def choose_playlist():
    return render_template_string('''
        <h2>Enter the name of the playlist you want to base recommendations on:</h2>
        <form action="{{ url_for('create_recommended_playlist') }}" method="POST">
            <input type="text" name="playlist_name" required>
            <input type="submit" value="Create Recommended Playlist">
        </form>
    ''')

@app.route('/create_recommended_playlist', methods=['POST'])
def create_recommended_playlist():
    playlist_name = request.form.get('playlist_name').strip().lower()
   
    if 'toke' not in session:
        return redirect('/')

    sp = spotipy.Spotify(auth=session['toke'])
    user_id = sp.current_user()['id']

    # Find the input playlist
    user_playlists = sp.current_user_playlists()
    playlist_id = None
    while user_playlists:
        for playlist in user_playlists['items']:
            if playlist['name'].strip().lower() == playlist_name:
                playlist_id = playlist['id']
                break
        if playlist_id or not user_playlists['next']:
            break
        user_playlists = sp.next(user_playlists)

    if not playlist_id:
        return f"Playlist '{playlist_name}' not found."

    # Get tracks from the input playlist
    playlist_tracks = sp.playlist_tracks(playlist_id)

    # Extract unique artists from the playlist
    artists = set(artist['id'] for item in playlist_tracks['items'] for artist in item['track']['artists'])

    # Get random tracks from each artist and similar artists
    recommended_tracks = []
    for artist_id in random.sample(list(artists), min(5, len(artists))):
        # Get random tracks from the artist
        artist_tracks = sp.artist_albums(artist_id, album_type='album,single')['items']
        if artist_tracks:
            random_album = random.choice(artist_tracks)
            album_tracks = sp.album_tracks(random_album['id'])['items']
            recommended_tracks.extend(random.sample(album_tracks, min(2, len(album_tracks))))     

    # Extract artist-track pairs from the playlist
    artist_track_pairs = [
        (artist['name'], item['track']['name'])
        for item in playlist_tracks['items']
        for artist in item['track']['artists']
    ]

    # Function to clean track names (remove versioning, extra suffixes, etc.)
    def clean_track_name(track_name):
        track_name = track_name.lower()
        # Remove common versioning words, parentheses, and extra suffixes
        track_name = re.sub(r'\s*(unplugged|live|remix|acoustic|version|radio|extended|edited|alternative|feat\.|ft\.)\s*[-:\(\[]*.*$', '', track_name)
        track_name = re.sub(r'[-:\(\[]*$', ' ', track_name)  # Clean any remaining punctuation
        return track_name.strip()

    recommended_track_names = set()  # Set to track names we've already added

    for artist_name, track_name in artist_track_pairs:
        # Perform a search with both artist and track name
        search_results = sp.search(q=f'{artist_name} {track_name}', type='track', limit=10)['tracks']['items']

        # Get tracks from the search results, excluding the original track if it's found
        for result in search_results:
            clean_result_name = clean_track_name(result['name'])
            clean_track_name_input = clean_track_name(track_name)

            # Exclude tracks that are essentially the same version or have already been added
            if clean_result_name != clean_track_name_input and clean_result_name not in recommended_track_names:
                recommended_tracks.append(result)
                recommended_track_names.add(clean_result_name)

    # Make sure there are no duplicates (same track in the original playlist)
    recommended_tracks = [
        track for track in recommended_tracks
        if track['id'] not in [item['track']['id'] for item in playlist_tracks['items']]
    ]

    # Make sure there are no songs with the same name as any track in the original playlist
    original_track_names = [clean_track_name(item['track']['name']) for item in playlist_tracks['items']]
    recommended_tracks = [
        track for track in recommended_tracks
        if clean_track_name(track['name']) not in original_track_names
    ]

    # Shuffle the recommended tracks and get URIs (limit to 20)
    random.shuffle(recommended_tracks)
    recommended_track_uris = [track['uri'] for track in recommended_tracks][:20]  # Limit to 20 songs

    # Create a new playlist with recommendations
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_playlist_name = f"Enhanced Recommendations based on {playlist_name} - {current_time}"
    new_playlist = sp.user_playlist_create(user_id, new_playlist_name, public=False)
    new_playlist_id = new_playlist['id']

    # Add recommended tracks to the new playlist
    sp.user_playlist_add_tracks(user_id, new_playlist_id, recommended_track_uris)

    return f'New playlist "{new_playlist_name}" created based on "{playlist_name}"'

if __name__ == '__main__':
    app.run(debug=True)
