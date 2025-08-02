import json
from crawl4ai import AsyncWebCrawler, JsonCssExtractionStrategy, CrawlerRunConfig, BrowserConfig, CacheMode


async def extract_from_local_file(uri, schema, out_path=None):
    run_config = CrawlerRunConfig(
        cache_mode = CacheMode.BYPASS,  #< skip cache for this operation
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    )
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=uri,
            config=run_config
        )
        if not result.success:
            print("Crawl failed:", result.error_message)
            return None
        return json.loads(result.extracted_content)


async def login_to_website(url):
    browser_cfg = BrowserConfig(
        headless=False
    )

    run_cfg = CrawlerRunConfig(
        delay_before_return_html=600
    )

    async with AsyncWebCrawler(config=browser_cfg, verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            config=run_cfg
        )
        if not result.success:
            print("Crawl failed:", result.error_message)
            return None
        print(result.html)
