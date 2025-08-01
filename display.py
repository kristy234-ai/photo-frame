"""
Display utilities for the Inky Impression 7‑colour e‑paper display.

This module wraps the Pimoroni `inky` library to show QR codes and photographs
on the display.  It automatically detects the attached display using
`inky.auto()` so the same code can drive different sizes of Inky boards.
"""

from __future__ import annotations

import os
import time
from typing import Optional

import qrcode
from PIL import Image, ImageOps

try:
    # Importing inky.auto will attempt to detect a connected Inky display.
    from inky.auto import auto as inky_auto

    INKY_DISPLAY = inky_auto()
    WIDTH, HEIGHT = INKY_DISPLAY.resolution
except Exception as exc:  # pragma: no cover - hardware not present in CI
    INKY_DISPLAY = None
    WIDTH, HEIGHT = (600, 448)  # Default resolution for Inky Impression 5.7"
    print(f"Inky display not available: {exc}")

from photos import get_next_photo


def show_qr_code(url: str) -> None:
    """Generate and display a QR code containing the provided URL.

    The QR code is centered on a white background the size of the e‑paper
    display.  If no hardware is present the image is saved to `qr.png` for
    debugging.

    Args:
        url: The URL to encode in the QR code.
    """
    qr = qrcode.QRCode(box_size=2, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    # Create a white canvas matching the display resolution
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "white")
    # Scale the QR code to fit comfortably on the display
    qr_size = min(WIDTH, HEIGHT) - 20
    qr_img = qr_img.resize((qr_size, qr_size), Image.NEAREST)
    canvas.paste(qr_img, ((WIDTH - qr_size) // 2, (HEIGHT - qr_size) // 2))
    if INKY_DISPLAY:
        INKY_DISPLAY.set_border(INKY_DISPLAY.WHITE)
        INKY_DISPLAY.set_image(canvas)
        # E‑paper refreshes slowly (~30 seconds)
        INKY_DISPLAY.show()
    else:
        canvas.save("qr.png")


def display_image(image: Image.Image) -> None:
    """Display a PIL image on the e‑paper panel.

    The image is resized/cropped to fit the display while preserving aspect
    ratio.  Colour conversion is performed by the `inky` library automatically
    when `set_image` is called.

    Args:
        image: PIL image to display.
    """
    if not INKY_DISPLAY:
        # In headless environments write the output image to disk for testing
        image.save("latest_display.png")
        return
    # Resize and crop the image to fit the display resolution
    fitted = ImageOps.fit(image, (WIDTH, HEIGHT))
    INKY_DISPLAY.set_image(fitted)
    INKY_DISPLAY.show()


def display_photos_loop(interval_seconds: int = 3600) -> None:
    """Repeatedly fetch and display photos from Google Photos.

    This function blocks and should be run in the main thread once the Flask
    server has been started.  It waits until the OAuth token file exists
    (indicating that the user has authorised access) before downloading photos.

    Args:
        interval_seconds: Time in seconds between image updates (default 1 hour).
    """
    # Wait for token.json to appear (authorisation complete)
    while not os.path.exists("token.json"):
        time.sleep(5)
    # Main loop: fetch the next photo and display it
    while True:
        photo_path = get_next_photo()
        if photo_path and os.path.exists(photo_path):
            try:
                with Image.open(photo_path) as img:
                    display_image(img.convert("RGB"))
            except Exception as exc:
                print(f"Failed to display {photo_path}: {exc}")
        else:
            print("No photos downloaded yet.")
        time.sleep(interval_seconds)