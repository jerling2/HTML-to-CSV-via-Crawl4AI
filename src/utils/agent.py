import json
import uuid
import os
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, CacheMode, BrowserConfig


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
    
    async def auth_crawl(self, url, browser_config=None, run_config=None):
        if not browser_config:
            browser_config = BrowserConfig()
        if not run_config:
            run_config = CrawlerRunConfig()
        run_config = CrawlerRunConfig(
            session_id = self.session_id,
            cache_mode = CacheMode.BYPASS,  #< skip cache for this operation
        )
        async with AsyncWebCrawler(config=browser_config, verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                config=run_config
            )
            if not result.success:
                print("Crawl failed:", result.error_message)
                return None
            if result.redirected_url in self.login_manager:
                await self.login_manager.login(result.redirected_url, result.session_id, crawler)
            return result #< This should always return a call

    async def probe_website(self, url: str):
        result = await self.auth_crawl(url, 
        BrowserConfig(headless=False), #< For debugging
        CrawlerRunConfig(
            session_id = self.session_id,
            cache_mode = CacheMode.BYPASS
        ))


class LoginProcedure:
    def __init__(self):
        self.procedures = {
            "https://uoregon.joinhandshake.com/login": self.uoregon_handshake
        }

    def __contains__(self, url):
        return url in self.procedures

    async def uoregon_handshake(self, session_id, crawler):
        username = os.getenv("HANDSHAKE_USER")
        password = os.getenv("HANDSHAKE_PASS")
        run_config = CrawlerRunConfig(
            session_id=session_id,
            js_code=[
                "document.querySelector('a.sso-button').click();",
                "const username = document.querySelector('input#username');",
                f"username.value = '{username}';",
                "const password = document.querySelector('input#password');",
                f"password.value = '{password}';",
                "document.querySelector('input.submit').click();",
            ],
            delay_before_return_html=10.0 #< for debugging.
        )
        result = await crawler.arun(
            url="https://uoregon.joinhandshake.com/login",
            config=run_config,
        )
        if not result.success:
            print("Crawl failed (uoregon_handshake):", result.error_message)
            return None
        return print(result.redirected_url)

    async def login(self, url, session_id, crawler):
        if url not in self.procedures:
            raise TypeError(f"{url} is not a recognized Login procedure.")
        await self.procedures[url](session_id, crawler)