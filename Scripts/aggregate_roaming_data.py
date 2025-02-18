import pandas as pd
import os
import glob

# Specify the folder containing the roaming_data files
folder_path = "C:/Python Path/Roaming/History"  # Change this to your target folder path
output_path = "C:/Python Path/Roaming" #Save aggregated data file here

def combine_and_aggregate_roaming_data(folder_path):
    # Get all CSV files in the folder that start with "roaming_data"
    files = glob.glob(os.path.join(folder_path, "roaming_data*.csv"))

    if not files:
        print("No files starting with 'roaming_data' were found in the specified folder.")
        return

    # Initialize an empty list to store DataFrames
    dataframes = []

    # Read each file and append the DataFrame to the list
    for file in files:
        try:
            df = pd.read_csv(file)
            # Ensure 'Good Roaming Calculation (%)' is cleaned and converted to float
            df['Good Roaming Calculation (%)'] = df['Good Roaming Calculation (%)'].str.replace('%', '').astype(float)
            dataframes.append(df)
            print(f"Loaded: {file}")
        except Exception as e:
            print(f"Error reading {file}: {e}")

    # Combine all DataFrames
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Ensure 'Adapter-Driver' is treated as a string and fill NaN values with an empty string
    combined_df['Adapter-Driver'] = combined_df['Adapter-Driver'].astype(str).fillna('')

    # Remove rows where Adapter-Driver is "N/A" or "iwlwifi" or "NaN"
    combined_df = combined_df[~combined_df['Adapter-Driver'].isin(['N/A', 'nan', 'iwlwifi'])]

    # Remove rows where Adapter-Driver starts with a number
    combined_df = combined_df[~combined_df['Adapter-Driver'].str.match(r'^\d')]

    # Aggregate by 'Adapter-Driver' and sum the numeric columns
    aggregated_df = combined_df.groupby('Adapter-Driver', as_index=False).agg({
        'Good Sum': 'sum',
        'Critical Sum': 'sum',
        'Warning Sum': 'sum',
        'Client Count': 'sum',
        'Total Sum': 'sum'
    })

    # Recalculate 'Good Roaming Calculation (%)'
    aggregated_df['Good Roaming Calculation (%)'] = (aggregated_df['Good Sum'] / aggregated_df['Total Sum']) * 100

    # Format 'Good Roaming Calculation (%)' to show as a percentage
    aggregated_df['Good Roaming Calculation (%)'] = aggregated_df['Good Roaming Calculation (%)'].fillna(0).map(lambda x: f"{x:.1f}%")

    # Ensure 'Good Roaming Calculation (%)' is numeric for sorting
    aggregated_df['Good Roaming Calculation (%)'] = aggregated_df['Good Roaming Calculation (%)'] \
        .str.replace('%', '', regex=False).astype(float)

    # Sort by 'Good Roaming Calculation (%)' in descending order
    aggregated_df.sort_values(by='Good Roaming Calculation (%)', inplace=True)

    # Remove rows where 'Good Roaming Calculation (%)' is 0
    aggregated_df = aggregated_df[aggregated_df['Good Roaming Calculation (%)'] != 0]

    # Remove rows where 'Total Sum' is less than 10,000
    aggregated_df = aggregated_df[aggregated_df['Total Sum'] >= 10000]

    # Format back as percentage strings
    # aggregated_df['Good Roaming Calculation (%)'] = aggregated_df['Good Roaming Calculation (%)'].map(lambda x: f"{x:.2f}%")

    # Output file path
    output_file = os.path.join(output_path, "aggregated_roaming_data.csv")

    # Save the aggregated data to a new CSV file
    aggregated_df.to_csv(output_file, index=False)
    print(f"Aggregated data saved to: {output_file}")

# Run the function
combine_and_aggregate_roaming_data(folder_path)
