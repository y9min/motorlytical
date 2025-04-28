import time
import random
import pandas as pd
import datetime
import warnings
import re
import os
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# Disable warnings
warnings.filterwarnings("ignore", category=Warning)
pd.options.mode.chained_assignment = None

# Initialize FastAPI
app = FastAPI()

# Setup Chrome Driver
def setup_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36")
    driver = uc.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32", webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

# Build search URL
def build_url(car, criteria):
    return f"https://www.autotrader.co.uk/car-search?make={car['make']}&model={car['model']}&postcode={criteria['postcode'].replace(' ', '+')}&radius={criteria['radius']}&include-delivery-options=on&advertising-location=at_cars&sort=most-recent"

# Scroll page
def scroll_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Extract car details
def extract_car_details(text):
    details = {"price": None, "mileage": None, "year": None, "transmission": None, "fuel": None, "engine": None, "owners": None}
    try:
        price_match = re.search(r"(\d{1,3}(,\d{3})*)", text)
        if price_match:
            details["price"] = price_match.group(1).replace(",", "")
        mileage_match = re.search(r"(\d{1,3}(,\d{3})*) miles", text, re.IGNORECASE)
        if mileage_match:
            details["mileage"] = mileage_match.group(1).replace(",", "")
        year_match = re.search(r"\b(20\d{2}|19\d{2})\b", text)
        if year_match:
            details["year"] = year_match.group(1)
        if "manual" in text.lower():
            details["transmission"] = "Manual"
        elif "automatic" in text.lower():
            details["transmission"] = "Automatic"
        if "diesel" in text.lower():
            details["fuel"] = "Diesel"
        elif "petrol" in text.lower():
            details["fuel"] = "Petrol"
        engine_match = re.search(r"(\d\.\d)\s*[Ll]", text)
        if engine_match:
            details["engine"] = engine_match.group(1)
        owners_match = re.search(r"(\d)\s+owners?", text, re.IGNORECASE)
        if owners_match:
            details["owners"] = owners_match.group(1)
    except:
        pass
    return details

def scrape_autotrader(cars, criteria, driver):
    data = []

    for car in cars:
        url = build_url(car, criteria)
        driver.get(url)

        print(f"Visiting URL: {url}")

        # ✅ Wait longer for page JS to fully load
        time.sleep(8)

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
            ).click()
            print("Rejected cookies.")
            time.sleep(3)
        except Exception:
            print("No cookie popup found.")

        # ✅ Aggressive scroll + wait
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # wait for lazy loading

        # ✅ Save screenshot after scroll
        try:
            driver.save_screenshot("/app/page_debug_scroll.png")
            print("Saved screenshot after scroll.")
        except Exception as e:
            print(f"Failed to save scroll screenshot: {e}")

        # ✅ Try to find listings, retry 3 times
        listings = []
        for attempt in range(3):
            try:
                listings = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='search-listing']")
                if listings:
                    print(f"Found {len(listings)} listings on attempt {attempt+1}!")
                    break  # found!
            except Exception as e:
                print(f"Attempt {attempt+1} failed to find listings: {e}")
            time.sleep(4)  # wait and retry

        # ✅ Fallback selector if still no listings
        if not listings:
            print("Trying fallback selector...")
            try:
                listings = driver.find_elements(By.CSS_SELECTOR, "article[data-testid='search-result']")
                if listings:
                    print(f"Found {len(listings)} listings with fallback selector!")
            except Exception as e:
                print(f"Fallback selector also failed: {e}")

        # ✅ Save final page screenshot
        try:
            driver.save_screenshot("/app/page_debug_final.png")
            print("Saved final page screenshot.")
        except Exception as e:
            print(f"Failed to save final screenshot: {e}")

        if not listings:
            print("No listings found after retries.")

        for listing in listings:
            try:
                text = listing.text
                link = listing.find_element(By.TAG_NAME, "a").get_attribute("href")
                if not link.startswith("http"):
                    link = "https://www.autotrader.co.uk" + link
                details = extract_car_details(text)
                details["link"] = link
                data.append(details)
            except Exception as e:
                print(f"Error extracting listing: {e}")
                continue

    return data

# Save CSV
def save_csv(data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"autotrader_results_{timestamp}.csv"
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename, df

# Create graph
def create_price_graph(df, timestamp):
    if df.empty:
        return None
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df.dropna(subset=["price"], inplace=True)
    plt.figure(figsize=(10,6))
    plt.hist(df["price"], bins=20, color='skyblue')
    plt.xlabel("Price (£)")
    plt.ylabel("Number of Cars")
    plt.title("Car Price Distribution")
    graph_name = f"price_graph_{timestamp}.png"
    plt.savefig(graph_name)
    plt.close()
    return graph_name

# Main /scrape endpoint
@app.get("/scrape")
def scrape(make: str = Query(...), model: str = Query(""), postcode: str = Query("BB7 3BB"), radius: str = Query("10")):
    try:
        start_time = time.time()
        driver = setup_driver()
        cars = [{"make": make, "model": model, "variant": ""}]
        criteria = {"postcode": postcode, "radius": radius}
        data = scrape_autotrader(cars, criteria, driver)
        driver.quit()

        if not data:
            return {"status": "no data found"}

        filename, df = save_csv(data)
        graph_file = create_price_graph(df, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
        elapsed = time.time() - start_time

        return {
            "status": "success",
            "listings_scraped": len(df),
            "csv_file": filename,
            "graph_file": graph_file,
            "elapsed_seconds": elapsed
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Debug screenshot endpoint
@app.get("/debug")
def get_debug_screenshot():
    screenshot_path = "/app/page_debug.png"
    if os.path.exists(screenshot_path):
        return FileResponse(screenshot_path, media_type='image/png', filename="page_debug.png")
    else:
        return {"status": "error", "message": "No screenshot found"}
