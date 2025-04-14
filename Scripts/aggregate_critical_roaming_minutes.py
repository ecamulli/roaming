import os
import pandas as pd
import json

# Define input and output directories
input_directory = r"C:/Python Path/Roaming/History"
output_directory = r"C:/Python Path/Roaming"
output_file = os.path.join(output_directory, "aggregated_critical_roaming_minutes.json")

# Initialize total
total_critical_sum = 0

# Loop through files in the input directory
for filename in os.listdir(input_directory):
    if filename.startswith("roaming_data") and filename.endswith(".csv"):
        file_path = os.path.join(input_directory, filename)
        try:
            df = pd.read_csv(file_path)
            if "Critical Sum" in df.columns:
                total_critical_sum += df["Critical Sum"].sum()
            else:
                print(f"'Critical Sum' column not found in {filename}")
        except Exception as e:
            print(f"Error reading {filename}: {e}")

# Convert total minutes into years, days, hours, minutes
minutes_in_year = 365 * 24 * 60
minutes_in_day = 24 * 60

years = total_critical_sum // minutes_in_year
remaining_minutes = total_critical_sum % minutes_in_year

days = remaining_minutes // minutes_in_day
remaining_minutes %= minutes_in_day

hours = remaining_minutes // 60
minutes = remaining_minutes % 60

# Create result dictionary
result_data = {
    "total_minutes": int(total_critical_sum),
    "years": int(years),
    "days": int(days),
    "hours": int(hours),
    "minutes": int(minutes)
}

# Write the result to a JSON file
with open(output_file, 'w') as json_file:
    json.dump(result_data, json_file, indent=4)

# Print result
print(f"Aggregated total critical sum: {total_critical_sum} minutes")
print(f"Converted to: {years} years, {days} days, {hours} hours, {minutes} minutes")
print(f"Result written to {output_file}")
