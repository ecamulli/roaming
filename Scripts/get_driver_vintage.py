import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from concurrent.futures import ThreadPoolExecutor

# Load the input CSV file
input_file = "C:/Python Path/Roaming/roaming_analysis_with_vintage.csv"
df = pd.read_csv(input_file)

# Ensure the column exists
if "Adapter-Driver" not in df.columns or "Driver Vintage" not in df.columns:
    raise ValueError("The required columns are missing from the input file.")

# Set up Selenium WebDriver options
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--log-level=3")  # Suppress logs

def process_adapter(adapter):
    """Runs the search for a single adapter-driver using Selenium."""
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    url = "https://www.catalog.update.microsoft.com/Home.aspx"
    driver.get(url)

    try:
        # Wait for the search bar and enter adapter name
        search_box = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='text' and contains(@id, 'searchText')]"))
        )
        search_box.clear()
        search_box.send_keys(adapter)
        search_box.send_keys(Keys.RETURN)

        # Wait for search results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "ctl00_catalogBody_updateMatches"))
        )

        # Extract the first row's "Last Updated" date dynamically
        last_updated = driver.find_element(By.XPATH, "//table[contains(@class, 'results')]/tbody/tr[3]/td[5]").text
    
    except Exception:
        # print(f"{adapter} - Not Found")
        last_updated = "Not Found"

    finally:
        driver.quit()

    return adapter, last_updated

# Filter only rows where "Driver Vintage" is "Not Found" or empty
to_search = df[df["Driver Vintage"].isna() | (df["Driver Vintage"] == "Not Found")]

# Run searches in parallel (up to 3 at a time)
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(process_adapter, to_search["Adapter-Driver"].dropna()))

# Update only the necessary rows
df.loc[to_search.index, "Driver Vintage"] = [r[1] for r in results]

# Save the updated data to a new CSV file
output_file = "merged_roaming_analysis_with_vintage.csv"
df.to_csv(output_file, index=False)

print(f"Process completed. Output saved to {output_file}")
