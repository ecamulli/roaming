import os
import requests
import pandas as pd
from tqdm import tqdm  # For progress bar
from datetime import datetime
from pandas import json_normalize

# Current date for output file naming
today_date = datetime.now().strftime("%Y-%m-%d")

# Define your save directory
output_dir = r"C:/Python Path/Roaming/History"  # Use raw string (r"") to avoid escape character issues

# Ensure the directory exists
os.makedirs(output_dir, exist_ok=True)  # This won't create anything if the folder already exists

# Define base filename
MASTER_OUTPUT_FILE = "roaming_data"
output_filename = os.path.join(output_dir, f"{MASTER_OUTPUT_FILE}_{today_date}.csv")

# API URLs
ROAMING_URL = 'https://api-v2.7signal.com/kpis/agents/adapter-drivers?type=ROAMING&includeClientCount=true'
#ROAMING_URL = 'https://api-v2.7signal.com/kpis/agents/adapter-drivers?from=1739545200000&to=1739804400000&type=ROAMING&band=5&includeClientCount=true'
AUTH_URL = 'https://api-v2.7signal.com/oauth2/token'

# Excel file containing customer details
EXCEL_PATH = "C:/Python Path/Customer_Data.xlsx"

# Read the customer details from the spreadsheet
customers_df = pd.read_excel(EXCEL_PATH)

# Function to fetch and process data for each customer
def fetch_customer_data(client_id, client_secret):
    auth_data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }

    auth_headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        # Get authentication token
        token_response = requests.post(AUTH_URL, data=auth_data, headers=auth_headers, timeout=10)
        token_response.raise_for_status()
        token = token_response.json().get("access_token")

        if not token:
            print(f"No access token received for client_id: {client_id}")
            return pd.DataFrame()

        # Set up headers for API requests
        headers_eyes = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}"
        }

        # Fetch roaming data
        response = requests.get(ROAMING_URL, headers=headers_eyes, timeout=10)
        response.raise_for_status()

        # Process and flatten the response data
        roaming_data = response.json()
        df = json_normalize(roaming_data['results'], 'types', ['driverProvider', 'driverVersion', 'clientCount'])

        if 'driverProvider' in df.columns and 'driverVersion' in df.columns:
            df['driver_info'] = df['driverProvider'] + ' - ' + df['driverVersion']
            df.drop(['driverProvider', 'driverVersion'], axis=1, inplace=True)
        else:
            return pd.DataFrame()

        return df

    except requests.RequestException as e:
        # print(f"❌ Error fetching data for client_id: {client_id} - {e}")
        return pd.DataFrame()

# Main loop to process all customers
data_list = []

for client_id, client_secret in tqdm(
    zip(customers_df['client_id'], customers_df['client_secret']),
    total=len(customers_df),
    desc="Processing Customers"
):
    customer_data = fetch_customer_data(client_id, client_secret)
    if not customer_data.empty:
        data_list.append(customer_data)

# Combine all collected customer data into a single DataFrame and group by driver_info
if data_list:
    master_df = pd.concat(data_list, ignore_index=True)

    # Group by driver_info and aggregate sums
    master_df = master_df.groupby('driver_info', as_index=False).agg({
        'goodSum': 'sum',
        'criticalSum': 'sum',
        'warningSum': 'sum',
        'clientCount': 'sum'
    })

    # Add totalSum column (sum of goodSum, criticalSum, and warningSum)
    master_df['totalSum'] = master_df['goodSum'] + master_df['criticalSum'] + master_df['warningSum']

    # Add calculation column based on the formula: (1 - (criticalSum / totalSum)) * 100
    master_df['calculation'] = master_df.apply(
        lambda row: (1 - (row['criticalSum'] / row['totalSum'])) * 100 if row['totalSum'] != 0 else 100,
        axis=1
    )

    # Sort the DataFrame by calculation in descending order (before formatting)
    master_df.sort_values(by='calculation', ascending=False, inplace=True)

    # Format the calculation column to one decimal place and append a % sign
    master_df['calculation'] = master_df['calculation'].apply(lambda x: f"{x:.1f}%")

    # Rename columns
    master_df.rename(columns={
        'driver_info': 'Adapter-Driver',
        'goodSum': 'Good Sum',
        'criticalSum': 'Critical Sum',
        'warningSum': 'Warning Sum',
        'clientCount': 'Client Count',
        'totalSum': 'Total Sum',
        'calculation': 'Good Roaming Calculation (%)'
    }, inplace=True)

    # Strip characters up to and including the first dash and space in the 'Adapter-Driver' column
    master_df['Adapter-Driver'] = master_df['Adapter-Driver'].str.replace(r'^.*?-\s', '', regex=True)

    # Save DataFrame to CSV
    try:
        master_df.to_csv(output_filename, index=False)
        print(f"✅ Data successfully saved to: {output_filename}")
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
else:
    print("⚠️ No valid data collected. CSV file was not created.")
