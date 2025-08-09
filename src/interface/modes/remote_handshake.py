import asyncio
import json
import re
import math
from ..abstracts.user_mode import UserMode
from .json_to_tsv_mode import ConvertJsonToTSVMode
from crawl4ai import CrawlerRunConfig, BrowserConfig, JsonCssExtractionStrategy, CacheMode
from src.utils import Agent


class RemoteHandshake(UserMode):

    def __init__(self):
        super().__init__()
        self.LOGIN_URL = 'https://uoregon.joinhandshake.com/login'
        self.TARGET_URL = 'https://uoregon.joinhandshake.com/saved-jobs'
        self.JOBS_PER_PAGE = 10
        self.MAX_NUM_RETRIES = 5

    async def _process_first_saved_job_page(self, agent, run_config):
        FAIL = (None, None)
        result = await agent.extract_from_remote(self.TARGET_URL, run_config)
        if not result.success:
            print("Crawl failed:", result.error_message)
            return FAIL
        extracted_content = json.loads(result.extracted_content)
        if not extracted_content:
            print("No saved jobs extracted ... (reached max retries)")
            return FAIL
        header_text = extracted_content[0].get('header', "")
        re_match = re.search(r'\d+', header_text)
        if not re_match:
            print(f'Could not match digits in: "{header_text}"')
            return FAIL
        num_jobs = int(re_match.group())
        num_pages = math.ceil(num_jobs / self.JOBS_PER_PAGE)
        return (extracted_content, num_pages)

    async def _process_rest_saved_job_pages(self, agent, urls, run_config):
        results = await agent.extract_many_from_remote(urls, run_config)
        json_data = []
        __num_retries = 0
        while urls:
            __reached_max_retries = __num_retries > self.MAX_NUM_RETRIES
            urls = []
            for result in results:
                if not result.success:
                    # Catastrophic failure, do not try again.
                    print("Crawl failed:", result.error_message)
                    continue
                data = json.loads(result.extracted_content)
                if data:
                    json_data.append(data)
                elif not __reached_max_retries:
                    print(f'{result.url} failed ... retry')
                    urls.append(result.url)
                else:
                    print(f'{result.url} failed ... (reached max retries)')
            __num_retries += 1
            results = await agent.extract_many_from_remote(urls, run_config)
        return json_data

    async def _run(self, schema, content_out_folder):
        wait_condition = """() => {
            const header = document.querySelector('main > div > h1')?.innerHTML;
            if (header) {
                // The page loaded successfully.
                return true;
            }
            const something_went_wrong = document.querySelector('section > div > button');
            if (something_went_wrong) {
                // The page is loaded, but something went wrong.
                return true
            }
            // Otherwise, wait for the page to load.
            return false;
        """
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            delay_before_return_html=5.0,
            wait_for=f"js:{wait_condition}", 
            extraction_strategy = JsonCssExtractionStrategy(
                schema, 
                verbose=True
            )
        )
        async with Agent(login_url=self.LOGIN_URL, browser_config=BrowserConfig(headless=True)) as agent:
            """
            IMPORTANT: Logically, agent should be a persistent context. However, in practice, agent is only a
            persistent context if the same run configuration is used. This could be a bug with C4A 0.7.2.
            I see two potential solutions: 1) use the same run_config for crawl sessions that indend to share
            the same context, or 2) modify the LoginProcedure to manually save & restore cookies. 
            """
            json_data = []
            initial_extracted_content, num_pages = await self._process_first_saved_job_page(agent, run_config)
            if (initial_extracted_content, num_pages) == (None, None):
                return False
            json_data.append(initial_extracted_content)
            saved_jobs_urls = [f'{self.TARGET_URL}?page={i}' for i in range(2, num_pages + 1)]
            rest_json_data = await self._process_rest_saved_job_pages(agent, saved_jobs_urls, run_config)
            json_data.extend(rest_json_data)
            for index, page_content in enumerate(json_data):
                out_path = self.get_path('data_content', file_name=f'page_{index}', dir_name=content_out_folder)
                with open(out_path, 'w') as f:
                    json.dump(page_content, f, indent=2)
            return True

    def interact(self):
        html_schema_path = self.prompt_choose('schema_html', "Please choose a html schema")
        content_out_path = self.prompt_enter('data_content', "Please enter a name for the output folder")
        content_out_folder = self.get_basename(content_out_path)
        if not html_schema_path:
            return print("No available html schemas.")
        with open(html_schema_path, 'r') as f:
            schema = json.load(f)
        result = asyncio.run(self._run(schema, content_out_folder))
        if result and input('Continue to table [y]? ') == "y":
            program = ConvertJsonToTSVMode()
            program.interact(content_data_path=content_out_path)
