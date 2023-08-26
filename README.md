# ZillowScraper
Collect complete rental and sales data for any location from Zillow.


## Description
ZillowScraper is a Python package designed for scraping real estate data from Zillow. The scraper collects comprehensive details for rental and sale properties in specified locations. Extracted information includes unit number, price, square footage, number of baths, number of beds, and availability dates. The data is cleaned and formatted for further analysis and can be saved to CSV files.

## Features
- Scrape property details for specific locations from Zillow.
- Extract both sale and rental information.
- Data cleaning and structuring utilities.
- Output data to CSV for easy downstream analysis.


## Installation
```
git clone https://github.com/hansenrhan/ZillowScraper.git
cd ZillowScraper
pip install -r requirements.txt
```


## Usage

```Python
from ZillowScraper import collect_real_estate_data

# Define the target locations and types of properties to scrape
# locations should follow a city-state format
locations = ["manhattan-ny", "san-francisco-ca"]
property_types = ["rent", "sale"]

# Collect and save the data
collect_real_estate_data(locations, property_types)

```