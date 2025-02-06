# 🎵 Spotify Recommended Playlist Generator  
## **Status:** This project is currently under development and not yet fully functional.
## (**Currently in-progress of deploying as a Heroku based site)
Generate a custom Spotify playlist based on your existing playlists using the **Spotify API**.

## Features
- Connects to your **Spotify account** to access your playlists.
- Recommends similar songs based on the **artists and tracks** in a selected playlist.
- Creates a **new playlist** with personalized recommendations.
- Uses **Flask** for the web interface.

---

## 1. Setup & Installation  
### Clone the repository  
```bash
git clone https://github.com/frankieburgoyne/SpotifyPlaylistGenerator.git
cd SpotifyPlaylistGenerator
```

---

## 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

---

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 4. Set Up Spotify API Credentials
You must create a Spotify Developer Account and get your Client ID and Client Secret
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Click Create an App and fill in the details.
3. Get your Client ID and Client Secret.
4. Set the Redirect URI to:
```bash
http://127.0.0.1:5000/api_callback
```

---

## 5. Create a .env File
1. Rename .env.example to .env
2. Replace ID, Secret, and Key with your information from Developer Account


---


# Usage
1. Run the Flask app in terminal:
```bash
python application.py
```
2. Open http://127.0.0.1:5000 in your browser
3. Login with your Spotify account
4. Enter the EXACT name of the playlist you want recommendations for
5. A new recommended playlist will be generated in your Spotify account

