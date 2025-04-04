#!/usr/bin/env python3
# This file is estabilising a serial communication between raspberry pi and arduino. It is taking mq3 data from arduino at a baud rate of 115200 and updating csv file on virtual machine engine

import serial
import time
import paramiko
from datetime import datetime
from zoneinfo import ZoneInfo

# -------------------------
# Configuration
# -------------------------
SERIAL_PORT       = "/dev/ttyACM0"
BAUD_RATE         = 115200
LOCAL_TIMEZONE    = ZoneInfo("Asia/Kolkata")  # e.g. "America/New_York"

# SSH/SFTP config
HOSTNAME          = "34.47.148.16"
USERNAME          = "fast-and-furious"
PRIVATE_KEY_PATH  = "/home/pi/.ssh/fast_and_furious_public_key_openSSH.ppm"

# Remote CSV path (watch out for spaces, just quote the path if needed)
REMOTE_CSV_PATH   = "/home/fast-and-furious/main/section_4_test_drive/mq3_data.csv"

def main():
    # 1) Connect to Arduino
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1.0)
    time.sleep(3)
    ser.reset_input_buffer()
    print("Serial connection established.")

    # 2) Set up Paramiko SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.load_system_host_keys()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh_client.connect(
            hostname=HOSTNAME,
            username=USERNAME,
            key_filename=PRIVATE_KEY_PATH
        )
        # 3) Open a session and run `cat >> remote_file` to append incoming data
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        # The command below appends all incoming data on this channel to 'mq3_data.csv'
        channel.exec_command(f'cat >> "{REMOTE_CSV_PATH}"')

        print("SSH channel established. Streaming data to remote CSV...")

        try:
            while True:
                time.sleep(0.01)
                if ser.in_waiting > 0:
                    line = ser.readline().decode("utf-8").rstrip()
                    # Build a timestamped CSV line
                    now = datetime.now(tz=LOCAL_TIMEZONE).isoformat()
                    csv_line = f"{now},{line}\n"
                    # 4) Send the CSV line over the channel
                    channel.send(csv_line)
                    print(csv_line, end="")  # Local debug
        except KeyboardInterrupt:
            print("Stopping data collection...")

        # Close the channel (this will end the 'cat >>' on the remote side)
        channel.close()

    except Exception as e:
        print(f"SSH Error: {e}")
    finally:
        ssh_client.close()
        ser.close()
        print("Closed serial and SSH connections.")

if __name__ == "__main__":
    main()
