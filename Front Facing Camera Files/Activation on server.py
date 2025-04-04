# Images for front facing camera is uploaded simultaneously in a folder on virtual machine and this code is on virtual machine to check that is any new image is uploaded on the folder then that image is processed, this task is being done by the watchdog library

import time
import os
import csv
import re
from datetime import datetime
import cv2
import numpy as np
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the folder to monitor and the CSV log file path.
WATCH_FOLDER = "/home/fast-and-furious/main/section_1_test_drive/"
CSV_LOG = "/home/fast-and-furious/main/section_1_test_drive/visibility_log.csv"


def add_alpha_channel(img):
    """
    Add an alpha channel to an image if it doesn't have one.
    The new alpha channel is set to fully opaque (255) for all pixels.
    """
    if img.shape[2] == 3:  # Check if image is in BGR format
        alpha = np.ones((img.shape[0], img.shape[1], 1), dtype=img.dtype) * 255
        img = np.concatenate((img, alpha), axis=2)
    return img


def compute_dark_channel(img, patch_size=15):
    """
    Compute the dark channel of an image.
    For each pixel, the dark channel is the minimum intensity value
    within a patch (of size patch_size) across all color channels.
    """
    min_channel = np.min(img, axis=2)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (patch_size, patch_size))
    dark_channel = cv2.erode(min_channel, kernel)
    return dark_channel


def compute_visibility_percentage(dark_channel_img):
    """
    Calculate a visibility percentage from the dark channel image.
    We assume that lower average dark channel values indicate better visibility.

    Formula:
      visibility (%) = 100 * (1 - (avg_dark / 255))
    """
    avg_dark = np.mean(dark_channel_img)
    visibility_percent = 100 * (1 - (avg_dark / 255))
    visibility_percent = np.clip(visibility_percent, 0, 100)
    return visibility_percent, avg_dark


def extract_timestamp_from_filename(filename):
    """
    Extract date and time from filename.
    Expected filename format: image_YYYYMMDD_HHMMSS.ext
    Returns a tuple (date, time) in string format (YYYY-MM-DD, HH:MM:SS).
    If the pattern is not found, returns None.
    """
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        date_formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        time_formatted = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
        return date_formatted, time_formatted
    else:
        return None


def process_image(file_path):
    """
    Process an image: read it, compute the dark channel and visibility,
    and log the results (with timestamp) into a CSV file.
    """
    # Read the image
    img = cv2.imread(file_path, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Error: Could not read {file_path}")
        return

    # Compute dark channel and visibility metrics.
    dark = compute_dark_channel(img, patch_size=15)
    visibility_percent, avg_dark = compute_visibility_percentage(dark)

    # Extract timestamp from the filename; if not present, use file modification time.
    filename = os.path.basename(file_path)
    timestamp = extract_timestamp_from_filename(filename)
    if timestamp:
        date_formatted, time_formatted = timestamp
    else:
        mod_time = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mod_time)
        date_formatted = dt.strftime("%Y-%m-%d")
        time_formatted = dt.strftime("%H:%M:%S")

    # Log the result into CSV.
    file_exists = os.path.exists(CSV_LOG)
    with open(CSV_LOG, mode='a', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        if not file_exists:
            csvwriter.writerow(["Date", "Time", "Filename",
                               "Visibility (%)", "Avg Dark Value"])
        csvwriter.writerow([date_formatted, time_formatted, filename,
                            f"{visibility_percent:.2f}", f"{avg_dark:.2f}"])

    print(f"Processed {filename}: Date: {date_formatted}, Time: {time_formatted}, Visibility: {visibility_percent:.2f}%, Avg Dark: {avg_dark:.2f}")


class NewFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Ignore directories and non-image files.
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"New file detected: {event.src_path}")
            # Wait briefly to ensure the file is fully written.
            time.sleep(1)
            process_image(event.src_path)


if __name__ == '__main__':
    # Set up the watchdog observer.
    event_handler = NewFileHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()
    print(f"Monitoring folder: {WATCH_FOLDER} for new image files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping folder monitoring.")
        observer.stop()
    observer.join()
