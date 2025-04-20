import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Load CSV file
input_file_path = "Output/aggregated_roaming_data.csv"
output_file_path = "Output/aggregated_roaming_data_with_vintage.csv"

df = pd.read_csv(input_file_path)

# Check if 'Adapter-Driver' column exists
if "Adapter-Driver" not in df.columns:
    print("❌ Error: 'Adapter-Driver' column not found in CSV.")
    exit()

# Set up Selenium WebDriver options
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--no-sandbox")
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--headless=new")

# Install and launch WebDriver
chrome_driver_path = ChromeDriverManager().install()
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Open Microsoft Catalog
driver.get("https://www.catalog.update.microsoft.com/Home.aspx")

# Wait for page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
print("✅ Page fully loaded.")

# Create a new column for Driver Vintage
df["Driver Vintage"] = "Not Found"

# Loop through each row in the CSV
for index, row in df.iterrows():
    adapter = row["Adapter-Driver"]
    print(f"\n🔍 Searching for: {adapter}")

    try:
        # Locate search box
        search_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='text' and contains(@id, 'searchTextBox')]"))
        )
        search_box.clear()
        driver.execute_script("arguments[0].value = arguments[1];", search_box, adapter)
        search_box.send_keys(Keys.RETURN)

        # Wait for search results
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        print("✅ Search results loaded.")

        # Locate the first row’s "Last Updated" cell
        last_updated_cell = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/div/form[2]/div[3]/table/tbody/tr[1]/td/div/div/div[2]/table/tbody/tr[2]/td[5]"))
        )
        last_updated = last_updated_cell.text.strip()
        print(f"✅ {adapter} - Last Updated: {last_updated}")

        # Store in DataFrame
        df.at[index, "Driver Vintage"] = last_updated

    except Exception as e:
        print(f"❌ Error processing '{adapter}': Not Found")
        print("🔍 Current page source (truncated):")
        print(driver.page_source[:500])
        df.at[index, "Driver Vintage"] = "Not Found"

    
    # Minimum delay between requests
    time.sleep(random.uniform(1.2, 2.5))

# Close WebDriver
driver.quit()

# Save the updated DataFrame to CSV
df.to_csv(output_file_path, index=False)
print(f"\n✅ File saved: {output_file_path}")
