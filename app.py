import os
from statistics import variance
import time
import datetime
import re
import warnings
import pandas as pd
import random
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium_stealth import stealth

pd.options.mode.chained_assignment = None  # default='warn'
warnings.filterwarnings("ignore", category=Warning)

# User agent list
user_agents = [
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
 "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
]

# Define search criteria

criteria = {
 "postcode": "BB7 3BB",
 "radius": "10",
 "year_from": "",
 "year_to": "",
 "price_from": "",
 "price_to": "",
 "mileage_from": "",
 "mileage_to": "",
 "gearbox": "",  # e.g. "Manual", "Automatic"
 "body_type": "",  # e.g. "Hatchback", "Saloon"
 "colour": "",  # e.g. "Blue", "Red"
 "doors": "",  # e.g. "5", "3"
 "seats": "",  # e.g. "5", "2"
 "fuel_type": "",  # e.g. "Petrol", "Diesel", "Electric"
 "battery_range": "",  # For electric vehicles
 "charging_time": "",  # For electric vehicles
 "engine_size_from": "",  # e.g. "1.0"
 "engine_size_to": "",  # e.g. "1.8"
 "drive_type": "",  # e.g. "Front Wheel Drive", "Four Wheel Drive"
 "seller_type": "",  # e.g. "trade", "private"
 "exclude_writeoff": False,  # Set to True to exclude written-off vehicles
 "only_writeoff": False,
 "only_n_ireland": False,  # Set to True to only show vehicles for N. Ireland
}

# Define the car make and model to search for
cars = [{"make": "BMW", "model": "", "variant": ""}]

def scrape_autotrader(cars, criteria):  
 chrome_options = Options()
 chrome_options.add_argument("--disable-notifications")
 chrome_options.add_argument("--start-maximized")
 chrome_options.add_argument("--headless")  # Comment out to see what's happening
 chrome_options.add_argument("--disable-blink-features=AutomationControlled")
 chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")
 chrome_options.add_argument("--blink-settings=imagesEnabled=false")
 driver = webdriver.Chrome(options=chrome_options)
 stealth(
     driver,
     languages=["en-US", "en"],
     vendor="Google Inc.",
     platform="Win32",
     webgl_vendor="Intel Inc.",
     renderer="Intel Iris OpenGL Engine",
     fix_hairline=True,
 )
 data = []
 try:
     for car in cars:
         # Fix URL encoding for postcode with space
         postcode = criteria["postcode"].replace(" ", "+")

         # Change this section in the scrape_autotrader function
         url = f"https://www.autotrader.co.uk/car-search?make={car['make']}&model={car['model']}"

         # Add variant/trim if specified
         if car.get("variant") and car["variant"].strip():
             url += f"&aggregatedTrim={car['variant'].replace(' ', '%20')}"

         if criteria.get("postcode"):
             url += f"&postcode={criteria['postcode'].replace(' ', '+')}"

         if criteria.get("radius"):
             url += f"&radius={criteria['radius']}"

         if criteria.get("price_from"):
             url += f"&price-from={criteria['price_from']}"

         if criteria.get("price_to"):
             url += f"&price-to={criteria['price_to']}"

         if criteria.get("year_from"):
             url += f"&year-from={criteria['year_from']}"

         if criteria.get("year_to"):
             url += f"&year-to={criteria['year_to']}"

         if criteria.get("mileage_from"):
             url += f"&minimum-mileage={criteria['mileage_from']}"

         if criteria.get("mileage_to"):
             url += f"&maximum-mileage={criteria['mileage_to']}"

         if criteria.get("gearbox"):
             url += f"&transmission={criteria['gearbox'].replace(' ', '%20')}"

         if criteria.get("body_type"):
             url += f"&body-type={criteria['body_type'].replace(' ', '%20')}"

         if criteria.get("colour"):
             url += f"&colour={criteria['colour'].replace(' ', '%20')}"

         if criteria.get("doors"):
             url += f"&quantity-of-doors={criteria['doors']}"

         if criteria.get("seats"):
             url += f"&seats_values={criteria['seats']}"

         if criteria.get("fuel_type"):
             url += f"&fuel-type={criteria['fuel_type'].replace(' ', '%20')}"

         if criteria.get("battery_range"):
             url += f"&battery-range={criteria['battery_range']}"

         if criteria.get("charging_time"):
             url += f"&charging-time={criteria['charging_time']}"

         if criteria.get("engine_size_from"):
             url += f"&minimum-badge-engine-size={criteria['engine_size_from']}"

         if criteria.get("engine_size_to"):
             url += f"&maximum-badge-engine-size={criteria['engine_size_to']}"

         if criteria.get("drive_type"):
             url += f"&drivetrain={criteria['drive_type'].replace(' ', '%20')}"

         if criteria.get("seller_type"):
             url += f"&seller-type={criteria['seller_type'].replace(' ', '%20')}"

         if criteria.get("exclude_writeoff") == True:
             url += f"&exclude-writeoff-categories=on"

         elif criteria.get("only_writeoff") == True:
             url += f"&only-writeoff-categories=on"

         if criteria.get("only_n_ireland") == True:
             url += f"&ni-only=on"

         url += "&include-delivery-options=on&advertising-location=at_cars"
         url += "&sort=most-recent"

         driver.get(url)
         st.write(f"Searching for {car['make']} {car['model']}...")
         st.write(f"URL: {url}")

         # Wait for page to load with longer initial timeout
         time.sleep(5)

         # Replace your cookie handling code with this more comprehensive approach:
         try:
             st.write("Looking for cookie consent buttons...")
             # Initialize reject_button
             reject_button = None
             # Try multiple approaches to find and click reject buttons
             for selector in [
                 "button#onetrust-reject-all-handler",
                 "button[aria-label='Reject all']",
                 "button.reject-optional",
                 "button.cookie-consent__button--secondary",
                 "button[data-testid='cookie-consent-reject-all']",
             ]:
                 try:
                     reject_button = WebDriverWait(driver, 2).until(
                         EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                     )
                     if reject_button:
                         st.write(f"Found reject button with selector: {selector}")
                         reject_button.click()
                         time.sleep(1)
                         break
                 except:
                     continue

             # If direct button approach failed, try iframe approach
             if not reject_button:
                 st.write("Looking for cookie consent iframe...")
                 iframes = driver.find_elements(By.TAG_NAME, "iframe")
                 for iframe in iframes:
                     try:
                         if (
                             iframe.get_attribute("title")
                             and "consent" in iframe.get_attribute("title").lower()
                         ):
                             driver.switch_to.frame(iframe)
                             st.write(
                                 "Found cookie iframe, looking for Reject button..."
                             )

                             for button_text in [
                                 "Reject All",
                                 "Reject",
                                 "Decline",
                                 "No",
                             ]:
                                 try:
                                     reject_button = WebDriverWait(driver, 2).until(
                                         EC.element_to_be_clickable(
                                             (
                                                 By.XPATH,
                                                 f"//button[contains(text(), '{button_text}')]",
                                             )
                                         )
                                     )
                                     if reject_button:
                                         st.write(f"Found '{button_text}' button")
                                         reject_button.click()
                                         break
                                 except:
                                     continue


                             driver.switch_to.default_content()
                             time.sleep(1)
                             break
                     except:
                         continue


         except Exception as e:
             st.write(f"Cookie handling: {str(e)}")
             driver.switch_to.default_content()


         # Wait longer for page to fully load after cookie handling
         time.sleep(3)


         # Check if we have "No results found" message
         page_text = driver.find_element(By.TAG_NAME, "body").text
         no_results_phrases = [
             "No results found",
             "No cars found",
             "No exact matches",
             "There are no",
         ]
         no_results = False


         for phrase in no_results_phrases:
             if phrase in page_text:
                 st.write(f"No results detected: '{phrase}'")
                 no_results = True
                 break


         if no_results:
             continue


         st.write("Scrolling to load all listings...")
         # Scroll more gradually to ensure all content loads
         last_height = driver.execute_script("return document.body.scrollHeight")
         for _ in range(10):  # More scroll attempts
             # Scroll down to bottom
             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
             # Wait to load page
             time.sleep(2)
             # Calculate new scroll height and compare with last scroll height
             new_height = driver.execute_script("return document.body.scrollHeight")
             if new_height == last_height:
                 # Try one more small scroll to trigger any remaining lazy loading
                 driver.execute_script("window.scrollBy(0, 300);")
                 time.sleep(1)
                 break
             last_height = new_height


         # Refresh content after scrolling
         time.sleep(2)


         # Try a more comprehensive approach to find listings
         st.write("Searching for car listings...")
         try:
             # First try class-based selectors
             for selector in [
                 "div.search-page__result",
                 "div.advert",
                 "div.listing",
                 "article.advert",
                 "div.vehicle-card",
                 "div.result-card",
                 "div.search-result",
                 "div[data-testid='search-result']",
                 "div[data-testid='advert']",
                 "div[data-testid='listing']",
             ]:


                 found_listings = driver.find_elements(By.CSS_SELECTOR, selector)
                 if found_listings and len(found_listings) > 5:
                     st.write(
                         f"Found {len(found_listings)} listings with selector: {selector}"
                     )
                     break


             # If that didn't work, try XPath
             if not found_listings or len(found_listings) < 5:
                 for xpath in [
                     "//div[.//a[contains(@href, '/car-details/')]]",
                     "//div[.//span[contains(text(), 'Â£')] and .//span[contains(text(), 'miles')]]",
                     "//div[contains(@class, 'search') and .//a[contains(@href, '/car-details/')]]",
                 ]:


                     found_listings = driver.find_elements(By.XPATH, xpath)
                     if found_listings and len(found_listings) > 5:
                         st.write(
                             f"Found {len(found_listings)} listings with XPath: {xpath}"
                         )
                         break


             # If we still don't have enough listings, try a more generic approach
             if not found_listings or len(found_listings) < 5:
                 st.write(
                     "Few listings found with specific selectors, trying generic approach..."
                 )
                 found_listings = driver.find_elements(
                     By.XPATH, "//div[.//a and .//span]"
                 )
                 st.write(
                     f"Found {len(found_listings)} potential listings with generic approach"
                 )

                 # Filter to keep only elements that look like car listings
                 valid_listings = []
                 for elem in found_listings:
                     try:
                         elem_text = elem.text
                         if (
                             len(elem_text) > 50
                             and ("Â£" in elem_text or "Â£" in elem_text)
                             and (car["make"].lower() in elem_text.lower())
                         ):
                             valid_listings.append(elem)
                     except:
                         continue


                 if valid_listings:
                     st.write(f"Filtered to {len(valid_listings)} valid car listings")
                     found_listings = valid_listings

         except Exception as e:
             st.write(f"Error finding listings: {str(e)}")

             # If specific selectors didn't work, try XPath for more dynamic approach
             if not found_listings:
                 for xpath in [
                     "//div[.//span[contains(text(), 'Ãƒâ€šÃ‚Â£')] and .//span[contains(text(), 'miles')]]",
                     "//div[.//a[contains(@href, '/car-details/')]]",
                     "//article[.//span[contains(text(), 'Ãƒâ€šÃ‚Â£')]]",
                 ]:
                     elements = driver.find_elements(By.XPATH, xpath)
                     if elements and len(elements) > 1:
                         found_listings = elements
                         st.write(f"Found {len(elements)} listings with XPath: {xpath}")
                         break
         except Exception as e:
             st.write(f"Selector error: {str(e)}")

         # Second approach: Look for price elements and navigate to parent containers
         if not found_listings:
             st.write("Standard selectors failed. Using pattern analysis...")
             try:
                 soup = BeautifulSoup(driver.page_source, "html.parser")


                 # Use Beautiful Soup to find elements with price text
                 price_elements = soup.find_all(text=lambda t: "Ãƒâ€šÃ‚Â£" in t)


                 if price_elements:
                     st.write(f"Found {len(price_elements)} price elements")


                     # Find parent divs containing both price and typical car listing information
                     potential_listings = set()


                     # Find parent elements with car listing characteristics
                     for element in price_elements:
                         # Walk up the DOM tree looking for container elements
                         current = element.parent
                         for _ in range(5):  # Check up to 5 levels up
                             if current.name in ["div", "article", "li", "section"]:
                                 # Get text of this container
                                 container_text = current.get_text().lower()


                                 # Check for car listing indicators
                                 if (
                                     "miles" in container_text
                                     or "mi" in container_text
                                 ) and any(
                                     str(y) in container_text
                                     for y in range(2000, 2016)
                                 ):
                                     potential_listings.add(current)
                                     break

                             # Move up to parent
                             if current.parent:
                                 current = current.parent
                             else:
                                 break


                     if potential_listings:
                         st.write(
                             f"Found {len(potential_listings)} potential listings via HTML analysis"
                         )

                         # Now we need to convert BS4 elements to Selenium elements
                         # Get class names or other identifiers from BS4 elements
                         listing_patterns = []
                         for item in potential_listings:
                             if item.get("class"):
                                 class_str = ".".join(item.get("class"))
                                 listing_patterns.append(f".{class_str}")
                             elif item.get("id"):
                                 listing_patterns.append(f"#{item.get('id')}")


                         # Use the patterns to find elements with Selenium
                         if listing_patterns:
                             for pattern in listing_patterns:
                                 try:
                                     elements = driver.find_elements(
                                         By.CSS_SELECTOR, pattern
                                     )
                                     if elements and len(elements) > 1:
                                         st.write(
                                             f"Found {len(elements)} listings with pattern: {pattern}"
                                         )
                                         found_listings = elements
                                         break
                                 except:
                                     continue
             except Exception as e:
                 st.write(f"Pattern analysis error: {str(e)}")


         # Third approach: Find all elements containing car details using XPath
         if not found_listings:
             st.write("Trying direct XPath approach...")
             try:
                 # Look for elements with both price and mileage information
                 complex_xpath = "//div[.//text()[contains(., 'Ãƒâ€šÃ‚Â£')] and .//text()[contains(., 'mile')]]"
                 elements = driver.find_elements(By.XPATH, complex_xpath)


                 if elements:
                     st.write(
                         f"Found {len(elements)} potential listings with complex XPath"
                     )
                     # Filter to keep only reasonably sized elements
                     valid_listings = []
                     for elem in elements:
                         # Get element text and check if it contains key car info
                         text = elem.text.lower()
                         if len(text) > 50 and any(
                             str(y) in text for y in range(2000, 2016)
                         ):
                             valid_listings.append(elem)

                     if valid_listings:
                         st.write(
                             f"Found {len(valid_listings)} valid listings after filtering"
                         )
                         found_listings = valid_listings
             except Exception as e:
                 st.write(f"XPath approach error: {str(e)}")

         # Add this after your existing extraction attempts if they fail
         if not found_listings:
             st.write("Attempting direct HTML extraction...")
             html = driver.page_source
             soup = BeautifulSoup(html, "html.parser")

             # Look for common patterns in car listings
             car_listings = []

             # Look for price elements
             price_elements = soup.find_all(string=lambda s: s and "Ã‚Â£" in s)
             for price_elem in price_elements:
                 # Find parent container that might be a car listing
                 parent = price_elem.parent
                 for _ in range(5):  # Look up to 5 levels up
                     if parent and parent.name in ["div", "article", "li"]:
                         text = parent.get_text()
                         # Check if this looks like a car listing
                         if (
                             make.lower() in text.lower()  # type: ignore
                             and model.lower() in text.lower()  # type: ignore
                             and (
                                 "mile" in text.lower()
                                 or any(str(y) in text for y in range(2010, 2026))
                             )
                         ):
                             car_listings.append(parent)
                             break

                         if parent:
                             parent = parent.parent
                         else:
                             break

             st.write(
                 f"Found {len(car_listings)} potential listings via direct HTML extraction"
             )

             # Process these listings
             for listing in car_listings:
                 text = listing.get_text()
                 details = extract_car_details(
                     text, car["make"], car["model"]
                 )


                 # Try to find a link
                 links = listing.find_all("a")
                 for link in links:
                     href = link.get("href")
                     if href and ("/car-details/" in href or "/vehicle/" in href):
                         if not href.startswith("http"):
                             href = "https://www.autotrader.co.uk" + href
                             details["link"] = href
                             break


                 if details["price"] and details["price"] != "Ã‚Â£0":
                     data.append(details)

         if not found_listings:
             st.write(
                 "Unable to identify listing elements. Extracting all possible car details..."
             )
             # Create a last-resort extraction approach
             try:
                 # Extract all prices from the page
                 price_elements = driver.find_elements(
                     By.XPATH, "//*[contains(text(), 'Ãƒâ€šÃ‚Â£')]"
                 )

                 if price_elements:
                     st.write(
                         f"Found {len(price_elements)} price elements, attempting direct extraction"
                     )

                     # Extract prices and associated info
                     for i, price_elem in enumerate(
                         price_elements[:20]
                     ):  # Limit to first 20
                         try:
                             price_text = price_elem.text.strip()


                             # Skip if not a simple price format
                             if (
                                 "month" in price_text.lower()
                                 or len(price_text) > 15
                             ):
                                 continue


                             # Get parent container
                             container = price_elem
                             for _ in range(3):
                                 try:
                                     container = container.find_element(
                                         By.XPATH, "./.."
                                     )
                                 except:
                                     break

                             # Get container text
                             container_text = container.text

                             # Only process if container has price and other car info
                             if "Ãƒâ€šÃ‚Â£" in container_text and (
                                 "mile" in container_text.lower()
                                 or any(
                                     str(y) in container_text
                                     for y in range(2000, 2016)
                                 )
                             ):

                                 car_details = extract_car_details(
                                     container_text, car["make"], car["model"]
                                 )

                                 # Try to extract link
                                 try:
                                     links = container.find_elements(
                                         By.TAG_NAME, "a"
                                     )
                                     for link in links:
                                         href = link.get_attribute("href")
                                         if href and (
                                             "/car-details/" in href
                                             or "/vehicle/" in href
                                         ):
                                             car_details["link"] = href
                                             break
                                 except:
                                     pass

                                 if (
                                     car_details.get("price")
                                     and car_details["price"] != "Ãƒâ€šÃ‚Â£0"
                                 ):
                                     data.append(car_details)
                                     st.write(
                                         f"Extracted car details for listing {i+1}: {car_details['price']}"
                                     )
                         except Exception as e:
                             st.write(f"Error processing price element {i+1}: {str(e)}")

                     if data:
                         st.write(
                             f"Extracted {len(data)} car listings via direct extraction"
                         )
                         # Skip the rest of the processing
                         continue
             except Exception as e:
                 st.write(f"Direct extraction error: {str(e)}")

             st.write("No listing elements found. Saving page for inspection.")
             with open("autotrader_page.html", "w", encoding="utf-8") as f:
                 f.write(driver.page_source)
             continue

         # Process found listings
         st.write(f"Processing {len(found_listings)} car listings...")

         for i, listing in enumerate(found_listings):
             try:
                 # Initialize text to avoid undefined variable errors
                 text = ""

                 # Get the HTML content of the listing
                 try:
                     listing_html = listing.get_attribute("outerHTML")
                 except:
                     st.write(f"Could not get HTML for listing {i+1}, skipping")
                     continue

                 # Try to get text content
                 try:
                     text = listing.text
                     if not text or text.strip() == "":
                         # If direct text extraction fails, try to get text from child elements
                         st.write(
                             f"Listing {i+1} has no direct text, trying child elements..."
                         )

                         # Try to get text from child elements
                         elements = listing.find_elements(By.XPATH, ".//*")
                         texts = [
                             elem.text
                             for elem in elements
                             if elem.text and elem.text.strip()
                         ]
                         if texts:
                             text = " ".join(texts)
                             st.write(
                                 f"Extracted {len(text)} characters from child elements"
                             )
                         else:
                             # If still no text, try to parse the HTML with BeautifulSoup
                             st.write(f"Trying BeautifulSoup for listing {i+1}...")
                             soup = BeautifulSoup(listing_html, "html.parser")
                             text = soup.get_text(separator=" ", strip=True)

                             if not text or text.strip() == "":
                                 st.write(
                                     f"Listing {i+1} has no extractable text content, skipping"
                                 )
                             continue

                 except Exception as e:
                     st.write(f"Error extracting text from listing {i+1}: {str(e)}")
                     continue

                 st.write(f"Processing listing {i+1}, text length: {len(text)}")

                 # Extract car details
                 try:
                     details = extract_car_details(
                         text, car["make"], car["model"]
                     )

                     # Make sure details is not None
                     if details is None:
                         details = {
                             "name": f"{car['make']} {car['model']}",
                             "price": None,
                             "year": None,
                             "mileage": None,
                             "transmission": None,
                             "fuel": None,
                             "engine": None,
                             "owners": None,
                             "link": None,
                         }
                  
                 except Exception as e:
                     st.write(f"Error extracting details from listing {i+1}: {str(e)}")
                     continue

                 # Extract link
                 try:
                     link_element = listing.find_element(By.TAG_NAME, "a")
                     link = link_element.get_attribute("href")
                     if link and ("/car-details/" in link or "/vehicle/" in link):
                         details["link"] = link
                 except:
                     try:
                         # Try to find any link in the listing
                         links = listing.find_elements(By.TAG_NAME, "a")
                         for link_element in links:
                             link = link_element.get_attribute("href")
                             if link and (
                                 "/car-details/" in link or "/vehicle/" in link
                             ):
                                 details["link"] = link
                                 break
                     except:
                         pass

                 # Only add listings with non-zero price
                 if details["price"] and details["price"] != "Ãƒâ€šÃ‚Â£0":
                     data.append(details)
                     st.write(
                         f"Processed listing {i+1}: {details['year']} {car['make']} {car['model']} - {details['price']}"
                     )
                 else:
                     st.write(f"Listing {i+1} has no valid price, skipping")
             except Exception as e:
                 st.write(f"Error processing listing {i+1}: {str(e)}")

         st.write("-" * 40)
         st.write(f"Completed search for {car['make']} {car['model']}, found {len(data)} listings")

         # Calculate average mileage directly from original extracted data
         valid_mileages = []
         for item in data:
             if item.get('mileage') and item.get('mileage') not in ['None', 'nan', '']:
                 try:
                     # Remove commas and convert to float
                     mileage_value = float(str(item.get('mileage')).replace(',', ''))
                     valid_mileages.append(mileage_value)
                 except (ValueError, TypeError):
                     pass

         if valid_mileages:
             avg_mileage = sum(valid_mileages) / len(valid_mileages)
             st.write("-" * 40)
             st.write(f"🛣️  Average Mileage: {avg_mileage:.0f} (from {len(valid_mileages)} listings)")
         else:
             st.write("-" * 40)
             st.write("No valid mileage data to calculate average")

         # Sleep between searches to avoid rate limiting
         time.sleep(2)

     # Remove duplicate entries
     if data:
         st.write(f"Processing {len(data)} raw listings to remove duplicates...")

         # Create a function to generate a unique identifier for each listing
         def generate_listing_key(listing):
             # Use a combination of fields to identify unique listings
             key_parts = [
                 str(listing.get("year", "")),
                 str(listing.get("price", "")),
                 str(listing.get("mileage", "")),
                 str(listing.get("engine", "")),
             ]
             return "|".join(key_parts)

         # Filter out duplicates by using a dictionary with the unique key
         unique_listings = {}
         for listing in data:
             key = generate_listing_key(listing)
             # Extract car ID from link if available for even better deduplication
             if listing.get("link"):
                 car_id_match = re.search(r"/car-details/(\d+)", listing["link"])
                 if car_id_match:
                     key = car_id_match.group(1)


             # Only add if we haven't seen this key before
             unique_listings[key] = listing


         # Convert back to list
         deduplicated_data = list(unique_listings.values())
        
         # Create DataFrame with explicit dtypes
         df = pd.DataFrame(deduplicated_data)


         # st.write raw data for debugging
         st.write("\nDEBUG - DataFrame before processing:")
         st.write(df[["year", "mileage", "price"]].head())


         # Ensure mileage is stored as string first to prevent NaN conversion
         df["mileage"] = df["mileage"].astype(str)
         df["mileage"] = df["mileage"].replace("None", "")
         df["mileage"] = df["mileage"].replace("nan", "")


         # Convert mileage strings to numeric values
         df["mileage_numeric"] = df["mileage"].str.replace(",", "").astype(float, errors='ignore')


         # Convert mileage to numeric for calculations
         df.loc[df["mileage_numeric"].notna(), "mileage"] = df["mileage_numeric"].astype(str)


         # Handle year column - preserve string representation
         df["year"] = df["year"].astype(str)
         df["year"] = df["year"].replace("None", "")
         df["year"] = df["year"].replace("nan", "")


         # st.write processed data
         st.write("\nDEBUG - DataFrame after processing:")
         st.write(df[["year", "mileage", "mileage_numeric", "price"]].head())


         # Convert year to numeric for calculations, but keep original string version
         df["year_numeric"] = pd.to_numeric(df["year"], errors="coerce")
         # Use year_numeric for any calculations, but keep year as string for display


         # Convert year column to appropriate type
         df["year"] = df["year"].apply(
             lambda y: (
                 int(y)
                 if isinstance(y, (int, float)) and not pd.isna(y) and str(y) != "Brand New"
                 else y
             )
         )


         # Convert mileage to string to ensure it's not lost
         df["mileage"] = df["mileage"].astype(str)
         df["mileage"] = df["mileage"].replace("None", "")
         df["mileage"] = df["mileage"].replace("nan", "")


         st.write(f"Removed {len(data) - len(deduplicated_data)} duplicate listings")
         st.write(f"Final count: {len(deduplicated_data)} unique listings")
         st.write("-" * 40)


         # Save results to CSV
         df = pd.DataFrame(deduplicated_data)


         # Filter out entries without a link (these are likely partial duplicates)
         df = df[df["link"].notna() & (df["link"] != "")]


         # Filter out "YOU_MAY_ALSO_LIKE" entries
         df = df[~df["link"].str.contains("YOU_MAY_ALSO_LIKE", case=False, na=False)]


         st.write(
             f"Filtered out {len(deduplicated_data) - len(df)} YOU_MAY_ALSO_LIKE entries"
         )
         st.write(
             f"Filtered out {len(deduplicated_data) - len(df)} entries with no link"
         )








         # Extract listing date from URL
         def extract_date(url):
             if not isinstance(url, str):
                 return None
             match = re.search(r"/car-details/(\d{8})", url)
             if match:
                 date_str = match.group(1)
                 return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
             return None


         df["date_listed"] = df["link"].apply(extract_date)


         # Split date_listed into day, month, year columns
         def extract_day(date_str):
             if not date_str:
                 return None
             try:
                 return date_str.split("/")[0]
             except:
                 return None


         def extract_month(date_str):
             if not date_str:
                 return None
             try:
                 return date_str.split("/")[1]
             except:
                 return None








         def extract_year(date_str):
             if not date_str:
                 return None
             try:
                 return date_str.split("/")[2]
             except:
                 return None


         # Create new columns
         df["day_listed"] = df["date_listed"].apply(extract_day)
         df["month_listed"] = df["date_listed"].apply(extract_month)
         df["year_listed"] = df["date_listed"].apply(extract_year)


         # Calculate days since listing
         def calculate_days_since(date_str):
             if not date_str:
                 return None
             try:
                 # Parse the date string (format: DD/MM/YYYY)
                 listed_date = datetime.datetime.strptime(
                     date_str, "%d/%m/%Y"
                 ).date()
                 # Get today's date
                 today = datetime.datetime.now().date()
                 # Calculate difference in days
                 delta = today - listed_date
                 return delta.days
             except:
                 return None


         # Apply the function to create a new column
         df["days_since_listed"] = df["date_listed"].apply(calculate_days_since)


         # Calculate average days on market (ignoring listings over 365 days old)
         days_data = df[df["days_since_listed"] <= 365]["days_since_listed"].dropna()
         if len(days_data) > 0:
             avg_days = days_data.mean()
             st.write(
                 f"⏳ Average days on the market: {avg_days:.1f} days (excluding listings over 365 days old)"
             )
             st.write(f"Based on {len(days_data)} listings out of {len(df)} total")
         else:
             st.write("No valid listings found to calculate average days on the market")


         # Calculate number of listings in last 3 months
         three_month_ago = datetime.datetime.now() - datetime.timedelta(days=90)
         three_month_date = three_month_ago.date()
         listings_3m = df[
             pd.to_datetime(
                 df["date_listed"], format="%d/%m/%Y", errors="coerce"
             ).dt.date
             >= three_month_date
         ]
         count_3m = len(listings_3m)
         st.write(f"{count_3m} listings in last 3 months")


         # Calculate number of listings in last 6 months
         six_month_ago = datetime.datetime.now() - datetime.timedelta(days=180)
         six_month_date = six_month_ago.date()
         listings_6m = df[
             pd.to_datetime(
                 df["date_listed"], format="%d/%m/%Y", errors="coerce"
             ).dt.date
             >= six_month_date
         ]
         count_6m = len(listings_6m)
         st.write(f"{count_6m} listings in last 6 months")


         # Calculate average and median prices for the last 6 months
         st.write("-" * 40)
         st.write("💰 Prices in last 6 months:")


         # Convert year_listed and month_listed to integers for proper comparison
         df["year_listed"] = pd.to_numeric(df["year_listed"], errors="coerce")
         df["month_listed"] = pd.to_numeric(df["month_listed"], errors="coerce")


         # Get current month and year
         current_date = datetime.datetime.now()
         current_year = current_date.year
         current_month = current_date.month


         # Function to get month name abbreviation
         def get_month_abbr(month_num):
             return datetime.date(2000, month_num, 1).strftime("%b")


         # Convert price string to numeric value
         df["price"] = (
             df["price"]
             .str.replace("Â£", "£", regex=False)
             .str.replace("Ãƒâ€šÃ‚Â£", "£", regex=False)
         )
         df["price_numeric"] = (
             df["price"]
             .str.replace("£", "", regex=False)
             .str.replace(",", "", regex=False)
             .astype(float)
         )


         # Store monthly data for percentage calculations
         monthly_data = []


         # Calculate stats for the last 6 months
         for i in range(6):
             # Calculate target month and year (going backward from current month)
             target_month = current_month - i
             target_year = current_year


             # Handle year rollover
             if target_month <= 0:
                 target_month += 12
                 target_year -= 1


             # Filter dataframe for this month and year
             month_data = df[
                 (df["month_listed"] == target_month)
                 & (df["year_listed"] == target_year)
             ]
             if len(month_data) > 0:
                 # Calculate stats on the price_numeric column
                 valid_prices = month_data["price_numeric"].dropna()


                 if len(valid_prices) > 0:
                     avg_price = valid_prices.mean()
                     median_price = valid_prices.median()








                     # Format the output with month abbreviation and year
                     month_abbr = get_month_abbr(target_month)
                     year_short = str(target_year)[2:]  # Get last two digits of year
                     st.write(
                         f"{month_abbr} '{year_short}: Average: £{avg_price:.0f}, Median: £{median_price:.0f} ({len(valid_prices)} listings)"
                     )








                     # Store for percentage calculations
                     monthly_data.append(
                         {
                             "month": f"{month_abbr} '{year_short}",
                             "avg_price": avg_price,
                             "median_price": median_price,
                             "count": len(valid_prices),
                             "index": i,  # Lower index = more recent
                         }
                     )








                 else:
                     month_abbr = get_month_abbr(target_month)
                     year_short = str(target_year)[2:]
                     st.write(f"{month_abbr} '{year_short}: No valid price data")








             else:
                 month_abbr = get_month_abbr(target_month)
                 year_short = str(target_year)[2:]
                 st.write(f"{month_abbr} '{year_short}: No listings found")








         # Calculate percentage changes
         median_change_3m = 0
         avg_change_3m = 0
         median_change_6m = 0
         avg_change_6m = 0








         if len(monthly_data) >= 3:
             # For 3 months
             current = monthly_data[0]
             three_months_ago = next(
                 (m for m in monthly_data if m["index"] >= 2), monthly_data[-1]
             )


             if current["median_price"] > 0 and three_months_ago["median_price"] > 0:
                 median_change_3m = (
                     (current["median_price"] / three_months_ago["median_price"]) - 1
                 ) * 100








             if current["avg_price"] > 0 and three_months_ago["avg_price"] > 0:
                 avg_change_3m = (
                     (current["avg_price"] / three_months_ago["avg_price"]) - 1
                 ) * 100


         if len(monthly_data) >= 6:
             # For 6 months
             current = monthly_data[0]
             six_months_ago = monthly_data[-1]


             if current["median_price"] > 0 and six_months_ago["median_price"] > 0:
                 median_change_6m = (
                     (current["median_price"] / six_months_ago["median_price"]) - 1
                 ) * 100


             if current["avg_price"] > 0 and six_months_ago["avg_price"] > 0:
                 avg_change_6m = (
                     (current["avg_price"] / six_months_ago["avg_price"]) - 1
                 ) * 100


         timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


         # st.write percentage changes
         st.write("-" * 40)
         st.write(
             f"📊 Median: 3 mo: {median_change_3m:+.1f}%, 6mo: {median_change_6m:+.1f}%"
         )
         st.write(f"📊 Average: 3 mo: {avg_change_3m:+.1f}%, 6mo: {avg_change_6m:+.1f}%")


         # Add this code to create and save the graph
         if monthly_data:
             create_price_trend_graph(monthly_data, timestamp, car["make"], car["model"])


         # Keep only the specified columns in the correct order
         selected_columns = [
             "name",
             "price",
             "year",
             "mileage",
             "engine",
             "date_listed",
             "day_listed",
             "month_listed",
             "year_listed",
             "days_since_listed",
             "link",
         ]


         # Make sure all requested columns exist (even if empty)
         for col in selected_columns:
             if col not in df.columns:
                 df[col] = None


         # Convert year column to string to handle "Brand New" values
         df["year"] = df["year"].astype(str)


         # Fix year format
         def fix_year_format(y):
             if pd.isna(y):
                 return ""
             elif y == "Brand New":
                 return "Brand New"
             else:
                 try:
                     # Try to convert to integer
                     return str(int(float(y)))
                 except (ValueError, TypeError):
                     # If conversion fails, return as is
                     return str(y)


         # Apply the function to the year column
         df["year"] = df["year"].apply(fix_year_format)


         # Select only these columns for the final CSV
         df_export = df[selected_columns]


         # Make sure year and mileage are strings to preserve all values
         df_export["year"] = df_export["year"].fillna("").astype(str)
         df_export["mileage"] = df_export["mileage"].fillna("").astype(str)


         # Replace "None" and "nan" with empty strings
         df_export["year"] = df_export["year"].replace(["None", "nan"], "")
         df_export["mileage"] = df_export["mileage"].replace(["None", "nan"], "")




         # Ensure the extracted year and mileage values are preserved
         for idx, row in df_export.iterrows():
             if pd.isna(row['year']) or row['year'] == '' or row['year'] == 'None' or row['year'] == 'nan':
                 # Try to find this listing in original data
                 matching_listings = [item for item in data if item.get('link') == row['link']]
                 if matching_listings and matching_listings[0].get('year'):
                     df_export.at[idx, 'year'] = str(matching_listings[0]['year'])
               
             if pd.isna(row['mileage']) or row['mileage'] == '' or row['mileage'] == 'None' or row['mileage'] == 'nan':
                 # Try to find this listing in original data
                 matching_listings = [item for item in data if item.get('link') == row['link']]
                 if matching_listings and matching_listings[0].get('mileage'):
                     df_export.at[idx, 'mileage'] = str(matching_listings[0]['mileage'])

         # Calculate average mileage from final filtered listings only
         final_valid_mileages = []
         for _, row in df_export.iterrows():
             if row.get('mileage') and row['mileage'] not in ['None', 'nan', '']:
                 try:
                     # Remove commas and convert to float
                     mileage_value = float(str(row['mileage']).replace(',', ''))
                     final_valid_mileages.append(mileage_value)
                 except (ValueError, TypeError):
                     pass

         if final_valid_mileages:
             final_avg_mileage = sum(final_valid_mileages) / len(final_valid_mileages)
             st.write("-" * 40)
             st.write(f"🛣️ Average Mileage: {final_avg_mileage:.0f} (from {len(final_valid_mileages)} filtered listings)")
         else:
             st.write("-" * 40)
             st.write("No valid mileage data in final listings")

         try:
             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
             filename = f"autotrader_results_{timestamp}.csv"
             df_export.to_csv(filename, index=False)
             st.write("-" * 40)
             st.write(f"💾 Results saved to {filename} with {len(df_export)} complete listings")
         except Exception as e:
             st.write(f"Error saving CSV: {str(e)}")

        # Supply Snapshot section
         st.write(f"{'-' * 20} SUPPLY SNAPSHOT: {car['make']} {car['model']} {'-' * 20}")
         total_listings = len(df_export)

         # Calculate market density (only if radius was provided)

         # Initialize market density variables
         market_density = 0
         market_density_str = "No radius provided"
         if criteria.get('radius'):
             try:
                 radius = float(criteria['radius'])
                 area = 3.14159 * (radius ** 2)  # Area of search circle
                 market_density = total_listings / area if area > 0 else 0
                 market_density_str = f"{market_density:.2f}"
             except (ValueError, TypeError):
                 market_density_str = "Invalid radius provided"
         else:
             market_density_str = "No radius provided"

         #Calculate price spread
         price_spread_pct = 0
         if len(df_export) > 1 and 'price_numeric' in df.columns:
             min_price = df['price_numeric'].min() /1000
             max_price = df['price_numeric'].max() /1000
             median_price = df['price_numeric'].median() / 1000
             if min_price > 0:
                 price_spread_pct = round(((max_price - min_price) / median_price) * 100)

         # Calculate turnover rate from average days on market
         avg_days = days_data.mean() if len(days_data) > 0 else 30
         turnover_rate_desc = "Good" if avg_days < 45 else "Average" if avg_days < 90 else "Slow"

         # Calculate competition index (0-100: 0-30 = Seller's Market, 30-70 = Balanced, 70+ = Buyer's Market)
         
         # Weight factors: Price spread (40%), Turnover rate (35%), Market density (25%)
         price_factor = min(price_spread_pct, 100) * 0.4  # Higher spread = buyer's advantage
         # Normalise days on market (0-100 scale where 0=0 days, 100=90+ days)
         days_normalised = min(avg_days, 90) / 90 * 100
         turnover_factor = days_normalised * 0.35  # Higher days = buyer's advantage

         # Handle market density factor differently based on whether radius was provided
         if criteria.get('radius'):
             density_normalised = min(market_density * 20, 100)  # Scale density to 0-100
             density_factor = density_normalised * 0.25
         else:
             # When no radius is provided, use a neutral density factor
             density_factor = 35  # Mid-point of the 0-70 range (balanced market)

         competition_index = round(price_factor + turnover_factor + density_factor)

         # st.write the snapshot
         st.write(f"🧮 Total Listings: {total_listings}")
         st.write(f"🗺️  Market Density: {market_density_str}")
         st.write(f"💲 Price Spread: {price_spread_pct:.0f}% (£{min_price:.0f}k - £{max_price:.0f}k)")
         st.write(f"🔄 Turnover Rate: {turnover_rate_desc} ({avg_days:.0f} days)")
         st.write(f"🎯 COMPETITION INDEX: {competition_index}/100 (0-100: 0-30 = Seller's Market, 30-70 = Balanced, 70+ = Buyer's Market)")

     else:
         st.write("No data found to save")

 except Exception as e:
     st.write(f"Error during scraping: {str(e)}")
 finally:
     driver.quit()

def extract_car_details(text, make, model):
 """Extract car details from text when regular extraction fails"""
 st.write(
     f"Extracting details from text: {text[:300]}..."
 )  # st.write 300 chars for debugging
 details = {
     "name": f"{make} {model}",
     "price": None,
     "year": None,
     "mileage": None,
     "mileage_numeric": None,
     "transmission": None,
     "fuel": None,
     "engine": None,
     "owners": None,
     "link": None,
 }

 # Extract price
 price_patterns = [
     r"(?:£|\$|€|Â£|Ãƒâ€šÃ‚Â£)\s*([\d,]+)",  # Currency symbol followed by number
     r"(?:price|cost|value)[:\s]*(?:£|\$|€|Â£|Ãƒâ€šÃ‚Â£)?\s*([\d,]+)",  # Price keyword followed by number
     r"(?:£|\$|€|Â£|Ãƒâ€šÃ‚Â£)\s*([\d,]+)(?!\s*miles)",  # Currency symbol with number NOT followed by "miles"
 ]

 for pattern in price_patterns:
     price_match = re.search(pattern, text, re.IGNORECASE)
     if price_match:
         price_value = price_match.group(1).replace(",", "")
         details["price"] = f"£{price_value}"
         break

 # Extract year
 year_patterns = [
     r"\b(20\d{2}|19\d{2})\b",  # Standard year format
     r"\((\d{2})\s+reg\)",  # Registration year format like (19 reg)
     r"(\d{4})\s*\([A-Z]\s*reg\)",  # Year with reg letter like 2019 (T reg)
     r"reg(?:istration)?[\s:]*(\d{4})",  # Registration followed by year
     r"(?:^|\s)('?\d{2})\s*plate",  # Year plate format like '23 plate
     r"(?:^|\s)(\d{2}\/\d{2})",  # Format like 23/73 (extract first part as year)
     r"(?:year|manufactured|built)[:\s]*(\d{4})",  # Year keyword followed by year
 ]


 for pattern in year_patterns:
     year_match = re.search(pattern, text, re.IGNORECASE)
     if year_match:
         year_str = year_match.group(1)
         # Handle 2-digit years
         if len(year_str) == 2:
             prefix = "20" if int(year_str) < 50 else "19"  # Assume 00-49 is 2000s, 50-99 is 1900s
             year_str = prefix + year_str
         details["year"] = int(year_str)
         break
 if not details["year"]:
     # Check if this is a brand new car
     brand_new_patterns = [
         r"\bbrand\s*new\b",
         r"\bnew\s*car\b",
         r"\bunregistered\b",
         r"\bzero\s*miles\b",
         r"\bdelivery\s*miles\b",
     ]
     is_brand_new = False
     for pattern in brand_new_patterns:
         if re.search(pattern, text, re.IGNORECASE):
             is_brand_new = True
             break
     if is_brand_new:
         details["year"] = "Brand New"
 
 # Extract mileage
 mileage_patterns = [
         r"([\d,]+)\s*miles",
         r"mileage[:\s]*([\d,]+)",
         r"([\d,]+)\s*mi",
         r"odometer[:\s]*([\d,]+)"
      ]


 for pattern in mileage_patterns:
         mileage_match = re.search(pattern, text, re.IGNORECASE)
         if mileage_match:
             try:
                 mileage_text = mileage_match.group(1).replace(",", "")
                 details["mileage"] = mileage_text
                 details["mileage_numeric"] = float(mileage_text)
                 st.write(f"DEBUG - Found mileage: {details['mileage']} using pattern: {pattern}")
                 break
             except Exception as e:
                 st.write(f"DEBUG - Mileage extraction error: {str(e)}")


 # Extract transmission type
 for trans_type in ["Manual", "Automatic", "Auto", "Semi-Auto", "Semi-Automatic"]:
     if trans_type.lower() in text.lower():
         details["transmission"] = trans_type
         break
 # Extract fuel type
 for fuel_type in [
     "Petrol",
     "Diesel",
     "Hybrid",
     "Electric",
     "Plug-in Hybrid",
     "PHEV",
 ]:
     if fuel_type.lower() in text.lower():
         details["fuel"] = fuel_type
         break
 # Extract engine size
 engine_pattern = r"(\d+\.\d+)(?:[L\s]|T|TT|TSI|TFSI|GDI|T-GDi|EcoBoost|VTEC|i-VTEC|VVT-i|VVTL-i|MIVEC|SkyActiv|Hemi|DOHC|SOHC|NA|SC|CRDi|dCi|TDI|4MATIC|xDrive|quattro)"
 engine_match = re.search(engine_pattern, text, re.IGNORECASE)
 if engine_match:
     details["engine"] = engine_match.group(1)
 else:
     # Try a simpler pattern as fallback
     simple_engine_pattern = r"(\d+\.\d+)"
     simple_engine_match = re.search(simple_engine_pattern, text)  # type: ignore
     if simple_engine_match:
         details["engine"] = simple_engine_match.group(1)


 st.write(f"DEBUG - Final details: Year: {details['year']}, Mileage: {details['mileage']}, Price: {details['price']}")


 return details


def create_price_trend_graph(monthly_data, timestamp, car_make, car_model):
 """Create a graph showing price trends over the last 6 months"""
 if not monthly_data or len(monthly_data) < 2:
     st.write("Not enough monthly data to create a meaningful graph")
     return
  # Sort data by index (lower index = more recent)
 sorted_data = sorted(monthly_data, key=lambda x: x['index'], reverse=True)
  # Extract data for plotting
 months = [item['month'] for item in sorted_data]
 avg_prices = [item['avg_price'] for item in sorted_data]
 median_prices = [item['median_price'] for item in sorted_data]
  # Create the figure and axis
 plt.figure(figsize=(10, 6))
 ax = plt.subplot(111)
  # Plot the lines
 ax.plot(months, avg_prices, 'o-', color='#1f77b4', linewidth=2, label='Average Price')
 ax.plot(months, median_prices, 's-', color='#ff7f0e', linewidth=2, label='Median Price')
  # Add data labels
 for i, (avg, med) in enumerate(zip(avg_prices, median_prices)):
     ax.annotate(f'£{avg:.0f}', (i, avg), textcoords="offset points",
                 xytext=(0,10), ha='center')
     ax.annotate(f'£{med:.0f}', (i, med), textcoords="offset points",
                 xytext=(0,-15), ha='center')
  # Format y-axis as currency
 def gbp_formatter(x, pos):
     return f'£{x:,.0f}'
 ax.yaxis.set_major_formatter(FuncFormatter(gbp_formatter))
  # Set labels and title
 plt.xlabel('Month')
 plt.ylabel('Price (£)')
 plt.title(f'{car_make} {car_model} Average and Median Prices Over Last 6 Months')
 plt.grid(True, linestyle='--', alpha=0.7)
 plt.legend()
  # Adjust layout and save
 plt.tight_layout()
 filename = f"average_price_trend_{timestamp}.png"
 plt.savefig(filename)
 st.write(f"📊 Price trend graph saved as {filename}")
 plt.close()


def main():
 st.write("Starting AutoTrader scraper...")
 start_time = time.time()
 st.write(f"Search criteria: {criteria}")
 st.write(f"Cars to search: {len(cars)}")


 # Add retry mechanism
 max_retries = 3
 for attempt in range(max_retries):
     try:
         st.write(f"Attempt {attempt+1} of {max_retries}")
         scrape_autotrader(cars, criteria)
         break  # If successful, break out of retry loop
     except Exception as e:
         st.write(f"Error on attempt {attempt+1}: {str(e)}")
         if attempt < max_retries - 1:
             st.write(f"Retrying in 5 seconds...")
             time.sleep(5)
         else:
             st.write("All retry attempts failed.")
             st.write("Scraping complete!")
 end_time = time.time()
 elapsed_time = end_time - start_time
 st.write("-" * 40)
 st.write(f"⏱ Total execution time: {elapsed_time:.2f} seconds")
 st.write("-" * 40)

if __name__ == "__main__":
 main()
