import json
import uuid
import os
import re
import traceback
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode, BrowserConfig, CrawlResult
from playwright.async_api import Page, BrowserContext, expect


class Agent:
    def __init__(self, login_url=None, browser_config=None):
        self.login_procedures = LoginProcedure()
        self.session_id = str(uuid.uuid4())
        self.crawler = None
        self.login_url = login_url
        self.browser_config = browser_config or BrowserConfig()

    async def __aenter__(self):
        """ Execute immediately after entering an `async wait` block """
        if self.login_url and self.login_url in self.login_procedures:
            self.crawler = self.login_procedures.auth(self.login_url, self.browser_config)
        else:
            self.crawler = AsyncWebCrawler(config=browser_config)
        print("\x1b[1;36m[INIT].... \u2192 Agent\x1b[0m")
        await self.crawler.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """ Execute just before leaving an `async wait` block """
        await self.__cleanup_crawler()
        if exc_type:
            print("Exception occurred!")
            formatted_tb = ''.join(traceback.format_exception(exc_type, exc_val, exc_tb))
            print("Detailed traceback:")
            print(formatted_tb)
        return False

    async def __cleanup_crawler(self):
        if self.crawler is not None:
            await self.crawler.close()
            self.crawler = None

    async def extract_from_local_file(self, file_path, schema):
        if not file_path.startswith("file://"):
            raise TypeError('file path must start with file://')
        run_config = CrawlerRunConfig(
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

    async def extract_from_raw(self, raw, run_config=None):
        if self.crawler is None:
            raise ValueError('Error: this method must be used in a `async with` block')
        run_config = run_config or CrawlerRunConfig()
        result = await self.crawler.arun(f'raw://{raw}', config=run_config)
        return result

    async def extract_from_remote(self, url: str, run_config=None) -> [CrawlResult]:
        if self.crawler is None:
            raise ValueError('Error: this method must be used in a `async with` block')
        run_config = run_config or CrawlerRunConfig()
        result = await self.crawler.arun(url, config=run_config)
        return result

    async def extract_many_from_remote(self, urls: [str], run_config=None, dispatcher=None) -> [CrawlResult]:
        if self.crawler is None:
            raise ValueError('Error: this method must be used in a `async with` block')
        results = await self.crawler.arun_many(urls, config=run_config, dispatcher=dispatcher)
        return results


class LoginProcedure:

    def __init__(self):
        self.procedures = {
            'https://uoregon.joinhandshake.com/login': self.uoregon_handshake_auth
        }

    def __contains__(self, url):
        return url in self.procedures

    def uoregon_handshake_auth(self, browser_config) -> AsyncWebCrawler:
        print('\x1b[1;36m[LOGIN]... \u2192 uoregon.joinhandshake.com\x1b[0m')
        username = os.getenv("HANDSHAKE_USER")
        password = os.getenv("HANDSHAKE_PASS")
        crawler = AsyncWebCrawler(config=browser_config)
        async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
            if any(
                cookie['name'] == 'production_current_user' and 
                cookie['domain'] == 'uoregon.joinhandshake.com' 
                for cookie in await context.cookies()
            ):
                # User is already logged in, no need to authenticate again.
                return page
            await page.goto('https://uoregon.joinhandshake.com/login')
            await page.locator(".sso-button").click()
            await page.get_by_placeholder("Username").fill(username)
            await page.get_by_placeholder("Password").fill(password)
            await page.get_by_role("button", name="Login").click()
            await expect(page.get_by_role("heading", name="Enter code in Duo Mobile")).to_be_visible(timeout=10_000)
            sso_code = await page.get_by_text(re.compile(r"^\d+$")).text_content()
            print(f"\x1b[1;93m[AUTH] SSO : {sso_code}\x1b[0m")
            await expect(page.get_by_role("button", name="Yes, this is my device")).to_be_visible(timeout=60_000)
            print(f"\x1b[1;93m[SUCCESS]\x1b[0m")
            await page.get_by_role("button", name="Yes, this is my device").click()
            await expect(page.get_by_role("heading", name="University of Oregon")).to_be_visible(timeout=10_000)
            # Suggestion: save cookies here, and set a flag. If the user intends to reuse the same context, the cookies can be restored.
            return page
        crawler.crawler_strategy.set_hook('on_page_context_created', on_page_context_created)
        return crawler

    def auth(self, url, browser_config):
        if url not in self.procedures:
            raise TypeError(f"{url} is not a recognized Login procedure.")
        return self.procedures[url](browser_config)