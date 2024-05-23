from robocorp.tasks import task
from browser_manager.browser_manager import BrowserManager
from robocorp import workitems

TARGET_URL = "https://www.aljazeera.com"


@task
def list_variables():
    print("==> ", workitems.inputs)
    for item in workitems.inputs:
        print("Handling item!")
        print('--> ',item.payload["search_word"])
        print('--> ',item.payload["month_range"])

@task
def search_and_save_results():
    for item in workitems.inputs:
        search_words = item.payload["search_word"]
        month_range = item.payload["month_range"]
    browser = BrowserManager()
    browser.search_news(TARGET_URL, search_words, int(month_range))
    browser.close_browsers()

@task
def test():
    print("Hello world")