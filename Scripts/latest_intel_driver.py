import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time


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
adapter_list_text = ""

paragraphs = soup.find_all("p")

for i, p in enumerate(paragraphs):
    if "Purpose" in p.get_text(strip=True):  # Locate the Purpose section
        if i + 1 < len(paragraphs):
            purpose_text = paragraphs[i + 1].get_text(strip=True)  # First paragraph after "Purpose"
        if i + 2 < len(paragraphs):
            additional_text.append(paragraphs[i + 2].get_text(strip=True))  # Second paragraph
        if i + 3 < len(paragraphs):
            additional_text.append(paragraphs[i + 3].get_text(strip=True))  # Third paragraph (if exists)

        # Find the first <ul> (list) that appears after the Purpose section
        next_ul = p.find_next("ul")
        if next_ul:
            list_items = next_ul.find_all("li")
            for li in list_items:
                if "23.110.0.5" in li.get_text():  # Ensure we get the correct version's list
                    adapter_list_text = li.get_text(strip=True)
                    break
        break

# Close the driver
driver.quit()

# Prepare JSON data
data = {
    "latest_driver_version": driver_version_web,
    "purpose": purpose_text,
    "additional_info": additional_text,
    "supported_adapters": adapter_list_text
}

# Save to a JSON file
output_file = "intel_driver_info.json"
with open(output_file, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)

print(f"Information saved to {output_file}")

# Print extracted JSON for verification
print(json.dumps(data, indent=4))
