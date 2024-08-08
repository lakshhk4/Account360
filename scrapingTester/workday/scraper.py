import requests
import json
import os

# Define constants
URL = "https://sec.wd3.myworkdayjobs.com/wday/cxs/sec/Samsung_Careers/jobs"
PAGES_TO_SCRAPE = 33
OUTPUT_DIRECTORY = "jsonSamsungCareers"

# Create the directory if it doesn't exist
if not os.path.exists(OUTPUT_DIRECTORY):
    os.makedirs(OUTPUT_DIRECTORY)

# Headers for the requests
headers = {
    "accept": "application/json",
    "accept-language": "en-US",
    "content-type": "application/json",
    "origin": "https://sec.wd3.myworkdayjobs.com",
    "priority": "u=1, i",
    "referer": "https://sec.wd3.myworkdayjobs.com/Samsung_Careers",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "x-calypso-csrf-token": "4e71e619-52ff-442e-87bb-37b6a5a7d34c"
}

# Loop through the pages and make requests
for page in range(PAGES_TO_SCRAPE):
    payload = {
        "appliedFacets": {},
        "limit": 20,
        "offset": page * 20,
        "searchText": ""
    }
    
    response = requests.post(URL, json=payload, headers=headers)

    # Save response data to a JSON file
    if response.status_code == 200:
        data = response.json()
        with open(os.path.join(OUTPUT_DIRECTORY, f'scraped_data_page_{page + 1}.json'), 'w') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Page {page + 1} data saved successfully.")
    else:
        print(f"Failed to retrieve data for page {page + 1}. Status code: {response.status_code}")
