import json
import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Path to ChromeDriver executable
driver_path = "C:/Drivers/chromedriver-win64/chromedriver.exe"

# Set up Chrome options (headless mode)
options = Options()
options.add_argument("--headless")
options.add_argument("--log-level=3")  # Suppress logs

# Start ChromeDriver process
service = Service(driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Open the Intel Wi-Fi drivers page
url = "https://www.intel.com/content/www/us/en/download/19351/intel-wireless-wi-fi-drivers-for-windows-10-and-windows-11.html"
driver.get(url)

# Wait for the page to load
time.sleep(3)

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Find the first driver version in the <select> element
select_element = soup.find("select", {"id": "version-driver-select"})
driver_version_web = "Not Found"
if select_element:
    first_option = select_element.find("option")
    driver_version_web = first_option.get_text(strip=True) if first_option else "Not Found"

# Extract the "Purpose" section dynamically
purpose_text = "Purpose section not found."
additional_text = []
adapter_list_text = []  # Changed from string to list

paragraphs = soup.find_all("p")

for i, p in enumerate(paragraphs):
    if "Purpose" in p.get_text(strip=True):  # Locate the Purpose section
        if i + 1 < len(paragraphs):
            purpose_text = paragraphs[i + 1].get_text(strip=True)  # First paragraph after "Purpose"
        if i + 2 < len(paragraphs):
            additional_text.append(paragraphs[i + 2].get_text(strip=True))  # Second paragraph
        if i + 3 < len(paragraphs):
            additional_text.append(paragraphs[i + 3].get_text(strip=True))  # Third paragraph (if exists)

        # Find all <ul> (lists) that appear after the Purpose section
        next_uls = p.find_all_next("ul")

        for ul in next_uls:
            list_items = ul.find_all("li")
            for li in list_items:
                adapter_list_text.append(li.get_text(strip=True))  # Append each list item correctly

# Close the driver
driver.quit()

# Prepare JSON data
data = {
    "latest_driver_version": driver_version_web,
    "purpose": purpose_text,
    "additional_info": additional_text,
    "supported_adapters": adapter_list_text  # Now correctly stores a list
}

# Truncate "supported_adapters"
supported_adapters_str = "<br>".join(data["supported_adapters"])[:325]


# Flatten the JSON data for HTML & CSV
flattened_data = {
    "latest_driver_version": data["latest_driver_version"],
    "purpose": data["purpose"],
    "additional_info_1": data["additional_info"][0] if len(data["additional_info"]) > 0 else "",
    "additional_info_2": data["additional_info"][1] if len(data["additional_info"]) > 1 else "",
    "supported_adapters": supported_adapters_str  # Truncated version
}

# Convert to DataFrame
df = pd.DataFrame([flattened_data])

# Generate filenames with today's date
date_str = datetime.today().strftime('%Y-%m-%d')
csv_filename = f"intel_driver_info.csv"


# Save to CSV
df.to_csv(csv_filename, index=False, encoding="utf-8")



print(f"✅ Intel driver information successfully saved to - {csv_filename}")
