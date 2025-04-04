# this is capturing image from front camera at every 3 seconds and sending the captured image on virtual machine engine

import time
import os
from picamera2 import Picamera2
import paramiko
from datetime import datetime
from zoneinfo import ZoneInfo  # For timezone-aware timestamps

# --- Configuration ---
HOSTNAME = '34.47.148.16'
USERNAME = 'fast-and-furious'
PRIVATE_KEY_PATH = '/home/pi/.ssh/fast_and_furious_public_key_openSSH.ppm'
REMOTE_DIR = '/home/fast-and-furious/main/section_1_test_drive/'

# --- Initialize Picamera2 ---
picam2 = Picamera2()
config = picam2.create_still_configuration()
picam2.configure(config)
picam2.start()
time.sleep(2)  # Allow the camera to warm up

# --- Setup SFTP connection using Paramiko with RSA key ---
try:
    key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)
except Exception as e:
    print(f"Failed to load RSA key: {e}")
    exit(1)

transport = paramiko.Transport((HOSTNAME, 22))
try:
    transport.connect(username=USERNAME, pkey=key)
except Exception as e:
    print(f"Failed to connect via SFTP: {e}")
    exit(1)
    
sftp = paramiko.SFTPClient.from_transport(transport)

print("Starting image capture and transfer. Press Ctrl+C to stop.")

try:
    while True:
        # Generate a human-readable, timezone-aware timestamp (e.g., UTC)
        tz = ZoneInfo("Asia/Kolkata")  # Update the timezone as needed
        timestamp = datetime.now(tz).strftime("%Y%m%d_%H%M%S")
        filename = f'image_{timestamp}.jpg'
        
        # Capture the image using Picamera2.
        picam2.capture_file(filename)
        print(f"Captured {filename}")
        
        # Upload the image to the remote directory.
        remote_filepath = os.path.join(REMOTE_DIR, filename)
        sftp.put(filename, remote_filepath)
        print(f"Transferred {filename} to {remote_filepath}")
        
        # Optionally remove the local file after transfer.
        os.remove(filename)
        
        # Wait for one second before capturing the next image.
        time.sleep(3)

except KeyboardInterrupt:
    print("Terminated by user.")

finally:
    sftp.close()
    transport.close()
    picam2.stop()
