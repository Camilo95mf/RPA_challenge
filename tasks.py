"""Main file with tasks."""

from robocorp.tasks import task
from robocorp import workitems
from browser_manager.browser_manager import BrowserManager

TARGET_URL = "https://www.aljazeera.com"


@task
def search_and_save_results():
    """
    Search and save results from Al Jazeera website.
    """
    browser = BrowserManager()
    browser.logger.info(f"Searching results for: {TARGET_URL}")
    browser.logger.info(
        f"Filter results by category/section/topic in {TARGET_URL} is not available."
    )
    for item in workitems.inputs:
        search_words = item.payload["search_word"]
        month_range = item.payload["month_range"]
    browser.clean_output()
    browser.search_news(TARGET_URL, search_words, int(month_range))
    browser.close_browsers()
    