import os
import pandas as pd

# File paths
drowsiness_log_path = '/home/fast-and-furious/main/section_2_test_drive/drowsiness_log.csv'
gemini_response_path = '/home/fast-and-furious/main/section_3_test_drive/gemini_response.csv'

# Read the drowsiness log CSV
df_drowsy = pd.read_csv(drowsiness_log_path)

# The timestamp column in the drowsiness file is "Time (sec)"
time_column = 'Time (sec)'

# Create a boolean mask for rows where Alert is "High drowsiness detected"
high_drowsy = df_drowsy['Alert'] == 'High drowsiness detected'

# Group consecutive rows based on changes in the boolean value
groups = (high_drowsy != high_drowsy.shift()).cumsum()

# Filter for rows with high drowsiness and assign group numbers
df_high = df_drowsy[high_drowsy].copy()
df_high['group'] = groups[high_drowsy]

# Compute the number of consecutive high drowsiness entries for each group
group_counts = df_high.groupby('group').size()

# Identify valid groups where there are at least 10 consecutive high drowsiness entries
valid_groups = group_counts[group_counts >= 10].index

# For each valid group, select the first row as the detection event (avoid counting the same group multiple times)
trigger_entries = df_high[df_high['group'].isin(
    valid_groups)].groupby('group').first()

# Create a new DataFrame for the Gemini response log with the detected drowsiness events
# Here, 'Time' is taken from the "Time (sec)" column, 'Event' is set to "Drowsiness", and 'Details' is left empty.
log_entries = pd.DataFrame({
    'Time': trigger_entries[time_column],
    'Event': 'Drowsiness',
    'Details': ''
})

# Overwrite (or create) the Gemini response CSV with the new log entries
log_entries.to_csv(gemini_response_path, index=False)

print("gemini_response.csv has been recreated with the detected drowsiness events.")
