# Scrapes top 10 pages on samsung from Reuters (links to articles)

import requests
import json
import os

# Define constants
REUTERS_URL = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-search-v2"
PAGES_TO_SCRAPE = 10
OUTPUT_DIRECTORY = "jsonReuters"

# Create the directory if it doesn't exist
if not os.path.exists(OUTPUT_DIRECTORY):
    os.makedirs(OUTPUT_DIRECTORY)

for page in range(1, PAGES_TO_SCRAPE + 1):
    querystring = {
        "query": json.dumps({
            "keyword": "samsung",
            "offset": (page - 1) * 20,
            "orderby": "display_date:desc",
            "size": 20,
            "website": "reuters"
        }),
        "d": "204",
        "_website": "reuters"
    }

    payload = ""
    headers = {
    "accept": '*/*',
    "accept-language": "en-US,en;q=0.9",
    "priority": "u=1, i",
    "referer": "https://www.reuters.com/site-search/?query=samsung&offset=20",
    "sec-ch-device-memory": "8",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-arch": '"arm"',
    "sec-ch-ua-full-version-list": '"Not/A)Brand";v="8.0.0.0", "Chromium";v="126.0.6478.183", "Google Chrome";v="126.0.6478.183"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": 'empty',
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    }

    response = requests.get(REUTERS_URL, headers=headers, params=querystring)

    # Save response data to a JSON file
    if response.status_code == 200:
        data = response.json()
        with open(os.path.join(OUTPUT_DIRECTORY, f'scraped_data_page_{page}.json'), 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Page {page} data saved successfully.")
    else:
        print(f"Failed to retrieve data for page {page}. Status code: {response.status_code}")
