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
app.secret_key = "your-secret-key"

CORS(app, origins=[os.getenv("FRONTEND_URL")], supports_credentials=True)


# Register the Spotify Blueprint
app.register_blueprint(spotify_bp, url_prefix='/spotify')

# Register the Google Blueprint
app.register_blueprint(google_bp, url_prefix='/google')

app.register_blueprint(ytmusic_bp, url_prefix='/ytmusic')

@app.route('/session')
def session_info():
    return jsonify(session)



# Run the Flask application


if __name__ == '__main__':
    app.run(port=int(os.getenv("PORT")), debug=True)
