"""Module with class to search and create outputs."""

import re
import logging
import datetime
import urllib.request
import os
import time

from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from selenium.webdriver.common.by import By
from dateutil.relativedelta import relativedelta

class BrowserManager():
    """Class with all methods to solve the challenge."""
    def __init__(self) -> None:
        self.selenium = Selenium()
        self.money_pattern = r"\$\d+(,\d{3})*(\.\d+)?\s*(dollars|USD)?"
        self.output_path = "./output"
        self.rpa_excel = Files()
        self.report_data = []
        self.images_urls = []
        logging.basicConfig()
        logging.root.setLevel(logging.NOTSET)
        logging.basicConfig(level=logging.NOTSET)
        self.logger = logging.getLogger(__name__)

    def clean_output(self):
        """Clear imeges from output folder"""
        self.logger.info(f"Cleaning output images folder: {self.output_path}")
        for filename in os.listdir(self.output_path):
            file_path = os.path.join(self.output_path, filename)
            if os.path.isfile(file_path) and ("jpg" in file_path):
                os.remove(file_path)

    def parse_date(self, raw_date:str) -> datetime.date:
        """Parse string to date object."""
        if ("days ago" in raw_date) or ("day ago" in raw_date):
            past_days = raw_date.split(" ")[0].strip()
            date = datetime.date.today() - datetime.timedelta(days=int(past_days))
        elif "ago" in raw_date:
            past_days = raw_date.split(" ")[0].strip()
            date = datetime.date.today()
        else:
            date = datetime.datetime.strptime(raw_date, "%b %d, %Y").date()

        return date

    def create_report(self, search_word:str, search_results:list, limit_date:datetime.date):
        """Process results and create output file."""
        for index, article in enumerate(search_results):
            current_article = article.text.split("\n")
            title = current_article[0]
            raw_date = current_article[1].split("...")[0].strip()
            description= " ".join(current_article[1].split("...")[1:]).strip()
            counter = title.lower().count(search_word.lower().strip()) + description.lower().count(search_word.lower().strip())
            contain_money_flag = True if re.search(self.money_pattern, title) or re.search(self.money_pattern, description) else False
            date = self.parse_date(raw_date)
            img_url = article.find_element(By.TAG_NAME, "img").get_attribute('src')
            new_row = {
                "title": title,
                "date": date,
                "description": description,
                "picture_filename": f"{self.output_path}/{index}.jpg",
                "count_search_word": counter,
                "money_flag": contain_money_flag
            }
            if date > limit_date:
                self.report_data.append(new_row)
                self.images_urls.append({
                    "img_url":img_url,
                    "picture_filename": new_row["picture_filename"]
                })

    def download_images(self):
        """Download images associated with articles."""
        if len(self.images_urls) > 0:
            for idx,img_data in enumerate(self.images_urls):
                if idx > 50:
                    self.logger.info("The download of 50 images has been exceeded.")
                    break
                urllib.request.urlretrieve(img_data["img_url"], img_data["picture_filename"])
        else:
            self.logger.error("Call create_report first.")

    def search_news(self, url:str, search_word:str, month_range:int):
        """Open Chrome and search target url."""
        try:
            self.logger.info(f"Opening chrome in url: {url}")
            self.selenium.open_chrome_browser(url=url, maximized=True)
            self.selenium.click_element_if_visible('//*[@id="onetrust-accept-btn-handler"]')
            self.selenium.click_element_when_visible("class=site-header__search-trigger")
            self.logger.info(f"Searching news related with: {search_word}")
            self.selenium.input_text_when_element_is_visible("class=search-bar__input", text=search_word)
            self.selenium.press_keys("class=search-bar__input", "ENTER")
            self.logger.info("Filtering news by date.")
            self.selenium.wait_until_element_is_visible("class=search-summary__select", timeout=20)
            self.selenium.click_element_when_visible("class=search-summary__select")
            self.selenium.click_element_when_visible('//*[@id="search-sort-option"]/option[1]')
            self.logger.info("Getting all results.")
            self.selenium.wait_until_element_is_visible("class=search-result__list", timeout=20)
            article_elements = self.selenium.find_elements("tag=article")
            if month_range > 1:
                limit_date = datetime.date.today() - relativedelta(months=month_range)
                limit_date = limit_date.replace(day=1)
            else:
                limit_date = datetime.date.today().replace(day=1)

            if len(article_elements) > 0:
                last_article_result = article_elements[-1]
                raw_date = last_article_result.text.split("\n")[1].split("...")[0].strip()
                last_date = self.parse_date(raw_date)

                while last_date > limit_date:
                    self.selenium.wait_until_element_is_visible('//*[@id="main-content-area"]/div[2]/div[2]/button')
                    self.selenium.execute_javascript("document.querySelector('.show-more-button').scrollIntoView();")
                    self.selenium.click_element_when_visible('//*[@id="main-content-area"]/div[2]/div[2]/button')
                    article_elements = self.selenium.find_elements("tag=article")
                    last_article_result = article_elements[-1]
                    raw_date = last_article_result.text.split("\n")[1].split("...")[0].strip()
                    last_date = self.parse_date(raw_date)
                
                self.selenium.wait_until_element_is_visible('//*[@id="main-content-area"]/div[2]/div[2]/button')
                article_elements = self.selenium.find_elements("tag=article")
                self.create_report(search_word, article_elements, limit_date)
                self.export_report()
            else:
                self.logger.warning(f"No search results found for: {search_word}")

        except Exception as err:
            self.logger.error(f"Error executing bot: {str(err)}")

    def export_report(self):
        """export report and output files."""
        if len(self.report_data) > 0:
            self.logger.info("Exporting processed results.")
            self.download_images()
            report = self.rpa_excel.create_workbook(
                                                f"{self.output_path}/search_result.xlsx",
                                                sheet_name="default"
                                            )
            self.rpa_excel.create_worksheet(name="Results",content=self.report_data,header=True)
            report.remove_worksheet("default")
            self.rpa_excel.save_workbook()
        else:
            self.logger.error("Call create_report function first.")

    def close_browsers(self) -> None:
        """Close all opened browsers."""
        self.logger.info("Ending process, closing browser.")
        self.selenium.close_browser()
