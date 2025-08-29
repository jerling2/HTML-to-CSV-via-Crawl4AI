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
from src.systems import VectorDatabase
from crawl4ai import (
    CrawlerRunConfig,
    BrowserConfig, 
    JsonCssExtractionStrategy,
    CacheMode,
    DefaultMarkdownGenerator,
    BM25ContentFilter
)


class RemoteHandshakeSummary(UserMode):

    def __init__(self):
        super().__init__()
        self.LOGIN_URL = 'https://uoregon.joinhandshake.com/login'

    async def _run(self, schema, data, collection_name):
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
        run_extract_html_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(
                schema,
                verbose=True
            ),
            wait_for=f"js:{wait_condition}",
            delay_before_return_html=0.0 #< For debugging (dleetl8r)
        )
        run_generate_markdown_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator()
        )
        DEBUG_HREF = data[0]['href']
        async with Agent(login_url=self.LOGIN_URL, browser_config=BrowserConfig(headless=False)) as agent:
            result = await agent.extract_from_remote(DEBUG_HREF, run_extract_html_config) #< change this to extract many l8r
            if not result.success:
                return print("Error, something went wrong")
            extracted_content = json.loads(result.extracted_content)
            raw_html = extracted_content[0]["job_summary"]
            result = await agent.extract_from_raw(raw_html, run_generate_markdown_config)
            if not result.success:
                return print("Error, something went wrong")
            clean_md = normalize_markdown(result.markdown)
            vector = embed_texts([clean_md])[0]
            data[0]['summary_vector'] = vector
            self.db.upsert(collection_name, [data[0]])
    
    # could be a util function `load_table_data based on milvus schema`
    def _load_table_data(self, table_data_path):
        data = []
        with open(table_data_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                row["job_id"] = int(row["job_id"])  #< Remove hardcoded element l8r
                row["summary_vector"] = []          #< Remove hardcoded element l8r
                data.append(row)
        print(json.dumps(data[0], indent=2))
        return data

    def _load_html_schema(self, html_schema_path):
        with open(html_schema_path, 'r') as f:
            schema = json.load(f)
        return schema 

    def interact(self):
        table_data_path = self.prompt_choose('data_table', "Please choose a table")
        data = self._load_table_data(table_data_path)
        html_schema_path = self.prompt_choose('schema_html', "Please choose a html schema")
        schema = self._load_html_schema(html_schema_path)
        collection_name = self.prompt_choose('milvus', "Please choose a collection")
        self.db.load_collection(collection_name)
        asyncio.run(self._run(schema, data, collection_name))
        self.db.release_collection(collection_name)