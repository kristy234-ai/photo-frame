# Raspberry Pi Photo Frame with Inky Impression 7‑colour Display

## Overview

This project turns a Raspberry Pi into a self‑contained picture frame that displays
photos from your Google Photos library on a Pimoroni **Inky Impression**
e‑paper display.  The Inky Impression is a 7‑colour (black, white, red, green,
blue, yellow and orange) e‑paper panel with low power consumption.  It has a
resolution of 600×448 pixels and retains images even when power is removed,
making it ideal for always‑on, low‑power photo displays【468744705003288†L77-L100】.  Because
e‑paper refreshes slowly (~30 seconds per update) it is well suited to
applications where the image changes infrequently【468744705003288†L99-L100】.

When the Raspberry Pi boots for the first time the frame draws a **QR code** on
the Inky display.  Scanning this QR code opens a configuration web page
hosted on the Pi.  Through this page you can authorise the device to access
your Google Photos library and start displaying your pictures.  The Pi stores
OAuth credentials locally and periodically fetches and displays new photos.

## Hardware required

* **Raspberry Pi** (any model with a 40‑pin header will work).  Pi Zero 2 W
  or Raspberry Pi 5 are recommended for wireless connectivity and CPU
  performance.
* **Pimoroni Inky Impression** 5.7 inch or 7.3 inch 7‑colour e‑paper HAT.
  The display supports seven colours and has a crisp, wide‑angle screen
  【468744705003288†L77-L108】.  It attaches to the Pi via the 40‑pin GPIO header and
  requires SPI and I²C to be enabled【468744705003288†L103-L113】.
* **Micro‑SD card** (8 GB or larger) flashed with Raspberry Pi OS.
* **Power supply** for your Pi.
* A **smartphone** or computer with a camera to scan QR codes.

## Preparing the Raspberry Pi image

1. **Flash Raspberry Pi OS**:  Download the latest Raspberry Pi OS Lite or
   Full image from the Raspberry Pi website and flash it to an SD card using
   Raspberry Pi Imager or balenaEtcher.
2. **Enable SSH (optional)**:  Create an empty file named `ssh` in the SD
   card’s `boot` partition to enable SSH at first boot.
3. **Configure Wi‑Fi (optional)**:  You may pre‑configure Wi‑Fi by adding
   `wpa_supplicant.conf` to the `boot` partition.  If you skip this step
   the device will show a QR code for configuration.
4. **Insert the SD card** and attach the Inky Impression display to the Pi.
5. **Boot the Pi**.  On first boot the display will stay blank for about
   30 seconds while the code initialises (e‑paper refresh time【468744705003288†L99-L100】).

## Installation and setup

These steps assume you have network access to the Pi via SSH or a local
keyboard/monitor.

1. **Clone this repository**

   ```sh
   git clone https://github.com/YOUR_USERNAME/photo-frame.git
   cd photo-frame
   ```

   Replace `YOUR_USERNAME` with your GitHub username once the repository is
   created.

2. **Install system dependencies**

   Enable SPI and I²C interfaces using `raspi-config`:

   ```sh
   sudo raspi-config
   # Navigate to Interface Options → SPI → enable
   # Navigate to Interface Options → I2C → enable
   sudo reboot
   ```

3. **Install Python dependencies**

   It is recommended to use a virtual environment:

   ```sh
   sudo apt update
   sudo apt install python3-venv python3-pip -y
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   The `inky` Python library provides an easy API for driving the e‑paper
   display【640128535581685†L445-L479】, and `qrcode`, `Flask` and Google API
   libraries are used for generating QR codes, hosting the configuration
   web page, and accessing Google Photos.

4. **Google API credentials**

   To fetch photos you must register a project in the [Google Cloud
   Console](https://console.cloud.google.com/) and enable the **Google Photos
   Library API**.  Create OAuth 2.0 **Client ID** credentials of type
   “Desktop Application” and download the `client_secret.json` file.  Copy
   this file into the root of the repository on the Pi.  During
   configuration the app will guide you through authorising the device with
   your Google account.

5. **Run the application**

   Start the photo frame by running:

   ```sh
   source venv/bin/activate
   python3 main.py
   ```

   On first launch the Inky display will show a QR code pointing at the
   device’s configuration page.  Scan the code with your phone and follow
   the instructions to authorise access to your Google Photos library.  The
   Google Photos API returns a `baseUrl` for each media item.  To download
   an image while retaining metadata you append the `d` parameter (for
   “download”) to the base URL【746387997225079†L360-L376】.  The app uses this
   pattern when fetching images.

6. **Auto‑start on boot** (optional)

   To start the photo frame automatically on boot you can create a
   `systemd` service.  Create a file `/etc/systemd/system/photo_frame.service`
   with the following contents (adjust the paths to match your setup):

   ```ini
   [Unit]
   Description=Raspberry Pi Photo Frame
   After=network.target

   [Service]
   User=pi
   WorkingDirectory=/home/pi/photo-frame
   ExecStart=/home/pi/photo-frame/venv/bin/python3 /home/pi/photo-frame/main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Then enable and start the service:

   ```sh
   sudo systemctl daemon-reload
   sudo systemctl enable photo_frame.service
   sudo systemctl start photo_frame.service
   ```

## How it works

* **QR code display** – On startup the application determines the Pi’s IP
  address, generates a QR code containing the URL of the local configuration
  web server and draws it on the Inky Impression.  A white background is
  created the size of the display and the QR code is centred on it.  The
  `inky` library handles pushing the image to the panel【640128535581685†L445-L479】.
* **Configuration web app** – A small Flask web app runs on the Pi.  When
  accessed it lets you initiate Google OAuth flow.  It uses the
  `client_secret.json` downloaded from the Google Cloud Console and
  stores the resulting OAuth token in `token.json`.
* **Photo download and display** – After authorisation the app
  periodically lists the most recent media items in your Google Photos
  library, downloads them via the `baseUrl` plus `d` parameter
  【746387997225079†L360-L376】, resizes them to the display resolution and
  shows them.  Because the display takes about 30 seconds to refresh
  【468744705003288†L99-L100】 it rotates the image at most once per hour by default.

## Extending the project

* **Different displays** – The code uses `inky.auto()` to detect
  compatible Inky boards, so it should work with other sizes (for example
  the 4 inch or 7.3 inch Inky Impression) without changes.  You can adapt
  the `display.py` module to support additional SPI‑based displays.
* **Wi‑Fi configuration** – The project currently expects Wi‑Fi to be
  pre‑configured via `wpa_supplicant.conf`.  You could extend the
  configuration web app to collect SSID and passphrase and write them to
  `/etc/wpa_supplicant/wpa_supplicant.conf` before rebooting.
* **Albums and filters** – Modify `photos.py` to request specific albums or
  filter by creation date when listing media items.  See Google’s
  documentation for details on the `mediaItems.search` endpoint and
  filters.

## License

All code in this repository is released under the MIT License.  See
`LICENSE` for details.  Third‑party libraries retain their respective
licenses.