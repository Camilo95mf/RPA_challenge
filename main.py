from browser_manager.browser_manager import BrowserManager


if __name__ == "__main__":
    browser = BrowserManager()
    browser.search_news("https://www.aljazeera.com", "dollar", 1)
    browser.close_browsers()