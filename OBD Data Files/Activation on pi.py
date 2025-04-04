import time
import os
import paramiko
from datetime import datetime
from zoneinfo import ZoneInfo  # If you need timezones

# --- Configuration ---
HOSTNAME = '34.47.148.16'
USERNAME = 'fast-and-furious'
PRIVATE_KEY_PATH = '/home/pi/.ssh/fast_and_furious_public_key_openSSH.ppm'
REMOTE_DIR = '/home/fast-and-furious/main/section_3_test_drive/'
LOCAL_FILE = '/home/pi/OBD-Data_trackLog.csv'  # Adjust to the actual local path
REMOTE_FILE = os.path.join(REMOTE_DIR, 'OBD-Data_trackLog.csv')


def upload_file(local_path, remote_path):
    """
    Uploads a file via SFTP to the specified remote path.
    """
    # Load private key
    key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)

    # Create and open the SFTP connection
    transport = paramiko.Transport((HOSTNAME, 22))
    transport.connect(username=USERNAME, pkey=key)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Upload the file
    sftp.put(local_path, remote_path)

    # Close the SFTP connection
    sftp.close()
    transport.close()


def main():
    while True:
        try:
            # Optionally, you can log the time of upload or handle partial writes
            # For example:
            print(
                f"[{datetime.now(ZoneInfo('UTC')).isoformat()}] Uploading {LOCAL_FILE} to {REMOTE_FILE} ...")

            # Upload the file
            upload_file(LOCAL_FILE, REMOTE_FILE)

        except Exception as e:
            # Handle exceptions or log errors
            print(f"Error uploading file: {e}")

        # Wait 1 second before the next upload
        time.sleep(1)


if __name__ == "__main__":
    main()
