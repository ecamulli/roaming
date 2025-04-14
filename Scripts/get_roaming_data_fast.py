import os
import requests
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Current date for output file naming
today_date = datetime.now().strftime("%Y-%m-%d")

# Define your save directory
output_dir = r"History"
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

# Define output filename
MASTER_OUTPUT_FILE = "roaming_data"
output_filename = os.path.join(output_dir, f"{MASTER_OUTPUT_FILE}_{today_date}.csv")

# API URLs
ROAMING_URL = 'https://api-v2.7signal.com/kpis/agents/adapter-drivers?type=ROAMING&includeClientCount=true'
AUTH_URL = 'https://api-v2.7signal.com/oauth2/token'

# Excel file containing customer details
EXCEL_PATH = "Customer_Data.xlsx"

# Read customer credentials
customers_df = pd.read_excel(EXCEL_PATH)

# Function to fetch authentication token
def get_auth_token(client_id, client_secret):
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
        response = requests.post(AUTH_URL, data=auth_data, headers=auth_headers, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.RequestException:
        return None

# Function to fetch and process data for a customer
def fetch_customer_data(client_info):
    client_id, client_secret = client_info
    token = get_auth_token(client_id, client_secret)
    
    if not token:
        return None
    
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(ROAMING_URL, headers=headers, timeout=10)
        response.raise_for_status()
        roaming_data = response.json().get('results', [])

        if not roaming_data:
            return None

        # Convert JSON to DataFrame efficiently
        data = []
        for entry in roaming_data:
            adapter = entry.get('driverProvider', 'Unknown')  # Adapter column
            driver = entry.get('driverVersion', 'Unknown')    # Driver column
            adapter_driver = f"{adapter} - {driver}"          # Concatenated Adapter-Driver column
            
    
            for type_info in entry.get("types", []):
                data.append({
                    "Adapter": adapter,
                    "Driver": driver,
                    "Adapter-Driver": adapter_driver,  # Keep the concatenated version
                    "goodSum": type_info.get("goodSum", 0),
                    "criticalSum": type_info.get("criticalSum", 0),
                    "warningSum": type_info.get("warningSum", 0),
                    "clientCount": entry.get("clientCount", 0)
                })
        return pd.DataFrame(data)

    except requests.RequestException:
        return None

# **Use Multi-Threading to Fetch Data Faster**
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(tqdm(executor.map(fetch_customer_data, zip(customers_df['client_id'], customers_df['client_secret'])), 
                        total=len(customers_df), desc="Fetching Data"))

# Combine all customer data into a single DataFrame
data_frames = [df for df in results if df is not None]

if data_frames:
    master_df = pd.concat(data_frames, ignore_index=True)

    # Group and aggregate data
    master_df = master_df.groupby(['Adapter', 'Driver', 'Adapter-Driver'], as_index=False).agg({
        'goodSum': 'sum',
        'criticalSum': 'sum',
        'warningSum': 'sum',
        'clientCount': 'sum'
    })

    
    # Strip the first word and dash in 'Adapter' and 'Adapter-Driver'
    master_df['Adapter'] = master_df['Adapter'].str.replace(r'^[^-]*-\s*', '', regex=True)
    master_df['Adapter-Driver'] = master_df['Adapter-Driver'].str.replace(r'^[^-]*-\s*', '', regex=True)

    # Add totalSum column
    master_df['totalSum'] = master_df[['goodSum', 'criticalSum', 'warningSum']].sum(axis=1)

    # Compute "Good Roaming Calculation (%)"
    master_df['Good Roaming Calculation (%)'] = ((1 - (master_df['criticalSum'] / master_df['totalSum'])) * 100).fillna(100)
    
    # Format to one decimal place with a % sign
    master_df['Good Roaming Calculation (%)'] = master_df['Good Roaming Calculation (%)'].map(lambda x: f"{x:.1f}%")

    # Sort by Good Roaming Calculation before formatting
    master_df.sort_values(by='Good Roaming Calculation (%)', ascending=False, inplace=True)

    # Rename columns
    master_df.rename(columns={
        'goodSum': 'Good Sum',
        'criticalSum': 'Critical Sum',
        'warningSum': 'Warning Sum',
        'clientCount': 'Client Count',
        'totalSum': 'Total Sum'
    }, inplace=True)

    # Save DataFrame to CSV
    master_df.to_csv(output_filename, index=False)
    print(f"✅ Roaming data successfully saved to: {output_filename}")

else:
    print("⚠️ No valid data collected. CSV file was not created.")
