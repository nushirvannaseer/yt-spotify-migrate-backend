# google.py
import os
import time
from flask import Blueprint, redirect, request, session, jsonify
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create a Blueprint for Google-related routes
google_bp = Blueprint('google', __name__)

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

# Route to initiate Google login
@google_bp.route('/login')
def google_login():
    try:
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/youtube&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return redirect(auth_url)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Callback route for Google OAuth
@google_bp.route('/callback')
def google_callback():
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()

        if 'refresh_token' in token_info and 'expires_in' in token_info:
            session["google_token_info"] = {
                'refresh_token': token_info['refresh_token'],
                'expires_in': token_info['expires_in'],
                'expires_at': time.time() + token_info['expires_in'],
                'access_token': token_info['access_token'],
                'token_type': token_info['token_type'],
                'scope': token_info['scope'],
            }
        else:
            return jsonify({'error': 'Error fetching tokens', 'details': token_info}), 400

        return redirect(os.getenv("FRONTEND_URL"))  # Redirect to frontend after login
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to refresh Google token
@google_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    try:
        google_token_info = session.get("google_token_info")
        if not google_token_info or 'refresh_token' not in google_token_info:
            return jsonify({'error': 'No refresh token available'}), 400

        if time.time() >= google_token_info['expires_at']:
            refresh_token = google_token_info['refresh_token']
            token_url = "https://oauth2.googleapis.com/token"
            refresh_data = {
                'client_id': GOOGLE_CLIENT_ID,
                'client_secret': GOOGLE_CLIENT_SECRET,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            }
            refresh_response = requests.post(token_url, data=refresh_data)
            refresh_response.raise_for_status()
            new_token_info = refresh_response.json()
            session["google_token_info"] = {
                'refresh_token': new_token_info.get('refresh_token', refresh_token),
                'expires_in': new_token_info.get('expires_in'),
                'expires_at': time.time() + new_token_info.get('expires_in', 0),
                'access_token': new_token_info.get('access_token'),
                'token_type': new_token_info.get('token_type'),
                'scope': new_token_info.get('scope'),
            }
            return jsonify(new_token_info)
        else:
            return jsonify({"message": "Token is still valid."})
    except requests.exceptions.RequestException as e:
        return jsonify({'error': 'Request failed', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
