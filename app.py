import time
import random
import pandas as pd
import datetime
import re
import warnings
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from fastapi import FastAPI, Query
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth
from bs4 import BeautifulSoup

# Disable pandas warnings
pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore", category=Warning)

app = FastAPI()

# User agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
]

# Setup driver
def setup_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    driver = uc.Chrome(options=options)
    stealth(driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
            webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

# Build search URL
def build_url(car, criteria):
    url = f"https://www.autotrader.co.uk/car-search?make={car['make']}&model={car['model']}&postcode={criteria['postcode'].replace(' ', '+')}&radius={criteria['radius']}&include-delivery-options=on&advertising-location=at_cars&sort=most-recent"
    return url

# Scroll page to load results
def scroll_page(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(10):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

# Extract car details
def extract_car_details(text):
    details = {
        "price": None, "mileage": None, "year": None,
        "transmission": None, "fuel": None, "engine": None, "owners": None
    }
    try:
        price_match = re.search(r"(£|Â£|€)\\s*(\\d{1,3}(,\\d{3})*)", text)
        if price_match:
            details["price"] = price_match.group(2).replace(",", "")
        mileage_match = re.search(r"(\\d{1,3}(,\\d{3})*)\\s*miles", text, re.IGNORECASE)
        if mileage_match:
            details["mileage"] = mileage_match.group(1).replace(",", "")
        year_match = re.search(r"\\b(20\\d{2}|19\\d{2})\\b", text)
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
        engine_match = re.search(r"(\\d\\.\\d)\\s*[Ll]", text)
        if engine_match:
            details["engine"] = engine_match.group(1)
        owners_match = re.search(r"(\\d)\\s+owners?", text, re.IGNORECASE)
        if owners_match:
            details["owners"] = owners_match.group(1)
    except:
        pass
    return details

# Scrape Autotrader
def scrape_autotrader(cars, criteria, driver):
    data = []

    for car in cars:
        url = build_url(car, criteria)
        driver.get(url)

        # ✅ Extra long wait to let headless browser fully load JS
        time.sleep(6)

        # ✅ Aggressive cookie rejection
        try:
            WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
            ).click()
            time.sleep(2)  # Let cookie banner fully close
        except Exception:
            pass  # Ignore if no cookie popup

        # ✅ Stronger scroll
        scroll_page(driver)

        # ✅ Find listings with retry
        listings = driver.find_elements(By.CSS_SELECTOR, "li.search-page__result")

        if not listings:
            # Retry once after waiting
            time.sleep(4)
            listings = driver.find_elements(By.CSS_SELECTOR, "li.search-page__result")

        for listing in listings:
            try:
                title = listing.text
                link = listing.find_element(By.TAG_NAME, "a").get_attribute("href")
                if not link.startswith("http"):
                    link = "https://www.autotrader.co.uk" + link
                details = extract_car_details(title)
                details["link"] = link
                data.append(details)
            except Exception:
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
    df = df.copy()
    if df.empty:
        return None
    df["price"] = pd.to_numeric(df["price"], errors='coerce')
    df.dropna(subset=["price"], inplace=True)
    df["listing_month"] = datetime.datetime.now().strftime("%b %Y")
    plt.figure(figsize=(10,6))
    plt.hist(df["price"], bins=20, color='skyblue')
    plt.xlabel("Price (£)")
    plt.ylabel("Number of Cars")
    plt.title("Car Price Distribution")
    graph_name = f"price_graph_{timestamp}.png"
    plt.savefig(graph_name)
    plt.close()
    return graph_name

# Deduplicate data
def deduplicate_data(df):
    df.drop_duplicates(subset=["price", "mileage", "year", "engine", "link"], inplace=True)
    return df

# Analyze supply snapshot
def analyze_market(df, radius):
    avg_mileage = None
    avg_price = None
    median_price = None
    competition_index = None
    try:
        if "mileage" in df.columns:
            df["mileage"] = pd.to_numeric(df["mileage"], errors="coerce")
            avg_mileage = df["mileage"].mean()
        if "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            avg_price = df["price"].mean()
            median_price = df["price"].median()
        price_spread = (df["price"].max() - df["price"].min()) / median_price * 100 if median_price else None
        market_density = len(df) / (3.1415 * (float(radius)**2)) if radius else None
        turnover_days = 60
        price_factor = min(price_spread or 0, 100) * 0.4
        turnover_factor = (turnover_days/90) * 100 * 0.35
        density_factor = min(market_density*20, 100) * 0.25 if market_density else 35
        competition_index = round(price_factor + turnover_factor + density_factor)
    except:
        pass
    return avg_mileage, avg_price, median_price, competition_index

# Main /scrape endpoint
@app.get("/scrape")
def scrape(
    make: str = Query(...),
    model: str = Query(""),
    postcode: str = Query("BB7 3BB"),
    radius: str = Query("10")
):
    retries = 3
    while retries > 0:
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
            df = deduplicate_data(df)
            graph_file = create_price_graph(df, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
            avg_mileage, avg_price, median_price, competition_index = analyze_market(df, radius)
            elapsed = time.time() - start_time
            return {
                "status": "success",
                "listings_scraped": len(df),
                "average_mileage": avg_mileage,
                "average_price": avg_price,
                "median_price": median_price,
                "competition_index": competition_index,
                "csv_file": filename,
                "graph_file": graph_file,
                "elapsed_seconds": elapsed
            }
        except Exception as e:
            retries -= 1
            if retries == 0:
                return {"status": "error", "message": str(e)}
            time.sleep(5)
