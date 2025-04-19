import os
import requests
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# Get local system time (your computer's time zone)
now_local = datetime.now()

# Current date and time
today_date = datetime.now().strftime("%Y-%m-%d")
to_timestamp = int(now_local.timestamp() * 1000)

# Get timestamp in milliseconds
from_timestamp = int((now_local - timedelta(days=10).timestamp() * 1000)

# Define your save directory
output_dir = "Output/bad_drivers_per_acct"
os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

# Driver vintage source file
merged_roaming_analysis_file = "Output/merged_roaming_analysis_with_vintage.csv"

# API URLs
ROAMING_URL = f"https://api-v2.7signal.com/kpis/agents/adapter-drivers?from={from_timestamp}&to={to_timestamp}&type=ROAMING&includeClientCount=true"
AUTH_URL = 'https://api-v2.7signal.com/oauth2/token'

# Excel file containing customer details
EXCEL_PATH = "Customer_Data.xlsx"

# Read customer credentials and account names
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
    client_id, client_secret, account_name = client_info
    token = get_auth_token(client_id, client_secret)
    
    if not token:
        return None
    
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(ROAMING_URL, headers=headers, timeout=30)
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
                    "Account Name": account_name,
                    "Adapter": adapter,
                    "Driver": driver,
                    "Adapter-Driver": adapter_driver,
                    "goodSum": type_info.get("goodSum", 0),
                    "criticalSum": type_info.get("criticalSum", 0),
                    "warningSum": type_info.get("warningSum", 0),
                    "clientCount": entry.get("clientCount", 0)
                })
        return pd.DataFrame(data)

    except requests.RequestException:
        return None

# **Use Multi-Threading to Fetch Data Faster**
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(tqdm(executor.map(fetch_customer_data, zip(customers_df['client_id'], customers_df['client_secret'], customers_df['account_name'])), 
                        total=len(customers_df), desc="Fetching Data"))

# Combine customer data into a single DataFrame
data_frames = [df for df in results if df is not None]

if data_frames:
    master_df = pd.concat(data_frames, ignore_index=True)
    
    
    # Group and aggregate data
    master_df = master_df.groupby(['Account Name', 'Adapter', 'Driver', 'Adapter-Driver'], as_index=False).agg({
        'goodSum': 'sum',
        'criticalSum': 'sum',
        'warningSum': 'sum',
        'clientCount': 'sum'
    })

        
    # Strip the first word and dash in 'Adapter' and 'Adapter-Driver'
    master_df['Adapter'] = master_df['Adapter'].str.replace(r'^[^-]*-\s*', '', regex=True)
    master_df['Adapter-Driver'] = master_df['Adapter-Driver'].str.replace(r'^[^-]*-\s*', '', regex=True)

    # Add totalSum column before calculating percentages
    master_df['totalSum'] = master_df[['goodSum', 'criticalSum', 'warningSum']].sum(axis=1)

    # Drop columns
    master_df = master_df.drop(columns=['warningSum', 'goodSum'])

    # Compute "Good Roaming Calculation (%)"
    master_df['Good Roaming Calculation (%)'] = ((1 - (master_df['criticalSum'] / master_df['totalSum'])) * 100).fillna(100).round(1)


    # Ensure "Good Roaming Calculation (%)" exists and is a float
    if 'Good Roaming Calculation (%)' in master_df.columns:
        master_df['Good Roaming Calculation (%)'] = master_df['Good Roaming Calculation (%)'].astype(float)

    # Rename columns
        master_df = master_df.rename(columns={'criticalSum': 'Critical Minutes', 'clientCount': 'Client Count', 'totalSum': 'Total Minutes'})

        
        # Function to ensure filenames are safe
        def sanitize_filename(name):
            return "".join(c if c.isalnum() or c in ('_', '-') else "_" for c in name)

        # Identify poor roamers
        poor_roamers = master_df[master_df['Good Roaming Calculation (%)'] < 99.0].sort_values(by="Good Roaming Calculation (%)", ascending=True)
        
        if not poor_roamers.empty:
            poor_roamers.loc[:, 'Adapter'] = poor_roamers['Adapter'].str.strip().str.lower()

            # Save separate reports for each account
            for account_name in poor_roamers['Account Name'].unique():
                account_data = poor_roamers[poor_roamers['Account Name'] == account_name]

                # Create a sanitized filename with account name and date
                sanitized_name = sanitize_filename(account_name)
                account_csv_filename =  os.path.join(output_dir, f"bad_drivers_for_{sanitized_name}.csv")

                # Save the filtered data to a CSV file
                account_data.to_csv(account_csv_filename, index=False)
                print(f"✅ Report saved: {account_csv_filename}")
