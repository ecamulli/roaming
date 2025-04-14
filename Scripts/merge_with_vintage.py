import pandas as pd
import os

# Define file paths
file1_path = "Output/aggregated_roaming_data.csv"  # Main dataset
file2_path = "Output/aggregated_roaming_data_with_vintage.csv"  # Contains Driver Vintage column

# Define output file paths
output_csv_path = "Output/merged_roaming_analysis_with_vintage.csv"
output_json_path = "Output/merged_roaming_analysis_with_vintage.json"
output_data_json_path = "Output/data.json"

# Load the CSV files into DataFrames
df1 = pd.read_csv(file1_path)  # Main data
df2 = pd.read_csv(file2_path)  # Contains 'Driver Vintage' column

# Keep only necessary columns from df2
df2 = df2[['Adapter-Driver', 'Driver Vintage']]

# Convert 'Driver Vintage' to datetime format
df2['Driver Vintage'] = pd.to_datetime(df2['Driver Vintage'], errors='coerce').dt.strftime('%Y-%m-%d')


# Perform a left merge to bring in Driver Vintage where available
merged_df = pd.merge(df1, df2, on="Adapter-Driver", how="left")

# Ensure Adapter and Driver columns are retained during merge
if 'Adapter' in df1.columns and 'Driver' in df1.columns:
    merged_df[['Adapter', 'Driver']] = df1[['Adapter', 'Driver']]

# Save the merged DataFrame to a CSV file
merged_df.to_csv(output_csv_path, index=False)

# Save the merged DataFrame to a JSON file (without index)
merged_df.to_json(output_json_path, orient="records", indent=4)
merged_df.to_json(output_data_json_path, orient="records", indent=4)


print(f"✅ CSV output saved to: {output_csv_path}")
print(f"✅ JSON output saved to: {output_json_path}")
print(f"✅ JSON output saved to: {output_data_json_path}")
