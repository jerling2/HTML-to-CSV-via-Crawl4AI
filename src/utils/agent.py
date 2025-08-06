import json
import uuid
import os
import re
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode, BrowserConfig
from playwright.async_api import Page, BrowserContext, expect

class Agent:
    def __init__(self):
        self.login_manager = LoginProcedure()
        self.session_id = str(uuid.uuid4())

    async def extract_from_local_file(self, file_path, schema):
        if not file_path.startswith("file://"):
            raise TypeError('file path must start with file://')
        run_config = CrawlerRunConfig(
            session_id = self.session_id,
            cache_mode = CacheMode.BYPASS,  #< skip cache for this operation
            extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
        )
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=file_path,
                config=run_config
            )
            if not result.success:
                print("Crawl failed:", result.error_message)
                return None
            return json.loads(result.extracted_content)

    async def ping_website(self, url: str):
        """
        TODO: in this current state, this function handles login. Ultimately, 
        I want this function to check if the crawler is already auth, and if not, 
        check if it can login (or else raise an error). Then I want it to crawl for data.
        """
        crawler = self.login_manager.uoregon_handshake_auth()
        run_config = CrawlerRunConfig(
            delay_before_return_html=10.0
        )
        await crawler.start()
        await crawler.arun('https://uoregon.joinhandshake.com/login', config=run_config)
        await crawler.close()


class LoginProcedure:

    def __contains__(self, url):
        return url in self.procedures

    def uoregon_handshake_auth(self) -> AsyncWebCrawler:
        username = os.getenv("HANDSHAKE_USER")
        password = os.getenv("HANDSHAKE_PASS")
        crawler = AsyncWebCrawler(config=BrowserConfig(headless=False))
        async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
            await page.goto('https://uoregon.joinhandshake.com/login')
            await page.locator(".sso-button").click()
            await page.get_by_placeholder("Username").fill(username)
            await page.get_by_placeholder("Password").fill(password)
            await page.get_by_role("button", name="Login").click()
            await expect(page.get_by_role("heading", name="Enter code in Duo Mobile")).to_be_visible(timeout=60_000)
            sso_code = await page.get_by_text(re.compile(r"^\d+$")).text_content()
            print(f"\x1b[32m[AUTH] SSO Code: {sso_code}\x1b[0m")
            await expect(page.get_by_role("button", name="Yes, this is my device")).to_be_visible(timeout=10_000)
            await page.get_by_role("button", name="Yes, this is my device").click()
            return page
        crawler.crawler_strategy.set_hook('on_page_context_created', on_page_context_created)
        return crawler

    async def login(self, url, session_id, crawler):
        if url not in self.procedures:
            raise TypeError(f"{url} is not a recognized Login procedure.")
        await self.procedures[url](session_id, crawler)