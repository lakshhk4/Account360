import json
import os

# Define constants
OUTPUT_DIRECTORY = "jsonReuters"
EXTRACTED_DATA_FILE = "extracted_data.json"

def extract_data_from_file(file_path):
    with open(file_path, 'r') as json_file:
        data = json.load(json_file)
        
    articles = data.get("result", {}).get("articles", [])
    
    # Collect desired information for each article
    extracted_data = []
    for article in articles:
        extracted_article = {
            "id": article.get("id"),
            "canonical_url": article.get("canonical_url"),
            "basic_headline": article.get("basic_headline"),
            "title": article.get("title"),
            "description": article.get("description"),
            "web": article.get("web"),
            "headline_feature": article.get("headline_feature"),
            "published_time": article.get("published_time")
        }
        extracted_data.append(extracted_article)
    
    return extracted_data

# Aggregate extracted data from all JSON files
all_extracted_data = []
for filename in os.listdir(OUTPUT_DIRECTORY):
    if filename.endswith(".json"):
        file_path = os.path.join(OUTPUT_DIRECTORY, filename)
        all_extracted_data.extend(extract_data_from_file(file_path))

# Save all extracted data to a new JSON file
with open(EXTRACTED_DATA_FILE, 'w') as output_file:
    json.dump(all_extracted_data, output_file, indent=4)

print(f"Extracted data saved to {EXTRACTED_DATA_FILE} successfully.")
