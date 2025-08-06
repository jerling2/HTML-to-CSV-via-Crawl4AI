import json
import uuid
import os
import re
import traceback
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode, BrowserConfig
from playwright.async_api import Page, BrowserContext, expect

"""
TODO:
- implement __aenter__(self) to enter an `async with` in Agent
- implement __aexit(self, exc_type, exc_val, exc_tb) to exit an `async with` in Agent

All that matters is that __aexit__ will close the agent. __aenter__ doesn't matter really.

"I want the Modes to be able to use an agent in the following way":

# Example 1: Extract from a local file
async with Agent as agent:
    result = agent.extract_from_local( [file_paths], schema )

# Example 2: Extract from a remote destination
async with Agent as agent:
    results: [CrawlResult] = agent.extract_from_remote( [urls], schema )

"Automatic Handling of Auth via LoginProcedure":

When a crawler accesses a destination, I want to check whether the redirected_url is in LoginProcedure.
If so: then toss out the old crawler and get a new one from LoginProcedures
Otherwise: if the CrawlResult fails, raise a Warning "You might be accessing destination w/out proper credentials".
"""


class Agent:
    def __init__(self):
        self.login_procedures = LoginProcedure()
        self.session_id = str(uuid.uuid4())
        self.crawler = None

    async def __aenter__(self):
        """ Execute immediately after entering an `async wait` block """
        print("\x1b[1;36m[INIT].... \u2192 Agent\x1b[0m")
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

    async def crawl_remote(self, url, run_config=None, browser_config=None, __num_retries=0):
        if __num_retries >= 2:
            await self.__cleanup_crawler()
            print("\x1b[31mError..... \u2716 reached max number of retries\x1b[0m")
            return None
        run_config = run_config or CrawlerRunConfig()
        browser_config = browser_config or BrowserConfig()
        if self.crawler is None:
            self.crawler = AsyncWebCrawler(config=browser_config, verbose=True)
            await self.crawler.start()
        result = await self.crawler.arun(url, config=run_config)
        if result.redirected_url in self.login_procedures:
            await self.__cleanup_crawler()
            self.crawler = self.login_procedures.auth(result.redirected_url, browser_config)
            await self.crawler.start()
            __num_retries += 1
            return await self.crawl_remote(url, run_config, browser_config, __num_retries)
        return result

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

    async def extract_from_remote(self, url, schema):
        result = await self.crawl_remote(url)


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
            await expect(page.get_by_role("heading", name="Enter code in Duo Mobile")).to_be_visible(timeout=59_000)
            sso_code = await page.get_by_text(re.compile(r"^\d+$")).text_content()
            print(f"\x1b[1;93m[AUTH] SSO : {sso_code}\x1b[0m")
            await expect(page.get_by_role("button", name="Yes, this is my device")).to_be_visible(timeout=10_000)
            print(f"\x1b[1;93m[SUCCESS]\x1b[0m")
            await page.get_by_role("button", name="Yes, this is my device").click()
            await expect(page.get_by_role("heading", name="University of Oregon")).to_be_visible(timeout=10_000)
            return page
        crawler.crawler_strategy.set_hook('on_page_context_created', on_page_context_created)
        return crawler

    def auth(self, url, browser_config):
        if url not in self.procedures:
            raise TypeError(f"{url} is not a recognized Login procedure.")
        return self.procedures[url](browser_config)