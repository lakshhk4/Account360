# Bloomberg Scraper with create_extraction_chain built-in langchain
# only able to retreive from first page

import asyncio
from playwright.async_api import async_playwright
from langchain.chains import create_extraction_chain
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import html


load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
langsmith_api = os.getenv('LANGCHAIN_API_KEY')
if not openai_api_key:
    raise ValueError("OpenAI API Key not found")
os.environ['OPENAI_API_KEY'] = openai_api_key
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.langchain.plus"
os.environ["LANGCHAIN_API_KEY"] = langsmith_api
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")

schema = {
            "properties": {
                "article_title": {"type": "string"},
                "article_description": {"type": "string"},
            },
            "required": ["article_title", "article_description"],
        }
    

def extract(content: str, schema: dict):
    extraction_chain = create_extraction_chain(schema=schema, llm=llm)
    return extraction_chain.run(content)

def myOwnExtractor(content: str):
    extractionPrompt = """
    Please extract the following information from the provided cleaned-up webpage content:

    Article Titles: The title of each article.
    Article Descriptions: A brief description or summary of each article.
    
    The extracted information should be formatted as a JSON array of objects, with each object containing the following fields:

    Content: {content}
    """
    templateExtraction = ChatPromptTemplate.from_template(extractionPrompt)
    chainRAG = LLMChain(llm=llm, prompt=templateExtraction, output_key="extracted_articles")
    extracted = chainRAG.run(content)
    return extracted



def clean_html(html_content):
    # Parse HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    # Get text content and decode HTML entities
    text = soup.get_text()
    text = html.unescape(text)

    # Remove extra whitespace
    text = ' '.join(text.split())

    return text

async def scrape_google_news():
    async with async_playwright() as p:
        # Launch the browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to the Google News website
        #await page.goto("https://news.google.com/topics/CAAqIggKIhxDQkFTRHdvSkwyMHZNREZ1YmpjNUVnSmxiaWdBUAE?hl=en-US&gl=US&ceid=US%3Aen")
        
        await page.goto("https://www.bloomberg.com/search?query=samsung")
        # Get the page content
        content = await page.content()
        # Print the page content
        print(content)
        cleaned_content = clean_html(content)
        print(cleaned_content)

        #limited_content = content[:10000]
        #print("Limited Content Length:", len(limited_content))
        # Extract information using the extraction chain
        #extracted_content = extract(cleaned_content, schema)
        extracted_content = myOwnExtractor(cleaned_content)
        print("Extraction....LLM")
        print(extracted_content)


        # Close the browser
        await browser.close()

        

# Run the async function to scrape content
asyncio.run(scrape_google_news())
