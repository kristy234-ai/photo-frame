"""
Flask configuration web application for the photo frame.

The web app provides a simple interface to start the Google OAuth flow and
finalise authorisation.  It stores credentials in `token.json` in the root
directory.  Additional configuration pages (for Wi‑Fi, album selection, etc.)
can be added here.
"""

from __future__ import annotations

import os
from flask import Flask, render_template, redirect, url_for, request, session
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
]


def create_app(host_ip: str) -> Flask:
    """Factory to create a Flask app bound to the given host IP for redirects.

    Args:
        host_ip: The IPv4 address of the Raspberry Pi.  This is used to
            construct the redirect URI for OAuth callbacks.

    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)
    # A secret key is required for session management; in a production system
    # you should set this to a random value and keep it secret.
    app.secret_key = os.environ.get("PHOTO_FRAME_SECRET_KEY", "dev-secret-key")
    @app.route("/")
    def index():
        """Home page showing configuration status."""
        configured = os.path.exists("token.json")
        return render_template("index.html", configured=configured)

    @app.route("/google_auth")
    def google_auth() -> object:
        """Initiate the OAuth flow and redirect the user to Google's consent page."""
        # The OAuth client configuration must be stored in client_secret.json
        if not os.path.exists("client_secret.json"):
            return "client_secret.json is missing.  Upload it to the project root.", 500
        flow = Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=SCOPES,
            redirect_uri=f"http://{host_ip}:5000/oauth2callback",
        )
        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
        )
        session["state"] = state
        return redirect(authorization_url)

    @app.route("/oauth2callback")
    def oauth2callback():
        """Handle the OAuth redirect and persist the credentials."""
        state = session.get("state")
        if not state:
            return "Session expired.  Start the OAuth flow again.", 400
        flow = Flow.from_client_secrets_file(
            "client_secret.json",
            scopes=SCOPES,
            state=state,
            redirect_uri=f"http://{host_ip}:5000/oauth2callback",
        )
        # Complete the flow using the full redirect URL
        flow.fetch_token(authorization_response=request.url)
        creds = flow.credentials
        # Save the credentials to token.json
        with open("token.json", "w") as token_file:
            token_file.write(creds.to_json())
        return redirect(url_for("index"))

    return app
