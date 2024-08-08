import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Function to clean HTML tags from a string
def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(separator="\n")

# Function to convert postedOn field to actual date
def convert_posted_on(posted_on):
    days_ago_mapping = {
        "Today": 0,
        "Yesterday": 1
    }
    for key in days_ago_mapping.keys():
        if key in posted_on:
            days_ago = days_ago_mapping[key]
            return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    # Check for "Posted X Days Ago"
    if "Posted " in posted_on and " Days Ago" in posted_on:
        try:
            days_ago = int(posted_on.split("Posted ")[1].split(" Days Ago")[0])
            return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # Check for "Posted X+ Days Ago"
    if "Posted " in posted_on and "+ Days Ago" in posted_on:
        try:
            days_ago = int(posted_on.split("Posted ")[1].split("+ Days Ago")[0])
            return (datetime.now() - timedelta(days=days_ago)).strftime("Before %Y-%m-%d")
        except ValueError:
            pass

    return posted_on

# Load the job details JSON file
with open('job_details.json', 'r') as file:
    job_details = json.load(file)

# Clean the job descriptions and postedOn fields, including similarJobs
for job in job_details:
    job_posting_info = job.get("jobPostingInfo", {})
    job_posting_info["jobDescription"] = clean_html(job_posting_info.get("jobDescription", ""))
    job_posting_info["postedOn"] = convert_posted_on(job_posting_info.get("postedOn", ""))
    
    # Clean the similarJobs if they exist
    similar_jobs = job.get("similarJobs", [])
    for similar_job in similar_jobs:
        similar_job["postedOn"] = convert_posted_on(similar_job.get("postedOn", ""))

# Save the cleaned job details to a new JSON file
with open('cleaned_job_details.json', 'w') as file:
    json.dump(job_details, file, indent=4)

print("Cleaned job details have been saved to cleaned_job_details.json")
