import pandas as pd
import re  # Import regex module

def calculate_manufacturers(input_file, output_file):
    # Load the CSV file
    df = pd.read_csv(input_file)

    # Identify the column containing manufacturer data
    if "Manufacturer" in df.columns:
        manufacturer_column = "Manufacturer"
    elif "Adapter-Driver" in df.columns:
        manufacturer_column = "Adapter-Driver"
    else:
        raise ValueError("No Manufacturer-related column found in the CSV file.")

    # Extract manufacturer names and remove (R) or ® symbols
    df["Manufacturer"] = df[manufacturer_column].apply(lambda x: re.sub(r'\(R\)|®', '', str(x).split()[0]) if isinstance(x, str) else "Unknown")

    # Count occurrences of each manufacturer
    manufacturer_counts = df["Manufacturer"].value_counts()

    # Convert to percentages
    manufacturer_percentages = (manufacturer_counts / manufacturer_counts.sum()) * 100

    # Create a DataFrame for output
    output_df = pd.DataFrame({
        "Manufacturer": manufacturer_percentages.index,
        "Percentage": manufacturer_percentages.values
    })

    # Save the results to a CSV file
    output_df.to_csv(output_file, index=False)
    print(f"✅ Manufacturers data saved to {manufacturers_output_file}")

def sum_total_sum(input_file, output_file):
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    # Sum the 'Total Sum' column
    total_sum_value = df['Total Sum'].sum()
    
    # Create a new dataframe to store the result
    total_sum_df = pd.DataFrame({'Total Sum': [total_sum_value]})
    
    # Save to CSV
    total_sum_df.to_csv(output_file, index=False)
    print(f"✅ Total samples data successfully saved to: {total_samples_output_file}")

# Define file paths
input_file = "merged_roaming_analysis_with_vintage.csv"
manufacturers_output_file = "manufacturers.csv"
total_samples_output_file = "total_samples.csv"

# Run the functions
calculate_manufacturers(input_file, manufacturers_output_file)
sum_total_sum(input_file, total_samples_output_file)
