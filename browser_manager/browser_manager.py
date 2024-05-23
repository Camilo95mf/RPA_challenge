from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.by import By
import re
import logging
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import urllib.request
import os
import time

class BrowserManager():
    def __init__(self) -> None:
        self.selenium = Selenium()
        self.MONEY_PATTERN = r"\$\d+(,\d{3})*(\.\d+)?\s*(dollars|USD)?"
        self.COLUMNS = ["title", "date", "description", "picture_filename", "count_search_word", "money_flag"]
        self.OUTPUT_PATH = "./output"
        self.output_df = pd.DataFrame(columns=self.COLUMNS)
    
    def clean_output(self):
        logging.info(f"Cleaning output imegs folder: {self.OUTPUT_PATH}")
        for filename in os.listdir(self.OUTPUT_PATH):
            file_path = os.path.join(self.OUTPUT_PATH, filename)
            if os.path.isfile(file_path) and file_path.__contains__("jpg"):
                os.remove(file_path)

    def parse_date(self, raw_date:str) -> datetime.date:
        """Parse string to date object."""
        if raw_date.__contains__("days ago") or raw_date.__contains__("day ago"):
            past_days = raw_date.split(" ")[0].strip()
            date = datetime.date.today() - datetime.timedelta(days=int(past_days))
        elif raw_date.__contains__("ago"):
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
            contain_money_flag = True if re.search(self.MONEY_PATTERN, title) or re.search(self.MONEY_PATTERN, description) else False

            date = self.parse_date(raw_date)

            img_url = article.find_element(By.TAG_NAME, "img").get_attribute('src')    

            new_row = {
                "title": title,
                "date": date,
                "description": description,
                "picture_filename": f"{self.OUTPUT_PATH}/{index}.jpg",
                "count_search_word": counter,
                "money_flag": contain_money_flag,
                "img_url": img_url
            }
    
            self.output_df = pd.concat([self.output_df, pd.DataFrame([new_row])], ignore_index=True)
    
        logging.info("Filtering results by date.")
        self.output_df = self.output_df[self.output_df['date'] > limit_date]
        

    def download_images(self):
        """Download images associated with articles."""
        if len(self.output_df.index) > 0:
            for _, row in self.output_df.iterrows():
                urllib.request.urlretrieve(row['img_url'], row["picture_filename"])
        else:
            logging.error("Call create_report first.")



    def search_news(self, url:str, search_word:str, month_range:int):
        """Open Chrome and search target url."""
        try:
            logging.info(f"Opening chrome in url: {url}")
            self.selenium.open_chrome_browser(url=url, maximized=True)
            self.selenium.click_element_if_visible('//*[@id="onetrust-accept-btn-handler"]')
            self.selenium.click_element_when_visible("class=site-header__search-trigger")
            logging.info(f"Searching news related with: {search_word}")
            self.selenium.input_text_when_element_is_visible("class=search-bar__input", text=search_word)
            self.selenium.press_keys("class=search-bar__input", "ENTER")
            logging.info("Filtering news by date.")
            self.selenium.wait_until_element_is_visible("class=search-summary__select", timeout=20)
            self.selenium.click_element_when_visible("class=search-summary__select")
            self.selenium.click_element_when_visible('//*[@id="search-sort-option"]/option[1]')
            logging.info("Getting all results.")
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
                    self.selenium.execute_javascript("document.querySelector('.show-more-button').scrollIntoView();")
                    self.selenium.click_element_when_visible('//*[@id="main-content-area"]/div[2]/div[2]/button')
                    article_elements = self.selenium.find_elements("tag=article")
                    last_article_result = article_elements[-1]
                    raw_date = last_article_result.text.split("\n")[1].split("...")[0].strip()
                    last_date = self.parse_date(raw_date)
                    time.sleep(5)

                time.sleep(10)
                article_elements = self.selenium.find_elements("tag=article")
                self.create_report(search_word, article_elements, limit_date)
                self.export_report()
            else:
                logging.warning("No search results found for: ", search_word)

        except Exception as err:
            logging.error("Error executing bot: "+str(err))

    def export_report(self):
        """export report and output files."""
        if len(self.output_df.index) > 0:
            logging.info("Exporting processed results.")
            self.download_images()
            self.output_df.drop(columns=['img_url'], inplace=True)
            self.output_df.to_excel(f"{self.OUTPUT_PATH}/search_result.xlsx", sheet_name="Results", index=False)
        else:
            logging.error("Call create_report first.")

    def close_browsers(self) -> None:
        """Close all opened browsers."""
        logging.info("Ending process, closing browser.")
        self.selenium.close_browser()