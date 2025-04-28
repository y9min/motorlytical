import time
import random
import pandas as pd
import datetime
import warnings
import re
import os
from bs4 import BeautifulSoup

from fastapi import FastAPI
import undetected_chromedriver.v2 as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Initialize FastAPI
app = FastAPI()

# User agent list
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

# Search criteria (can be updated later to dynamic)
criteria = {
    "postcode": "BB7 3BB",
    "radius": "10",
}
cars = [{"make": "BMW", "model": "", "variant": ""}]

# Disable pandas warnings
pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore", category=Warning)


def setup_driver():
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    options.add_argument("--blink-settings=imagesEnabled=false")
    
    driver = uc.Chrome(options=options)
    stealth(
        driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver


def scrape_autotrader(cars, criteria, driver):
    data = []

    for car in cars:
        base_url = f"https://www.autotrader.co.uk/car-search?make={car['make']}&model={car['model']}&postcode={criteria['postcode'].replace(' ', '+')}&radius={criteria['radius']}&include-delivery-options=on&advertising-location=at_cars&sort=most-recent"

        driver.get(base_url)
        time.sleep(3)

        # Attempt to reject cookies
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-reject-all-handler"))
            ).click()
        except Exception:
            pass

        time.sleep(2)

        listings = driver.find_elements(By.CSS_SELECTOR, "li.search-page__result")

        for listing in listings:
            try:
                title = listing.find_element(By.CSS_SELECTOR, "h3").text
                price = listing.find_element(By.CSS_SELECTOR, ".vehicle-price").text
                link = listing.find_element(By.TAG_NAME, "a").get_attribute("href")
                mileage = None
                year = None

                try:
                    details_text = listing.text
                    mileage_match = re.search(r"(\d{1,3}(,\d{3})*) miles", details_text)
                    if mileage_match:
                        mileage = mileage_match.group(1).replace(",", "")
                    year_match = re.search(r"\b(20\d{2}|19\d{2})\b", details_text)
                    if year_match:
                        year = year_match.group(1)
                except:
                    pass

                data.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "mileage": mileage,
                    "year": year
                })

            except Exception as e:
                print(f"Error extracting a listing: {str(e)}")

    return data


def save_data(data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"autotrader_scrape_{timestamp}.csv"
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    return filename, df


def create_price_trend_graph(df, timestamp):
    if "year" not in df.columns or df.empty:
        return None

    df_filtered = df.dropna(subset=["year"])
    df_filtered["year"] = pd.to_numeric(df_filtered["year"], errors='coerce')
    df_filtered = df_filtered.dropna(subset=["year"])

    if df_filtered.empty:
        return None

    plt.figure(figsize=(10, 6))
    df_filtered["year"].hist(bins=15)
    plt.title("Car Year Distribution")
    plt.xlabel("Year")
    plt.ylabel("Number of Listings")
    plt.grid(True)
    graph_filename = f"year_distribution_{timestamp}.png"
    plt.savefig(graph_filename)
    plt.close()

    return graph_filename


@app.get("/scrape")
def scrape():
    try:
        start_time = time.time()

        driver = setup_driver()
        data = scrape_autotrader(cars, criteria, driver)
        driver.quit()

        if not data:
            return {"status": "no data found"}

        csv_file, df = save_data(data)
        graph_file = create_price_trend_graph(df, datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))

        avg_mileage = None
        if "mileage" in df.columns and not df["mileage"].isnull().all():
            df["mileage"] = pd.to_numeric(df["mileage"], errors='coerce')
            avg_mileage = df["mileage"].mean()

        elapsed_time = time.time() - start_time

        return {
            "status": "success",
            "listings_scraped": len(data),
            "average_mileage": avg_mileage,
            "csv_file": csv_file,
            "graph_file": graph_file,
            "time_seconds": elapsed_time
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
