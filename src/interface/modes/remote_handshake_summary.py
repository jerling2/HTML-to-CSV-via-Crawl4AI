import asyncio
import csv
import json
import re
import pickle
from ..abstracts.user_mode import UserMode
from src.utils import (
    Agent,
    normalize_markdown,
    embed_texts,
    clean_extracted_content,
    chunk_text
)
from src.systems import VectorDatabase
from crawl4ai import (
    CrawlerRunConfig,
    BrowserConfig, 
    JsonCssExtractionStrategy,
    CacheMode,
    DefaultMarkdownGenerator,
    BM25ContentFilter,
    MemoryAdaptiveDispatcher,
    RateLimiter
)


class RemoteHandshakeSummary(UserMode):

    def __init__(self):
        super().__init__()
        self.LOGIN_URL = 'https://uoregon.joinhandshake.com/login'
        self.MAX_NUM_RETRIES = 3
        self.WAIT_BETWEEN_RETRIES = 15
        self.CHUNK_SIZE = 500
        self.CHUNK_OVERLAP = 20

    async def _run(self, html_schema, metadata):
        wait_condition = """() => {
            const job_summary_container = document.querySelector('main > div > div + div + div + div');
            const button = document.querySelector('main > div > div + div + div + div button');
            const something_went_wrong = document.querySelector('section > div > button');
            const retry_later = document.querySelector('pre[style*="white-space: pre-wrap"]');
            const explore_homepage = document.querySelector('h1')?.innerText;
            if (button?.innerText === 'More') {
                // Expand the job description.
                button.click();
            } else if (button?.innerText === 'Less') {
                // The page loaded successfully.
                return true;
            } else if (job_summary_container) {
                // Job summary is short, but does exist.
                return true;
            } else if (something_went_wrong) {
                // The page is loaded, but something went wrong.
                return true;
            } else if (retry_later) {
                // The page is loaded, but handshake is throttling.
                return true;
            } else if (explore_homepage === 'Explore Homepage') {
                // "You do not have permission to view this job"
                return true;
            }
            return false;
        }
        """
        run_dispatcher = MemoryAdaptiveDispatcher(
            max_session_permit=10,
            rate_limiter=RateLimiter(
                base_delay=(1.0, 2.0),
            ),
        )
        run_extract_html_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=JsonCssExtractionStrategy(
                html_schema,
                verbose=True
            ),
            wait_for=f"js:{wait_condition}",
            delay_before_return_html=2.0,
        )
        run_generate_markdown_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            markdown_generator=DefaultMarkdownGenerator()
        )
        job_arr = [(data['job_id'], data['href']) for data in metadata.values()]
        job_map = {data['href']: data['job_id'] for data in metadata.values()}
        document_data = []
        async with Agent(login_url=self.LOGIN_URL, browser_config=BrowserConfig(headless=True)) as agent:
            document_data.append(await self._fetch_first_job(agent, job_arr[0], run_extract_html_config, run_generate_markdown_config))
            document_data.extend(await self._fetch_rest_jobs(agent, job_arr[1:], job_map, run_extract_html_config, run_generate_markdown_config, run_dispatcher))
        entities = []
        for data in document_data:
            job_id, raw_markdown = data
            entities.extend(
                self._process_document(metadata[job_id], raw_markdown)
            )
        return entities

    async def _fetch_first_job(self, agent, job, first_pass_config, second_pass_config):
        job_id, href = job
        first_pass_result = await agent.extract_from_remote(href, first_pass_config)
        if not first_pass_result.success:
            raise Exception(f"Crawl failed: {first_pass_result.error_message}")
        raw_html = json.loads(first_pass_result.extracted_content)[0]['job_summary']
        if not raw_html:
            raise Exception(f"Did not extract any content")
        second_pass_result = await agent.extract_from_raw(raw_html, second_pass_config)
        if not second_pass_result.success:
            raise Exception(f"Crawl failed: {second_pass_result.error_message}")
        return (job_id, second_pass_result.markdown)

    async def _fetch_rest_jobs(self, agent, jobs, job_map, first_pass_config, second_pass_config, dispatcher):
        __num_retries = 0
        __time_wait = 10
        __num_failed_prev = 0
        first_pass_results = []
        urls = [job[1] for job in jobs]
        crawl_results = await agent.extract_many_from_remote(urls, first_pass_config, dispatcher)
        while urls:
            urls = []
            for crawl_result in crawl_results:
                if not crawl_result.success:
                    # Catastrophic failure, do not try again.
                    print("Crawl failed:", crawl_result.error_message)
                    continue
                data = json.loads(crawl_result.extracted_content)
                if data:
                    first_pass_results.append(crawl_result)
                elif not __num_retries > self.MAX_NUM_RETRIES:
                    print(f'{crawl_result.url} failed ... retry')
                    urls.append(crawl_result.url)
                else:
                    print(f'{crawl_result.url} failed ... (reached max retries)')
            num_failed = len(urls)
            if num_failed <= __num_failed_prev:
                __num_retries += 1
            else:
                __num_retries = 0
            __num_failed_prev = num_failed
            if urls and not __num_retries > self.MAX_NUM_RETRIES:
                print(f"Waiting {self.WAIT_BETWEEN_RETRIES} seconds before trying again.")
                await asyncio.sleep(self.WAIT_BETWEEN_RETRIES)
                crawl_results = await agent.extract_many_from_remote(urls, first_pass_config, dispatcher)
        second_pass_results = []
        for first_pass_result in first_pass_results:
            job_id = job_map[first_pass_result.url]
            raw_html = json.loads(first_pass_result.extracted_content)[0]['job_summary']
            second_pass_result = await agent.extract_from_raw(raw_html, second_pass_config)
            if not second_pass_result.success:
                print(f"An error concurred during the second pass. `job_id`: {job_id}")
                continue
            second_pass_results.append((job_id, second_pass_result.markdown))
        return second_pass_results

    def _process_document(self, entity_metadata, raw_markdown):
        clean_markdown = normalize_markdown(raw_markdown)
        chunks = chunk_text(clean_markdown, chunk_size=self.CHUNK_SIZE, overlap=self.CHUNK_OVERLAP)
        vectors = embed_texts(chunks)
        results = []
        for i in range(len(chunks)):
            entity = entity_metadata.copy()
            entity['chunk_id'] = i
            entity['chunk'] = chunks[i]
            entity['summary_vector'] = vectors[i]
            results.append(entity)
        return results

    def _load_metadata(self, file_paths, table_schema):
        json_data = []
        for path in file_paths:
            with open(path, "r") as f:
                json_data.extend(json.load(f))
        entity_data = clean_extracted_content(table_schema, json_data)
        metadata = {}
        for data in entity_data:
            job_id = data['job_id']
            metadata[job_id] = data   
        return metadata

    def interact(self):
        html_schema_path = self.prompt_choose('schema_html', "Please choose a html schema")
        if not html_schema_path:
            return print("Error: No available html schemas.")
        table_schema_path = self.prompt_choose('schema_table', "Please choose a table schema")
        if not table_schema_path:
            return print("Error: No available table schemas.")
        content_path = self.prompt_choose('data_content', "Please choose a data folder")
        if not content_path:
            return print("Error: No available data folders.")
        collection_name = self.prompt_choose('milvus', "Please choose a collection")
        if not collection_name:
            return print("Error: No available collections.")
        with open(html_schema_path, 'r') as f:
            html_schema = json.load(f)
        with open(table_schema_path, "r") as f:
            table_schema = json.load(f)
        content_file_paths = self.get_paths_from_folder('data_content', content_path)
        metadata = self._load_metadata(content_file_paths, table_schema)
        entities = asyncio.run(self._run(html_schema, metadata))
        self.db.load_collection(collection_name)
        self.db.insert(collection_name, entities)
        self.db.release_collection(collection_name)