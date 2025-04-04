import os
import pandas as pd
import requests

# --- Configuration ---

# File paths
visibility_log_path = '/home/fast-and-furious/main/section_1_test_drive/visibility_log.csv'
obd_data_path = '/home/fast-and-furious/main/section_3_test_drive/OBD Data TrackLog.csv'
gemini_response_path = '/home/fast-and-furious/main/section_3_test_drive/gemini_response.csv'

# Gemini API configuration (update with your actual endpoint and API key)
# Replace with your actual Gemini API endpoint
GEMINI_API_URL = 'https://api.gemini.example.com/analyze'
API_KEY = 'your_gemini_api_key'  # Replace with your actual API key

# --- Load and Prepare Data ---

# Read OBD CSV; assume it has "GPS Time" and "Speed (OBD)(km/h)"
df_obd = pd.read_csv(obd_data_path)
df_obd['GPS Time'] = pd.to_datetime(df_obd['GPS Time'])
df_obd.sort_values('GPS Time', inplace=True)

# Read visibility CSV; assume it has "Time Stamp" (only time in HH:MM:SS format) and "Visibility (%)"
df_visibility = pd.read_csv(visibility_log_path)
# Extract the date from the first OBD entry (assuming both logs are from the same day)
default_date = df_obd['GPS Time'].iloc[0].date()
# Combine the default date with the time from visibility CSV
df_visibility['Time Stamp'] = pd.to_datetime(
    df_visibility['Time Stamp'].apply(lambda t: f"{default_date} {t}"))
df_visibility.sort_values('Time Stamp', inplace=True)

# --- Merge Data Based on Timestamps ---

# Use merge_asof to align the two DataFrames on their timestamps.
# We set a tolerance of 2 seconds (adjust as needed) to account for small differences.
merged = pd.merge_asof(
    df_visibility, df_obd,
    left_on='Time Stamp', right_on='GPS Time',
    direction='nearest', tolerance=pd.Timedelta(seconds=2)
)

# Drop rows where a match wasn't found (if any)
merged = merged.dropna(subset=['Speed (OBD)(km/h)'])

# For the purpose of the Gemini prompt, we'll use a subset of columns.
merged_subset = merged[['Time Stamp', 'Visibility (%)', 'Speed (OBD)(km/h)']]

# Convert the merged data into a CSV-formatted string.
csv_data = merged_subset.to_csv(index=False)

# --- Build Gemini API Prompt ---

prompt = f"""
Please analyze the following data and determine if there is a driving risk based on the vehicle's visibility percentage and current speed.
Note:
- Visibility (%) is relative and may vary based on camera calibration and the method of calculation.
- The timestamps come from two different logs: one provides only time (which we combined with a default date) and the other provides full datetime details.
Evaluate each record to detect any risk conditions (e.g., low visibility combined with high speed or any other patterns indicating potential danger).

For each detected risk event, return the following:
- Timestamp of the event (from the 'Time Stamp' column)
- Risk description (e.g., "Low visibility risk", "High speed in low visibility conditions", etc.)
- Relevant parameters that led to the decision.

Below is the merged CSV data:
{csv_data}
"""

# --- Send Prompt to Gemini API ---

payload = {"prompt": prompt}
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

try:
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        # Extract details from Gemini response.
        # It's expected that the response includes a timestamp, a fault (risk description), and parameters.
        risk_event = {
            'Time': result.get('timestamp', 'N/A'),
            'Event': result.get('fault', 'Visibility Risk'),
            'Details': result.get('parameters', '')
        }

        # Append the risk event to the Gemini response CSV (create it if it doesn't exist)
        if os.path.exists(gemini_response_path):
            df_gemini = pd.read_csv(gemini_response_path)
        else:
            df_gemini = pd.DataFrame(columns=['Time', 'Event', 'Details'])

        df_gemini = df_gemini.append(risk_event, ignore_index=True)
        df_gemini.to_csv(gemini_response_path, index=False)

        print("Gemini response log updated with visibility risk event.")
    else:
        print("Gemini API Error:", response.status_code, response.text)
except Exception as e:
    print("Error connecting to Gemini API:", e)
