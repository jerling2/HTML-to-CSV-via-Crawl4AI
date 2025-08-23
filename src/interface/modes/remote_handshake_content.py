import asyncio
import csv
import json
import re
from ..abstracts.user_mode import UserMode
from src.utils import (
    Agent,
    normalize_markdown,
    embed_texts
)
from src.database import VectorDatabase
from crawl4ai import (
    CrawlerRunConfig,
    BrowserConfig, 
    JsonCssExtractionStrategy,
    CacheMode,
    DefaultMarkdownGenerator,
    BM25ContentFilter
)


class RemoteHandshakeContent(UserMode):

    def __init__(self):
        super().__init__()
        self.LOGIN_URL = 'https://uoregon.joinhandshake.com/login'

    async def _run(self, schema, hrefs, db):
        print(json.dumps(hrefs, indent=4))
        wait_condition = """() => {
            const button = document.querySelector('main > div > div + div + div + div button');
            if (button?.innerText === 'More') {
                // Expand the job description.
                button.click();
            } else if (button?.innerText === 'Less') {
                // The page loaded successfully.
                return true;
            }
            return false;
        }
        """
        pass_one_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(
                schema,
                verbose=True
            ),
            wait_for=f"js:{wait_condition}",
            delay_before_return_html=2.0
        )
        pass_two_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator()
        )
        async with Agent(login_url=self.LOGIN_URL, browser_config=BrowserConfig(headless=False)) as agent:
            result = await agent.extract_from_remote(hrefs[0], pass_one_config)
            if not result.success:
                print("Error, something went wrong")
                return
            extracted_content = json.loads(result.extracted_content)
            raw_html = extracted_content[0]["content"]
            result = await agent.extract_from_raw(raw_html, pass_two_config)
            if result.success:
                clean_md = normalize_markdown(result.markdown)
                embeddings = embed_texts([clean_md])
    
    def _load_table_data(self, table_data_path):
        required_fields = {"href", "company", "position", "pay", "type", "location"}

        with open(table_data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if not required_fields.issubset(reader.fieldnames):
                raise ValueError("TSV missing required fields")

    def interact(self):
        table_data_path = self.prompt_choose('data_table', "Please choose a table")
        with open(table_data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if "href" not in reader.fieldnames:
                raise ValueError("TSV file missing required 'href' column")
            if "href" not in reader.fieldnames:
                raise ValueError("TSV file missing required 'href' column")
            if "href" not in reader.fieldnames:
                raise ValueError("TSV file missing required 'href' column")
            hrefs = [row['href'] for row in reader]
        html_schema_path = self.prompt_choose('schema_html', "Please choose a html schema")
        with open(html_schema_path, 'r') as f:
            schema = json.load(f)
        with VectorDatabase('handshake') as db:
            result = asyncio.run(self._run(schema, hrefs, db))