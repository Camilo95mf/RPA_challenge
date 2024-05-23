# from robocorp.tasks import task
from robocorp.tasks import task
from browser_manager.browser_manager import BrowserManager
# from RPA.Robocorp.WorkItems import WorkItems
from robocorp import workitems

TARGET_URL = "https://www.aljazeera.com"


@task
def list_variables():
    # library = WorkItems()
    # library.get_input_work_item()

    # variables = library.get_work_item_variables()
    # print(len(variables.items()))
    # print(variables.items())
    # for variable, value in variables.items():
    #     print("%s = %s", variable, value)
    print("==> ", workitems.inputs)
    for item in workitems.inputs:
        print("Handling item!")
        print('--> ',item.payload)

@task
def search_and_save_results():
    browser = BrowserManager()
    browser.search_news(TARGET_URL, "dollar", 1)
    browser.close_browsers()

@task
def test():
    print("Hello world")