# app.py
from flask import Flask, jsonify, session
from dotenv import load_dotenv
from flask_cors import CORS
from blueprints.spotify import spotify_bp  # Import the Spotify blueprint
from blueprints.google import google_bp    # Import the Google blueprint
from blueprints.ytmusic import ytmusic_bp  # Import the YouTube Music blueprint
import os
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SESSION_SECRET")
app.config['SESSION_COOKIE_SECURE'] = True  # Ensures cookies are only sent over HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

CORS(app, supports_credentials=True, origins=[os.getenv("FRONTEND_URL")])

# Register the Spotify Blueprint
app.register_blueprint(spotify_bp, url_prefix='/spotify')

# Register the Google Blueprint
app.register_blueprint(google_bp, url_prefix='/google')

app.register_blueprint(ytmusic_bp, url_prefix='/ytmusic')

@app.route('/session')
def session_info():
    print("Session info requested", session)
    if 'spotify_token_info' in session or 'google_token_info' in session:
        return jsonify(dict(session))
    return jsonify({"message": "No user logged in"}), 401

@app.route('/logout')
def logout():
    session.clear()
    response = jsonify({"message": "Logged out successfully"})
    response.set_cookie('session', '', expires=0)  # Expire the session cookie
    return response




# Run the Flask application


if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT")), debug=True)
