#!/usr/bin/env python3
"""
Entry point for the Raspberry Pi photo frame application.

On startup the script determines the IP address of the Raspberry Pi, generates
a QR code containing a URL to the configuration web app and displays it on the
Inky Impression e‑paper display.  A Flask app is then started on port 5000
to handle Google Photos authorisation.  Once a valid OAuth token is present
the app periodically downloads photos and displays them on the e‑paper panel.
"""

from threading import Thread
import os
import time
from display import show_qr_code, display_photos_loop
from webapp.app import create_app


def get_ip_address() -> str:
    """Return the first non‑loopback IPv4 address of the machine.

    If multiple network interfaces are active this function picks the first
    address returned by `hostname -I`.
    """
    # Use os.popen rather than socket.gethostbyname to avoid DNS lookup
    ips = os.popen("hostname -I").read().strip().split()
    for ip in ips:
        if not ip.startswith("127."):
            return ip
    return "127.0.0.1"


def main() -> None:
    """Run the photo frame application."""
    # Determine Pi IP and generate a QR code for the configuration page
    host_ip = get_ip_address()
    config_url = f"http://{host_ip}:5000"
    try:
        show_qr_code(config_url)
    except Exception as exc:
        # If the display is not connected, log an error but continue to serve
        print(f"Failed to show QR code on display: {exc}")

    # Create Flask application
    app = create_app(host_ip)

    # Start Flask in a separate thread so we can continue to update photos
    def run_flask():
        app.run(host="0.0.0.0", port=5000, debug=False)

    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Wait for OAuth token and begin displaying photos
    display_photos_loop()


if __name__ == "__main__":
    main()