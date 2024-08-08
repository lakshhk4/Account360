# Another attempt at Bloomberg Scraping
# Doesn't work beyond 1st page.
import asyncio
import pprint
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_transformers import BeautifulSoupTransformer
from playwright.async_api import async_playwright
from langchain.chains import create_extraction_chain
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access api keys from env
openai_api_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')

print(f"OpenAI API Key: {openai_api_key}")
print(f"Langchain API Key: {langsmith_api}")

os.environ['OPENAI_API_KEY'] = openai_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

# Schema definition
schema = {
    "properties": {
        "article_title": {"type": "string"},
        "article_description": {"type": "string"},
    },
    "required": ["article_title", "article_description"],
}

def extract(content: str, schema: dict):
    # Assuming llm is defined and configured elsewhere in your code
    return create_extraction_chain(schema=schema, llm=llm).run(content)

async def fetch_content_with_scroll(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        # Scroll and wait for content to load
        previous_height = await page.evaluate("document.body.scrollHeight")
        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)  # Adjust delay as needed
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                break
            previous_height = new_height

        content = await page.content()
        await browser.close()
        return content

async def load_urls_with_scroll(urls):
    tasks = [fetch_content_with_scroll(url) for url in urls]
    return await asyncio.gather(*tasks)

def scrape_with_playwright(urls, schema):
    # Load content from URLs with scrolling
    html_contents = asyncio.run(load_urls_with_scroll(urls))

    # Wrap the content in Document objects
    documents = [Document(page_content=content) for content in html_contents]

    # Transform content with BeautifulSoup
    bs_transformer = BeautifulSoupTransformer()
    docs_transformed = bs_transformer.transform_documents(
        documents, tags_to_extract=["span"]
    )

    # Split the documents into manageable chunks
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=1000, chunk_overlap=0
    )
    splits = splitter.split_documents(docs_transformed)

    # Process each split with the LLM
    extracted_contents = []
    for split in splits:
        extracted_content = extract(schema=schema, content=split.page_content)
        extracted_contents.append(extracted_content)

    pprint.pprint(extracted_contents)
    return extracted_contents

# Define URLs
urls = ["https://www.bloomberg.com/search?query=samsung"]

# Extract content
extracted_contents = scrape_with_playwright(urls, schema=schema)
