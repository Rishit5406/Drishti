import os
import pandas as pd
import re

# --- Configuration ---

# File paths (adjust if needed)
mq3_data_path = '/mnt/data/mq3_data.csv'
gemini_response_path = '/home/fast-and-furious/main/section_3_test_drive/gemini_response.csv'

# Threshold parameters (adjust based on your sensor calibration)
# Threshold for sudden change (add/drop) in sensor value
THRESHOLD_DIFF = 10.0
# Upper limit for normal sensor value (adjust as needed)
ABNORMAL_UPPER = 160.0
# Lower limit for normal sensor value (adjust as needed)
ABNORMAL_LOWER = 120.0

# --- Helper function to extract numeric sensor value ---


def extract_sensor_value(value_str):
    # Expecting string like "Sensor Value: 142"
    match = re.search(r"(\d+\.?\d*)", value_str)
    if match:
        return float(match.group(1))
    else:
        return None

# --- Helper function to generate anomaly details for a row ---


def get_mq3_anomaly_detail(row):
    details = []
    # Check for sudden change (if diff is computed and not NaN)
    if pd.notnull(row['diff']) and abs(row['diff']) > THRESHOLD_DIFF:
        if row['diff'] > 0:
            details.append("Sudden add in sensor value")
        else:
            details.append("Sudden drop in sensor value")
    # Check for abnormal sensor value
    if row['SensorValue'] > ABNORMAL_UPPER:
        details.append("Abnormal high sensor value")
    if row['SensorValue'] < ABNORMAL_LOWER:
        details.append("Abnormal low sensor value")
    return "; ".join(details)

# --- Main processing ---


# Read the MQ3 data CSV
df_mq3 = pd.read_csv(mq3_data_path)

# Update column names based on the CSV file
# Timestamp column: 'Time Stamp'
# Sensor value column: 'Sensor Value'
timestamp_col = 'Time Stamp'
sensor_value_col = 'Sensor Value'

# Extract numeric sensor values into a new column 'SensorValue'
df_mq3['SensorValue'] = df_mq3[sensor_value_col].apply(extract_sensor_value)

# Calculate the difference between consecutive sensor values
df_mq3['diff'] = df_mq3['SensorValue'].diff()

# Determine if each row is an anomaly based on either sudden change or abnormal behavior
df_mq3['anomaly'] = (
    (df_mq3['diff'].abs() > THRESHOLD_DIFF) |
    (df_mq3['SensorValue'] > ABNORMAL_UPPER) |
    (df_mq3['SensorValue'] < ABNORMAL_LOWER)
)

# Generate details for each row that is an anomaly
df_mq3.loc[df_mq3['anomaly'], 'Details'] = df_mq3[df_mq3['anomaly']].apply(
    get_mq3_anomaly_detail, axis=1)

# Group consecutive anomaly rows so that continuous detections yield one entry only
# Create a grouping key that changes whenever the anomaly flag changes
df_mq3['group'] = (df_mq3['anomaly'] != df_mq3['anomaly'].shift()).cumsum()

# Filter only the rows that are flagged as anomalies
df_anomaly = df_mq3[df_mq3['anomaly']].copy()

# For each continuous anomaly group, select the first row as the representative event
trigger_entries = df_anomaly.groupby('group').first()

# Create a DataFrame for the Gemini log entries using the timestamp and anomaly details
log_entries = pd.DataFrame({
    'Time': trigger_entries[timestamp_col],
    'Event': 'MQ3 Sensor Anomaly',
    'Details': trigger_entries['Details']
}).reset_index(drop=True)

# Append these entries to the Gemini response CSV.
# If the file does not exist, create a new one.
if os.path.exists(gemini_response_path):
    df_gemini = pd.read_csv(gemini_response_path)
else:
    df_gemini = pd.DataFrame(columns=['Time', 'Event', 'Details'])

df_gemini_updated = pd.concat([df_gemini, log_entries], ignore_index=True)
df_gemini_updated.to_csv(gemini_response_path, index=False)

print("Gemini response log updated with MQ3 sensor anomalies.")
