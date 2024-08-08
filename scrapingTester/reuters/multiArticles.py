import json
import asyncio
from playwright.async_api import async_playwright

async def scrape_reuters_article(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto(url, timeout=5000, wait_until="commit")
        except Exception as e:
            print(f"Navigation timeout for URL: {url}, Error: {e}")
            await browser.close()
            return ""

        try:
            await page.wait_for_selector("div[data-testid='ArticleBody']", timeout=5000)
            paragraphs = await page.query_selector_all("div[data-testid='ArticleBody'] div[data-testid^='paragraph-']")
            content = [await paragraph.inner_text() for paragraph in paragraphs]
            cleaned_content = ' '.join(content).replace(', opens new tab', '').replace('\n', ' ').strip()
            return cleaned_content
        except Exception as e:
            print(f"Error extracting content from URL: {url}, Error: {e}")
            return ""
        finally:
            await browser.close()

async def process_batch(data, start, end):
    articles_to_process = data[start:end]
    for i, article in enumerate(articles_to_process, start=1):
        article_url = "https://www.reuters.com" + article['canonical_url']
        article_content = await scrape_reuters_article(article_url)
        article['content'] = article_content
        if article_content:
            print(f"Successfully extracted content for article {start+i}/{len(data)}: {article['title']}")
        else:
            print(f"Failed to extract content for article {start+i}/{len(data)}: {article['title']}")

    return articles_to_process

async def main():
    with open('extracted_data.json', 'r') as file:
        data = json.load(file)

    batch_size = 5
    num_batches = len(data) // batch_size + (1 if len(data) % batch_size != 0 else 0)

    for batch_num in range(num_batches):
        start = batch_num * batch_size
        end = start + batch_size
        print(f"Processing batch {batch_num+1}/{num_batches} (articles {start+1} to {min(end, len(data))})")
        processed_articles = await process_batch(data, start, end)

        # Append the processed articles to the updated JSON file
        try:
            with open('updated_articles.json', 'r') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = []

        existing_data.extend(processed_articles)
        with open('updated_articles.json', 'w') as file:
            json.dump(existing_data, file, indent=4)

        print(f"Batch {batch_num+1} saved to 'updated_articles.json'")

print("Starting script...")
asyncio.run(main())
print("Script finished.")
