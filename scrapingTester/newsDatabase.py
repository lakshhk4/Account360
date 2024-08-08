# Script that stores the JSON bloomberg data into a chromadb database
import os
from dotenv import load_dotenv
import json
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema import Document
import openai


# Load environment variables from .env file
load_dotenv()

# Access api keys from env
openai_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

os.environ['OPENAI_API_KEY'] = openai_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

# Step 2: Data Ingestion
file_names = [f'scraped_data_page_{i}.json' for i in range(1,10)]

articles = []

for file in file_names:
    with open(file, 'r') as f:
        data = json.load(f)
        articles.extend(data['results'])  # Collect all articles

# Convert articles to Langchain Document objects
documents = []
for article in articles:
    document = Document(
        #page_content=article['summary'],
        page_content= f"{article['headline']} {article['summary']}",
        metadata={
            'authors': article['authors'],
            'eyebrow': article['eyebrow'],
            'headline': article['headline'],
            'publishedAt': article['publishedAt'],
            'subtype': article['subtype'],
            'thumbnail': article['thumbnail'],
            'type': article['type'],
            'url': article['url']
        }
    )
    documents.append(document)

# Step 3: Generate Embeddings and Store Data in ChromaDB using Langchain
embedding = OpenAIEmbeddings()

print(len(documents))

vectordb = Chroma(persist_directory="./chroma_db")
