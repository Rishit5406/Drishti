import os
import csv
import time
import requests
import pandas as pd

# === Configuration ===
# Replace with your actual Gemini API endpoint
GEMINI_API_URL = "https://api.gemini.example.com/analyze"
API_KEY = "your_gemini_api_key"  # Replace with your Gemini API key
CSV_FILE_PATH = '/home/fast-and-furious/main/section_3_test_drive/OBD-Data_trackLog.csv'
CSV_RESPONSE_LOG = '/home/fast-and-furious/main/section_3_test_drive/gemini_response.csv'
COLUMNS = [
    'GPS Time',
    'Bearing',
    'Acceleration Sensor(Total)(g)',
    'Acceleration Sensor(X axis)(g)',
    'Acceleration Sensor(Y axis)(g)',
    'Acceleration Sensor(Z axis)(g)',
    'Engine Load(%)',
    'Speed (OBD)(km/h)',
    'Throttle Position(Manifold)(%)'
]

# === Gemini API Prompt ===
BASE_PROMPT = (
    "Please process the CSV data provided below. The CSV contains several columns, but focus only on these:\n"
    "- 'GPS Time'\n"
    "- 'Bearing'\n"
    "- 'Acceleration Sensor(Total)(g)'\n"
    "- 'Acceleration Sensor(X axis)(g)'\n"
    "- 'Acceleration Sensor(Y axis)(g)'\n"
    "- 'Acceleration Sensor(Z axis)(g)'\n"
    "- 'Engine Load(%)'\n"
    "- 'Speed (OBD)(km/h)'\n"
    "- 'Throttle Position(Manifold)(%)'\n\n"
    "The CSV updates in real time at 10 rows per second. Your task is to detect instances of rash driving by identifying the following patterns:\n"
    "1. Aggressive Acceleration – sudden, high increases in acceleration exceeding typical thresholds.\n"
    "2. Sharp Turn – rapid changes in 'Bearing' combined with variations in 'Acceleration Sensor(X axis)(g)', 'Acceleration Sensor(Y axis)(g)', and 'Speed (OBD)(km/h)'.\n"
    "3. Harsh Braking – rapid deceleration shown by a sudden drop in 'Speed (OBD)(km/h)' and corresponding acceleration sensor values.\n"
    "4. Speeding over a Speed Breaker or in a Pothole – unusual speed profiles along with abrupt fluctuations in 'Acceleration Sensor(Y axis)(g)'.\n\n"
    "For each detected event, return the following details:\n"
    "- Timestamp (from 'GPS Time')\n"
    "- Fault type (e.g., Aggressive Acceleration, Sharp Turn, Harsh Braking, Speeding over a Speed Breaker/Pothole)\n"
    "- Sensor parameters and values that led to the decision.\n\n"
    "Below is the CSV data:"
)

# === Helper Functions ===


def get_csv_data():
    """
    Reads the CSV and returns the data for the required columns as a CSV-formatted string.
    """
    try:
        df = pd.read_csv(CSV_FILE_PATH, usecols=COLUMNS)
        return df.to_csv(index=False)
    except Exception as e:
        print("Error reading CSV file:", e)
        return None


def log_response(response_data):
    """
    Logs the Gemini response into the specified CSV file.
    Expects response_data to be a dict with keys 'GPS Time', 'Fault', and 'Parameters'.
    """
    file_exists = os.path.isfile(CSV_RESPONSE_LOG)
    try:
        with open(CSV_RESPONSE_LOG, 'a', newline='') as csvfile:
            fieldnames = ['GPS Time', 'Fault', 'Parameters']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            # Write header if file doesn't exist yet
            if not file_exists:
                writer.writeheader()
            writer.writerow(response_data)
    except Exception as e:
        print("Error logging response:", e)


def analyze_data():
    """
    Reads the CSV data, builds the Gemini prompt, sends it to the Gemini API,
    prints the result, and logs the response.
    """
    csv_data = get_csv_data()
    if csv_data is None:
        return

    # Build the full prompt by appending the CSV data
    full_prompt = f"{BASE_PROMPT}\n\n{csv_data}"

    payload = {
        "prompt": full_prompt,
        # Add any additional Gemini API parameters if needed
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("Gemini Analysis Result:", result)

            # Map the result to our logging format. Adjust keys if needed.
            data_to_log = {
                'GPS Time': result.get('timestamp', 'N/A'),
                'Fault': result.get('fault', 'N/A'),
                'Parameters': result.get('parameters', 'N/A')
            }
            log_response(data_to_log)
        else:
            print("Gemini API Error:", response.status_code, response.text)
    except Exception as e:
        print("Error connecting to Gemini API:", e)


# === Main Loop ===
if __name__ == '__main__':
    while True:
        analyze_data()
        # Sleep for one second (adjust as necessary based on CSV update frequency)
        time.sleep(1)
