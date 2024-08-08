# Testing Scraper on Google News
# Not working?
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import html


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

        # Go to the Google News search results page
        await page.goto("https://news.google.com/search?q=samsung&hl=en-US&gl=US&ceid=US%3Aen")

        all_content = []

        for i in range(3):  # Load more results three times for testing
            # Get the page content
            content = await page.content()
            all_content.append(content)
            print(f"Scraped page content {i + 1}.")

            # Scroll to the bottom to load more results
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print("Scrolled to bottom of the page.")
            await page.wait_for_timeout(5000)  # Wait for scrolling and new results to load

        # Close the browser
        await browser.close()

        return all_content

# Run the async function to scrape content
all_content = asyncio.run(scrape_google_news())

# Print or process the scraped content
for i, content in enumerate(all_content):
    cleaned_content = clean_html(content)
    print(f"Page {i + 1} cleaned content:")
    print(cleaned_content[:1000])  # Print first 1000 characters of each page content for verification
