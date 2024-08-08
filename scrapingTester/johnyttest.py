# Learning Scraping from Johnty Test
from playwright.sync_api import sync_playwright
import time
from rich import print


def scroll_me():

    def check_json(response):
        if "products" in response.url:
            print({"url": response.url, "body": response.json()})

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 1080})
        
        page.on("response", lambda response:check_json(response))
        page.goto("https://www.reuters.com/legal/litigation/samsung-owes-142-mln-wireless-patent-case-jury-says-2024-04-17")
        time.sleep(2)
        #page.click("#hf_cookie_text_cookieAccept")
        page.wait_for_load_state("networkidle")
        
        html_content = page.content()
        print(html_content)
        browser.close()

scroll_me()