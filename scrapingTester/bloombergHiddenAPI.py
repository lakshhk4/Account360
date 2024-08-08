# Scraping Script, bloomberg!
# CORRECT VERSION
import requests
import json
import os

url = "https://www.bloomberg.com/markets2/api/search"
pages_to_scrape = 10
output_directory = "jsonBloomberg"

# Create the directory if it doesn't exist
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for page in range(5, pages_to_scrape):
    querystring = {"query": "samsung", "page": page, "sort": "time:desc"}

    payload = ""
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://www.bloomberg.com/search?query=samsung",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
    
    # Save response data to a JSON file
    if response.status_code == 200:
        data = response.json()
        with open(os.path.join(output_directory, f'scraped_data_page_{page}.json'), 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Page {page} data saved successfully.")
    else:
        print(f"Failed to retrieve data for page {page}. Status code: {response.status_code}")
