from robocorp.tasks import task
from browser_manager.browser_manager import BrowserManager
from robocorp import workitems

TARGET_URL = "https://www.aljazeera.com"


@task
def search_and_save_results():
    print(f"Searching results for: {TARGET_URL}")
    print(f"filter results by category/section/topic in {TARGET_URL} is not available.")
    for item in workitems.inputs:
        search_words = item.payload["search_word"]
        month_range = item.payload["month_range"]
    browser = BrowserManager()
    browser.search_news(TARGET_URL, search_words, int(month_range))
    browser.close_browsers()
