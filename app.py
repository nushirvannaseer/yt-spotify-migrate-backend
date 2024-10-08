# app.py
from pprint import pprint
from flask import Flask, json, jsonify, session
from dotenv import load_dotenv
from flask_cors import CORS
from blueprints.spotify import spotify_bp  # Import the Spotify blueprint
from blueprints.google import google_bp    # Import the Google blueprint
from blueprints.ytmusic import ytmusic_bp  # Import the YouTube Music blueprint
import os
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SESSION_SECRET")
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
    if ('spotify_token_info' in session and 'current_user' in session) or 'google_token_info' in session:
        return jsonify(dict(session))
    return jsonify({"error": "No user logged in"}), 401

@app.route('/logout')
def logout():

    session['spotify_token_info'] = None
    session['google_token_info'] = None 
    session['current_user'] = None
    session.clear()
    response = jsonify({"message": "Logged out successfully"})
    response.set_cookie('session', '', expires=0)  # Expire the session cookie
    return response




# Run the Flask application
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))  # Default to 5000 if PORT is not set
    app.run(host="0.0.0.0", port=port, debug=True)