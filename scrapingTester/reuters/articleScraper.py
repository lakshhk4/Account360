#used again for failed articles.
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

async def main():
    print("Loading extracted data from JSON file...")
    with open('updated_articles.json', 'r') as file:
        data = json.load(file)

    print("Identifying failed articles...")
    failed_articles = [article for article in data if not article.get('content')]

    if not failed_articles:
        print("No failed articles found.")
        return

    print(f"Retrying scraping for {len(failed_articles)} failed articles...")
    for i, article in enumerate(failed_articles, start=1):
        article_url = "https://www.reuters.com" + article['canonical_url']
        article_content = await scrape_reuters_article(article_url)
        article['content'] = article_content
        if article_content:
            print(f"Successfully re-scraped content for article {i}/{len(failed_articles)}: {article['title']}")
        else:
            print(f"Failed again to extract content for article {i}/{len(failed_articles)}: {article['title']}")

    print("Updating original JSON file with re-scraped content...")
    article_dict = {article['id']: article for article in failed_articles}
    for article in data:
        if article['id'] in article_dict:
            article['content'] = article_dict[article['id']]['content']

    with open('updated_articles.json', 'w') as file:
        json.dump(data, file, indent=4)
    print("Original JSON file updated.")

# Run the async main function
print("Starting script...")
asyncio.run(main())
print("Script finished.")
