"""import requests

url = "https://sec.wd3.myworkdayjobs.com/wday/cxs/sec/Samsung_Careers/job/645-Clyde-Avenue-Mountain-View-CA-USA/Staff-Engineer--Backend-Ad-Serving--Golang-_R94635"

payload = ""
headers = {
    "accept": "application/json",
    "accept-language": "en-US",
    "content-type": "application/x-www-form-urlencoded",
    "priority": "u=1, i",
    "referer": "https://sec.wd3.myworkdayjobs.com/en-US/Samsung_Careers/job/645-Clyde-Avenue-Mountain-View-CA-USA/Staff-Engineer--Backend-Ad-Serving--Golang-_R94635",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "x-calypso-csrf-token": "0a94cc2b-5f76-438c-bcf8-797eb9118b81"
}

response = requests.request("GET", url, data=payload, headers=headers)

print(response.text)"""
import os
import json
import requests
from time import sleep

# Directory containing the scraped JSON files
scraped_data_dir = 'jsonSamsungCareers'

# List to store all external URLs
external_urls = []

# Load each JSON file and gather external URLs
for filename in os.listdir(scraped_data_dir):
    if filename.endswith('.json'):
        file_path = os.path.join(scraped_data_dir, filename)
        with open(file_path, 'r') as file:
            data = json.load(file)
            for job_posting in data.get('jobPostings', []):
                external_urls.append(job_posting['externalPath'])

print(f"Total external URLs: {len(external_urls)}")

base_url = "https://sec.wd3.myworkdayjobs.com/wday/cxs/sec/Samsung_Careers"

# Headers for the requests
headers = {
    "accept": "application/json",
    "accept-language": "en-US",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

# Function to get job details from the external URL
def get_job_details(external_path):
    url = base_url + external_path
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get details for {external_path}")
        return None

# Check if the job details file already exists
if os.path.exists('job_details.json'):
    with open('job_details.json', 'r') as file:
        all_job_details = json.load(file)
else:
    all_job_details = []

# Make requests to gather job details
count = len(all_job_details) + 1  # Start count from the current length of job details
for external_path in external_urls[len(all_job_details):]:  # Continue from where we left off
    job_details = get_job_details(external_path)
    if job_details:
        all_job_details.append(job_details)
        
        # Update the JSON file after each successful scrape
        with open('job_details.json', 'w') as file:
            json.dump(all_job_details, file, indent=4)
        
        print(f"Job {count} saved")
        count += 1
        if count % 20 == 0:
            sleep(1)

print("Job details have been saved to job_details.json")
