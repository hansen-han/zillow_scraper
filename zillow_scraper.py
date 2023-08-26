# Load packages
import requests
import json
from bs4 import BeautifulSoup
import pandas as pd
import math
import re
import time
import urllib.parse


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def make_frame_rentals(frame, data_list):
    for i in data_list:
        for item in i['props']['pageProps']['searchPageState']['cat1']['searchResults']['listResults']:
            try:
                # check if the unit will require extra work, or is good as is....
                if "area" in list(item.keys()):
                    listing_type = "regular"
                    beds = item['beds']
                    baths = item['baths']
                    area = item['area']
                    unit_number = None
                    price = item['unformattedPrice']

                else:
                    listing_type = "nested"
                    beds = None
                    baths = None
                    area = None
                    unit_number = None
                    price = None

                unit_description = item['statusText']
                detailed_url = item["detailUrl"]
                latitude = item['latLong']['latitude']
                longitude = item['latLong']['longitude']
                unit_address = item['address']
                unit_address_street = item['addressStreet']
                unit_city = item['addressCity']
                unit_zipcode = item['addressZipcode']

                unit_dict = {
                    "listing_type": listing_type,
                    "unit_description": unit_description,
                    "detailed_url": detailed_url,
                    "latitude": latitude,
                    "longitude": longitude,
                    "unit_address": unit_address,
                    "unit_address_street": unit_address_street,
                    "unit_city": unit_city,
                    "unit_zipcode": unit_zipcode,
                    "beds": beds,
                    "baths": baths,
                    "area": area,
                    "price": price,
                    "unit_number": unit_number,
                }

                frame = frame.append(unit_dict, ignore_index=True)
                
            except:
                pass

    return frame


def make_frame_sales(frame, data_list):
    for i in data_list:
        for item in i['props']['pageProps']['searchPageState']['cat1']['searchResults']['listResults']:
            frame = frame.append(item, ignore_index=True)
    return frame


def extract_listing_count(html_content):
    try:

        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the span element with class "result-count"
        span_element = soup.find('span', class_='result-count')

        # Check if the span element was found
        if span_element:
            # Extract the number using regular expressions
            text_content = span_element.text
            match = re.search(r'([\d,]+)', text_content)

            if match:
                # Convert the number string with commas to an integer
                number = int(match.group(1).replace(',', ''))
                return number
        else:
            raise TypeError("Could not extract the number of listings")
    except Exception as e:
        raise TypeError("Could not extract the number of listings")

def zillow_url_constructor(location, category, pg_num, min_price):
    """
    Returns a url for the dynamic scraper to use.
    """

    # quick conversion
    if category == "rent":
        category = "rental"

    # validation
    if category not in ["rental", "sale"]:
        raise TypeError("invalid category for url_constructor(), must be either 'rental', or 'sale'")
    
    # --- default dictionaries used for setting parameters --- 
    rental_search_query_state_dict = {
        "pagination": {},
        "isMapVisible": True,
        "filterState": {
            "price": {
                "min": min_price,
            },
            "mp": {
                "min": min_price,
            },
            "fr": {
                "value": True
            },
            "fsba": {
                "value": False
            },
            "fsbo": {
                "value": False
            },
            "nc": {
                "value": False
            },
            "cmsn": {
                "value": False
            },
            "auc": {
                "value": False
            },
            "fore": {
                "value": False
            },
            "sort": {
                "value": "pricea"
            }
        },
        "isListVisible": True,
        "mapZoom": 11,
    }
    sale_search_query_state_dict = {
        "pagination": {},
        "isMapVisible": True,
        "filterState": {
            "price": {
                "min": min_price,
            },
            "sort": {
                "value": "pricea"
            },
            "mp": {
                "min": min_price,
            }
        },
        "isListVisible": True,
        "mapZoom": 11,
    }


    if category == "rental":
        if pg_num == 1:
            new_url = "https://www.zillow.com/{location}/{category}/?searchQueryState={searchQueryStateDict}".format(
                    location = location,
                    category="rentals",
                    searchQueryStateDict = urllib.parse.quote(str(rental_search_query_state_dict).replace("True", "true").replace("False", "false"))
                )
        else:
            rental_search_query_state_dict["pagination"] = {"currentPage":pg_num}

            new_url = "https://www.zillow.com/{location}/{category}/{pg_num}_p/?searchQueryState={searchQueryStateDict}".format(
                location = location,
                category="rentals",
                searchQueryStateDict = urllib.parse.quote(str(rental_search_query_state_dict).replace("True", "true").replace("False", "false")),
                pg_num = pg_num
            )

    else:
        if pg_num == 1:
            new_url = "https://www.zillow.com/{location}/?searchQueryState={searchQueryStateDict}".format(
                    location = location,
                    searchQueryStateDict = urllib.parse.quote(str(sale_search_query_state_dict).replace("True", "true").replace("False", "false"))
                )
        else:
            sale_search_query_state_dict["pagination"] = {"currentPage":pg_num}

            new_url = "https://www.zillow.com/{location}/{pg_num}_p/?searchQueryState={searchQueryStateDict}".format(
                    location = location,
                    searchQueryStateDict = urllib.parse.quote(str(sale_search_query_state_dict).replace("True", "true").replace("False", "false")),
                    pg_num = pg_num
                )
            
    return new_url
    
def make_request_with_backoff(url, headers, max_retries=5, base_delay=1):
    for retry in range(max_retries + 1):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        
        print(f"Request failed with status code {response.status_code}. Retrying in {base_delay * (2 ** retry)} seconds...")
        time.sleep(base_delay * (2 ** retry))
    
    print("Max retries reached. Request failed.")
    return None

def extract_zillow_page_json(request_obj):

    # find and extract the JSON of the listings from a zillow page
    html_content = request_obj.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # Locate the <script> tag with the specified id
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

    data = None
    # Extract the JSON content (if the tag is found)
    if script_tag:
        json_content = script_tag.string
        # Now, you can parse the json_content using json.loads
        data = json.loads(json_content)
    
    return data

def find_new_minimum(data, past_minimums):
    # get the new minimum price for the next iteration of the dynamic scraper

    listing_json = data['props']['pageProps']['searchPageState']['cat1']['searchResults']['listResults']
    attempt_num = 1
    # if we aren't able to extract it from the last one, we move backwards until we can...

    continue_run = True
    while continue_run:

        # if it is a non-nested listing, try extracting the price
        if "units" not in list(listing_json[len(listing_json)-attempt_num].keys()):
            try:
                return float(listing_json[len(listing_json)-attempt_num]['unformattedPrice'])
            except:
                pass

        # if it is a nested listing, go through more complex logic to extract the price...
        else:
            if len(listing_json[len(listing_json)-attempt_num]['units']) == 1:
                # if there is only one unit, it is simple to extract the price...
                price = listing_json[len(listing_json)-attempt_num]['units'][0]['price']
                # convert to numeric
                price = float(price.replace("$", "").replace(",", "").replace("+", ""))
                return price
            elif len(listing_json[len(listing_json)-attempt_num]['units']) > 1:
                # if there are multiple, take the bottom one that isn't less than past minimums (that way we don't end up in a loop)
                unit_prices = [unit['price'] for unit in listing_json[len(listing_json)-attempt_num]['units']]
                
                # convert price strings to numeric
                unit_prices = [float(unit_price.replace("$", "").replace(",", "").replace("+", "")) for unit_price in unit_prices]

                # remove all prices that are lower than previous minimums
                unit_prices = [unit_price for unit_price in unit_prices if unit_price < max(past_minimums)]

                # if there are still prices after filtering, get the lowest one
                if unit_prices:
                    return min(unit_prices)

                # if there are not, move on                    
                else:
                    pass
            else:
                pass
                # if there are no units there is a problem...move back one more

        # if we weren't able to extract the minimum price from it, move on to the next one.    
        attempt_num += 1
    
def zillow_scraper(city, property_type, time_between_scrapes, min_price, testing):
    """

    Collects all data available for a given city (either rental or sales). 

    Arguments:
        city (str): city name
        property_type (str): either "sale" or "rent"
        time_between_scrapes (int): number of seconds to wait before making consecutive requests
        min_price (int): the minimum price to start filtering on, useful to continue scraping if it is interrupted.
        testing (bool): if true, will return only the first page
    Returns:
        data_dict (dict): collection of extracted data

    """
    data_list = []

    # Validation
    if property_type not in ["sale", "rent"]:
        raise TypeError("property_type:", property_type,
                        "is not valid, select either 'sale' or 'rent'")
                        
    
    # --- get the total number of listings for the run --- 

    try:
        r = requests.get('https://www.zillow.com/homes/for_{property_type}/'.format(
            property_type=property_type) + city, headers=headers)
        html_content = r.text
        num_listings = extract_listing_count(html_content)

        # --- calculate the number of listings per page... ---
        soup = BeautifulSoup(html_content, 'html.parser')

        # Locate the <script> tag with the specified id
        script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

        # Extract the JSON content (if the tag is found)
        if script_tag:
            json_content = script_tag.string
            # Now, you can parse the json_content using json.loads
            data = json.loads(json_content)
            data_list.append(data)

            num_listings_per_page = len(
                data['props']['pageProps']['searchPageState']['cat1']['searchResults']['listResults'])

            # there is only 20 pages at max....so we need to calculate the max number of results that we are looking for in a query
            max_results = num_listings_per_page*20

            print("Total Listings:", num_listings)
        
        # if in testing mode, return the first bit
        if testing:
            data_dict = {
                "data_list":data_list,
                "min_price":min_price,
                "num_listings":num_listings
            }
            return data_dict

    except Exception as e:
        raise TypeError(
            "Error with getting the total number of listings")
    

    # --- Run Dynamic Scraper --- 
    # The idea here is to take chunks at a time...we set a minimum to max and sort in ascending....
    # take the price of the last one, and set that to be the next minimum, collect and run again until all are collected....
    # We know when to stop, when the total number of results are less than the max results (thats a sign we've hit the top)
        # For this case, we'll also need to calculate the number of pages to collect so we don't over-do it. (originally removed from zillow_scraper.ipynb)

    # variables for the loop 
    
    run_dynamic_scraper = True
    min_price = min_price
    target_pages = 20
    past_minimums = [0]

    # Continue to run the scraper until the maximum number of listings is hit.
    while run_dynamic_scraper:
        try:
            pg_num = 1
            # collect the first page, find out how many more pages to collect....
            #  construct the url given the minimum price, location, etc.. 
            url = zillow_url_constructor(location=city, category=property_type, pg_num=pg_num, min_price=min_price)

            # make request with retries/backoff system
            r = make_request_with_backoff(url = url, headers=headers, base_delay=time_between_scrapes)

            # if it is empty, raise error and end the script
            if not r:
                raise TypeError("make_request_with_backoff() failed, aborting scraping run.")

            # if it is not empty, collect the data of interest. 
            data = extract_zillow_page_json(r)

            if data:
                # if there is data, record it
                data_list.append(data)

                # on the first request...check to see if it is the last sequence to run (are there 20 pages of data?)
                if pg_num == 1: 
                    num_listings = extract_listing_count(r.text)
                    num_listings_per_page = len(data['props']['pageProps']['searchPageState']['cat1']['searchResults']['listResults'])
                    pages_to_collect = math.ceil(num_listings/num_listings_per_page)
                    if pages_to_collect < 20:
                        run_dynamic_scraper = False
                        target_pages = pages_to_collect
            else:
                # if there is no data, need to debug and figure out why it wasn't able to extract...
                print("=== Page HTML ====")
                print(r.text)
                print("=== End === ")
                raise TypeError("extract_zillow_page_json() failed, aborting scraping run.")


            # collect all remaining pages of data
            for pg_num in range(2, target_pages+1):
                #  construct the url given the minimum price, location, etc.. 
                url = zillow_url_constructor(location=city, category=property_type, pg_num=pg_num, min_price=min_price)

                # make request with retries/backoff system
                r = make_request_with_backoff(url = url, headers=headers, base_delay=time_between_scrapes)

                # if it is empty, raise error and end the script
                if not r:
                    raise TypeError("make_request_with_backoff() failed, aborting scraping run.")

                # if it is not empty, collect the data of interest. 
                data = extract_zillow_page_json(r)

                if data:
                    # if there is data, record it
                    data_list.append(data)
                else:
                    # if there is no data, need to debug and figure out why it wasn't able to extract...
                    raise TypeError("extract_zillow_page_json() failed, aborting scraping run.")

                # wait between each request to avoid being blocked
                time.sleep(time_between_scrapes)

            # after all the data has been collected...we need to find out the new minimum_price for the next round...
            # use "data" since it is the from the last round.
            past_minimums.append(min_price) # save the old minimum price
            min_price = find_new_minimum(data, past_minimums = past_minimums) # set the new minimum price

        # if there is an error, break the script, return whatever data was collected.
        except Exception as e:
            print("Error collecting data:", e)
            break

    data_dict = {
        "data_list":data_list,
        "min_price":min_price,
        "num_listings":num_listings
        }

    return data_dict


def extract_floor_plans(data):
    if isinstance(data, dict):
        if "floorPlans" in data:
            return data["floorPlans"]
        else:
            for key, value in data.items():
                result = extract_floor_plans(value)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = extract_floor_plans(item)
            if result is not None:
                return result
    return None

def get_units_from_detailed_url(detailed_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    target_url = "https://www.zillow.com{detailed_url}".format(detailed_url=detailed_url)
    r = requests.get(target_url, headers=headers)
    html_content = r.text
    soup = BeautifulSoup(html_content, 'html.parser')

    # extract the building info
    script_tag = soup.find("script", id="__NEXT_DATA__")

    # Check if the script tag was found
    if script_tag:
        # Extract the content of the <script> tag
        script_content = script_tag.string
    else:
        print("Script tag not found.")
    
    data_dict = json.loads(script_content)

    floor_plans = extract_floor_plans(data_dict)

    # convert dictionary to pandas dataframe with relevant data
    unit_number = []
    price = []
    sqft = []
    baths = []
    beds = []
    available_from = []
    for unit in floor_plans:
        unit_number.append(unit['units'][0]['unitNumber'])
        price.append(unit['units'][0]['price'])
        sqft.append(unit['units'][0]['sqft'])
        baths.append(unit['baths'])
        beds.append(unit['beds'])
        available_from.append(unit['units'][0]['availableFrom'])

    df = pd.DataFrame()
    df['unit_number'] = unit_number
    df['price'] = price
    df['sqft'] = sqft
    df['baths'] = baths
    df['beds'] = beds
    df['available_from'] = available_from
    
    return df


def rental_frame_expander(frame, time_to_sleep):

    # given a rental frame with nested and regular data, we want to get all units for each building
    for x in range(0, len(frame['listing_type'])):
        row = frame.iloc[x]
        if row['listing_type'] == "nested" and ".com" not in row['detailed_url']:
            try:
                building_data = get_units_from_detailed_url(row['detailed_url'])
                for j in range(0, len(building_data['unit_number'])):
                    unit_row = building_data.iloc[j]


                    unit_dict = {
                        "listing_type": "expanded",
                        "unit_description": row['unit_description'],
                        "detailed_url": row['detailed_url'],
                        "latitude": row['latitude'],
                        "longitude": row['longitude'],
                        "unit_address": row['unit_address'],
                        "unit_address_street": row['unit_address_street'],
                        "unit_city": row['unit_city'],
                        "unit_zipcode": row['unit_zipcode'],
                        "beds": unit_row['beds'],
                        "baths": unit_row['baths'],
                        "area": unit_row['sqft'],
                        "price": unit_row['price'],
                        "unit_number": unit_row['unit_number']
                    }

                    frame = frame.append(unit_dict, ignore_index=True)

                time.sleep(time_to_sleep)

                
            except Exception as e:
                print("Error:", e)
                pass
    
    return frame


def collect_real_estate_data(locations, property_types = ["rent", "sale"], output_directory = "./"):
    '''

    Collects real estate data for target locations and property types.
    
    Arguments:
        locations (list): a list of locations to collect
        property_types (list): toggle whether or not to collect rental/sale or both
        output_directory (str): where output files should be written to
    '''
    for location in locations:
        for property_type in property_types:
            data_dict = zillow_scraper(city=location, property_type=property_type, time_between_scrapes=120, testing=False, min_price=0)
            data = data_dict["data_list"]
            min_price = data_dict["min_price"]
            num_listings = data_dict["num_listings"]
            print(location, property_type, min_price, num_listings)
            df = pd.DataFrame()

            if property_type == "sale":
                # extract into a table
                df = make_frame_sales(df, data)

                #drop cols
                df = df.drop('hdpData', 1) #remove this line to see a whole bunch of other random cols, in dict format

                #drop dupes
                df = df.drop_duplicates(subset='zpid', keep="last")

                #filters
                df['zestimate'] = df['zestimate'].fillna(0)
                df['best_deal'] = df['unformattedPrice'] - df['zestimate']
            else:
                # convert the rental data json into a dataframe
                df = make_frame_rentals(df, data)

                # get rid of duplicate rows (since some may be collected more than once)
                df = df.drop_duplicates()

                # get additional data for nested apartments
                df = rental_frame_expander(df, time_to_sleep = 120)

                # remove nested rows now that we have the expanded data.
                df = df[df.listing_type != "nested"]

                # Drop the 'listing_type' column
                df = df.drop(columns=['listing_type'])

            
            df.to_csv("{output_directory}{location}_{property_type}_{date}.csv".format(location=location, property_type=property_type, date=todays_date, output_directory=output_directory))


def get_hoa_fee(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        r = requests.get(url, headers=headers)

        html_page = r.text

        # Initialize a BeautifulSoup object
        soup = BeautifulSoup(html_page, 'html.parser')

        # Find the span containing "monthly HOA fee"
        target_span = soup.find('span', string=re.compile(r'monthly HOA fee'))

        if target_span:
            
            text_content = target_span.string
            if text_content:
                text_content = text_content.replace("$", "").replace(",", "").replace(" monthly HOA fee", "")
                number = float(text_content)            
            if number:
                return number
            else:
                return None
        else:
            return None

    except Exception as e:
        return None
