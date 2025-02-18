import pandas as pd

# Define file paths
file1_path = "aggregated_roaming_data.csv"  # Main dataset
file2_path = "aggregated_roaming_data_with_vintage.csv"  # Contains Driver Vintage column
output_file_path = "roaming_analysis_with_vintage.csv"

# Load the CSV files into DataFrames
df1 = pd.read_csv(file1_path)  # Main data
df2 = pd.read_csv(file2_path)  # Contains 'Driver Vintage' column

# Keep only necessary columns from df2
df2 = df2[['Adapter-Driver', 'Driver Vintage']]

# Perform a left merge to bring in Driver Vintage where available
merged_df = pd.merge(df1, df2, on="Adapter-Driver", how="left")

# Save the merged DataFrame to a CSV file
merged_df.to_csv(output_file_path, index=False)

print(f"Merged CSV file saved as: {output_file_path}")
