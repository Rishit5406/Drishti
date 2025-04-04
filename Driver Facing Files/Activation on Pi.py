# chnages required
# this is capturing image of driver side, processing the frames and sending the results obtained from integrating the dlib model on virtual machine engine.

import cv2
import dlib
import numpy as np
import paramiko
from datetime import datetime
from zoneinfo import ZoneInfo

# ===============================
# Configuration and Constants
# ===============================
# Drowsiness Detection Constants (time-based)
DROWSY_TIME_THRESHOLD = 3.0   # seconds required to trigger drowsiness alert
SLEEP_TIME_THRESHOLD = 8.0    # seconds required to trigger sleep alert
EYE_AR_THRESH = 0.22         # EAR threshold for eye closure
USB_CAM_INDEX = 0            # USB Camera index
LANDMARKS_MODEL = "/home/pi/Desktop/main/section2_shape_predictor_68_face_landmarks.dat"  # dlib's landmarks model path

# Yawning Detection Constants (time-based)
YAWN_THRESHOLD = 0.7               # Lip Aspect Ratio (LAR) threshold for yawning
EAR_THRESHOLD_FOR_YAWNING = 0.10   # Additional EAR check for yawning (ensuring eyes are almost closed)
YAWN_TIME_THRESHOLD = 3.0          # seconds required to count as a yawn

# Remote Server Configuration
HOSTNAME = '34.47.148.16'
USERNAME = 'fast-and-furious'
PRIVATE_KEY_PATH = '/home/pi/.ssh/fast-and-furious_public_key_openSSH.ppm'

# CSV Paths on remote server
REMOTE_DROWSINESS_LOG_PATH = "/home/fast-and-furious/main/section_2_test_drive/drowsiness_log.csv"
REMOTE_YAWNING_LOG_PATH = "/home/fast-and-furious/main/section_2_test_drive/yawning_log.csv"
REMOTE_COMBINED_LOG_PATH = "/home/fast-and-furious/main/section_2_test_drive/combined_log.csv"

# Local CSV file for combined logging on Raspberry Pi
LOCAL_COMBINED_LOG_PATH = "/home/pi/Desktop/main/combined_log.csv"

# ===============================
# Initialize dlib Models
# ===============================
try:
    face_detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(LANDMARKS_MODEL)
except Exception as e:
    print(f"Error: Unable to load the landmarks model ({LANDMARKS_MODEL}). Please verify the file path.")
    print(e)
    exit()

# ===============================
# Helper Functions for Detection
# ===============================
def calculate_eye_aspect_ratio(eye_points):
    """
    Compute the Eye Aspect Ratio (EAR) from eye landmark coordinates.
    """
    A = np.linalg.norm(np.array(eye_points[1]) - np.array(eye_points[5]))
    B = np.linalg.norm(np.array(eye_points[2]) - np.array(eye_points[4]))
    C = np.linalg.norm(np.array(eye_points[0]) - np.array(eye_points[3]))
    return (A + B) / (2.0 * C)

def process_faces(gray_frame, faces, shape_predictor):
    """
    Process each detected face and compute EAR for both eyes.
    Returns a list of tuples: (landmarks, left_ear, right_ear)
    """
    results = []
    for face in faces:
        landmarks = shape_predictor(gray_frame, face)
        left_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
        right_eye_points = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]
        left_ear = calculate_eye_aspect_ratio(left_eye_points)
        right_ear = calculate_eye_aspect_ratio(right_eye_points)
        results.append((landmarks, left_ear, right_ear))
    return results

def lip_aspect_ratio(landmarks):
    """
    Compute the Lip Aspect Ratio (LAR) using specific mouth landmarks.
    """
    top_lip = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in [50, 52, 56, 58]])
    bottom_lip = np.array([(landmarks.part(n).x, landmarks.part(n).y) for n in [48, 54]])
    A = np.linalg.norm(top_lip[0] - top_lip[3])
    B = np.linalg.norm(top_lip[1] - top_lip[2])
    C = np.linalg.norm(bottom_lip[0] - bottom_lip[1])
    return (A + B) / (2.0 * C)

# ===============================
# Helper Functions for Logging
# ===============================
def update_remote_csv(remote_file_path, entry):
    """
    Connect to the remote server and append a new entry to the specified CSV file.
    """
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(HOSTNAME, username=USERNAME, key_filename=PRIVATE_KEY_PATH)
        sftp = client.open_sftp()
        remote_file = sftp.open(remote_file_path, "a")
        remote_file.write(entry + "\n")
        remote_file.flush()
        remote_file.close()
        sftp.close()
        client.close()
    except Exception as e:
        print(f"Error updating remote CSV ({remote_file_path}): {e}")

def update_local_csv(local_file_path, entry):
    """
    Append a new entry to the local CSV file.
    """
    try:
        with open(local_file_path, "a") as f:
            f.write(entry + "\n")
    except Exception as e:
        print(f"Error updating local CSV ({local_file_path}): {e}")

def log_drowsiness(status, drowsiness_percent):
    """
    Log a new drowsiness event with timestamp, status, and drowsiness percentage
    to the dedicated drowsiness log.
    """
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()
    entry = f"{timestamp},{status},{drowsiness_percent}"
    update_remote_csv(REMOTE_DROWSINESS_LOG_PATH, entry)

def log_yawning(total_yawns, yawn_percent):
    """
    Log a new yawning event with timestamp, total yawns, and the yawning percentage
    to the dedicated yawning log.
    """
    timestamp = datetime.now(ZoneInfo("UTC")).isoformat()
    entry = f"{timestamp},{total_yawns},{yawn_percent}"
    update_remote_csv(REMOTE_YAWNING_LOG_PATH, entry)

def log_combined_data(timestamp, left_ear, right_ear, lar, drowsiness_percent, driver_status, yawn_or_not):
    """
    Log a combined row to both the remote and local CSV files with all relevant fields.
    CSV Columns:
    timestamp, left_ear, right_ear, lar, drowsiness_percent, driver_status, yawn_or_not
    """
    entry = (
        f"{timestamp},"
        f"{left_ear:.3f},"
        f"{right_ear:.3f},"
        f"{lar:.3f},"
        f"{drowsiness_percent:.1f},"
        f"{driver_status},"
        f"{yawn_or_not}"
    )
    # Log to remote combined CSV
    update_remote_csv(REMOTE_COMBINED_LOG_PATH, entry)
    # Log to local combined CSV on the Raspberry Pi
    update_local_csv(LOCAL_COMBINED_LOG_PATH, entry)

# ===============================
# Video Capture Initialization
# ===============================
cap = cv2.VideoCapture(USB_CAM_INDEX)
if not cap.isOpened():
    print("Error: Could not open USB camera. Please verify that it is connected.")
    exit()

# ===============================
# Variables for Time-Based Tracking
# ===============================
closed_start_time = None  # time when eyes first detected closed
yawn_start_time = None    # time when yawning condition started
yawn_count = 0            # total yawn events detected

# ===============================
# Main Loop: Process Each Frame
# ===============================
while True:
    ret, frame = cap.read()
    if not ret:
        break  # End loop if frame not read properly

    # Use current time (as float seconds) from the desired timezone
    current_dt = datetime.now(ZoneInfo("Asia/Kolkata"))
    timestamp = current_dt.isoformat()
    current_time = current_dt.timestamp()

    # Convert frame to grayscale for face detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)

    # If no face is detected, reset timers and log "N/A" values.
    if len(faces) == 0:
        closed_start_time = None
        yawn_start_time = None
        driver_status = "N/A"
        drowsiness_percent = 0.0
        left_ear = 0.0
        right_ear = 0.0
        lar = 0.0
        yawn_or_not = "No"
        print(f"{timestamp}, Left EAR: N/A, Right EAR: N/A, LAR: N/A, Drowsiness%: {drowsiness_percent:.1f}, Status: {driver_status}, Yawn: {yawn_or_not}")
        log_combined_data(timestamp, left_ear, right_ear, lar, drowsiness_percent, driver_status, yawn_or_not)
        continue

    # Process the first detected face (adjust if you want to handle multiple faces)
    results = process_faces(gray, faces, shape_predictor)
    landmarks, left_ear, right_ear = results[0]
    lar = lip_aspect_ratio(landmarks)
    avg_ear = (left_ear + right_ear) / 2.0

    # ---------------------------
    # Time-based Drowsiness Detection
    # ---------------------------
    both_eyes_closed = (left_ear < EYE_AR_THRESH and right_ear < EYE_AR_THRESH)
    if both_eyes_closed:
        if closed_start_time is None:
            closed_start_time = current_time  # start timer when eyes first close
        closed_duration = current_time - closed_start_time
    else:
        closed_duration = 0
        closed_start_time = None

    # Determine driver status based on closed eye duration
    if closed_duration >= SLEEP_TIME_THRESHOLD:
        driver_status = "ALERT: Driver Sleeping!"
        drowsiness_percent = 100.0
    elif closed_duration >= DROWSY_TIME_THRESHOLD:
        driver_status = "ALERT: High Drowsiness!"
        # Optionally compute a percentage relative to the window between thresholds
        drowsiness_percent = ((closed_duration - DROWSY_TIME_THRESHOLD) / (SLEEP_TIME_THRESHOLD - DROWSY_TIME_THRESHOLD)) * 100.0
    else:
        driver_status = "Driver Awake"
        drowsiness_percent = 0.0

    # ---------------------------
    # Time-based Yawning Detection
    # ---------------------------
    if (lar > YAWN_THRESHOLD and avg_ear < EAR_THRESHOLD_FOR_YAWNING):
        if yawn_start_time is None:
            yawn_start_time = current_time  # start yawning timer
        yawn_duration = current_time - yawn_start_time
    else:
        if yawn_start_time is not None:
            yawn_duration = current_time - yawn_start_time
            if yawn_duration >= YAWN_TIME_THRESHOLD:
                yawn_detected = True
            else:
                yawn_detected = False
            yawn_start_time = None
        else:
            yawn_duration = 0
            yawn_detected = False

    yawn_or_not = "Yes" if ((yawn_start_time is not None and (current_time - yawn_start_time) >= YAWN_TIME_THRESHOLD) or (yawn_duration >= YAWN_TIME_THRESHOLD)) else "No"
    if yawn_or_not == "Yes":
        yawn_count += 1
        log_yawning(yawn_count, min(100.0, (yawn_duration / YAWN_TIME_THRESHOLD) * 100.0))
        yawn_start_time = None

    # ---------------------------
    # Print and Log Combined Data
    # ---------------------------
    print(
        f"{timestamp}, "
        f"Left EAR: {left_ear:.3f}, Right EAR: {right_ear:.3f}, LAR: {lar:.3f}, "
        f"Drowsiness%: {drowsiness_percent:.1f}, Status: {driver_status}, Yawn: {yawn_or_not}"
    )
    log_combined_data(timestamp, left_ear, right_ear, lar, drowsiness_percent, driver_status, yawn_or_not)

    # Optionally, display the live video feed (uncomment if desired)
    # cv2.imshow("Live Feed", frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

# Clean up resources
cap.release()
cv2.destroyAllWindows()
