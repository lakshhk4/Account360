# Attempt to scrape multiple pages from bloomberg 
# But doesn't seem to work.
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

        # Go to the Bloomberg search results page
        await page.goto("https://www.bloomberg.com/search?query=samsung")

        all_content = []

        for i in range(3):  # Load more results three times for testing
            # Get the page content
            content = await page.content()
            all_content.append(content)
            print(f"Scraped page content {i + 1}.")

            # Scroll to the bottom to load more results
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            print("Scrolled to bottom of the page.")
            await page.wait_for_timeout(3000)  # Wait for scrolling and new results to load

            # Click the "Load More Results" button
            try:
                load_more_button = await page.wait_for_selector('button[title="Load More Results"]', timeout=10000)
                if load_more_button:
                    print(f"Load More Results button found on attempt {i + 1}. Clicking button.")
                    await load_more_button.click()
                    await page.wait_for_timeout(7000)  # Wait for new results to load
                else:
                    print("Load More Results button not found.")
                    break
            except Exception as e:
                print(f"No more results to load or button not found on attempt {i + 1}: {e}")
                break

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
