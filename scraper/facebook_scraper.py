import random
import re

import pandas as pd

import logging_config as log
from scraper.scraper import Scraper
from scraper.scraper_config import ScraperConfig
from utils.data_utils import DataUtils
from utils.date_utils import DateUtils
from utils.scrap_utils import ScrapUtils


class FacebookScraper(Scraper):
    """
    필요한 데이터를 불러들인다.
    """

    def __init__(self, scrap: ScrapUtils = None, max_tries=5):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = ScraperConfig()
        if scrap:
            self.scrap = scrap
        else:
            self.scrap = ScrapUtils()
        self.max_tries = max_tries
        super().__init__(self.scrap, self.logger, self.cfg)

    def get_creation_time_kst(self, ele):
        time_element = self.scrap.element("span.x4k7w5x a.x1i10hfl", parent=ele, waitable=False)
        if not time_element:
            raise Exception('Not Exists Time Element')

        self.scrap.move_to_element(time_element)
        ts = self.scrap.text("div.xu96u03", waitable=False)
        if ts == '':
            y_offset = self.scrap.execute_script("return window.pageYOffset")
            rand = random.randint(-100, 100)
            self.scrap.scroll_down(y_offset + rand)
            raise Exception('Failed to get date and time.')
        return self.to_date(ts)

    @staticmethod
    def to_date(date_str):
        date_str = DataUtils.replace_tuples(date_str, (("오전", "AM"), ("오후", "PM")))
        date_str = re.sub(".요일 ", "", date_str)
        return DateUtils.str_to_time(date_str, '%Y년 %-m월 %-d일 %p %-I:%-M')

    def scrap_row(self, ele):
        permalink = self.scrap.attr("span.x4k7w5x > a.x1i10hfl", 'href', parent=ele, waitable=False)
        self.scrap.move_to_element(ele)
        ts = self.scrap.tries(self.get_creation_time_kst, n=5, ele=ele)
        message = self.scrap.text("div[data-ad-preview='message']", parent=ele, waitable=False)
        likes = self.scrap.integer("div.x1n2onr6 div.x6s0dn4 span.xrbpyxo", parent=ele, waitable=False)
        comments = self.scrap.integer("div.x1n2onr6 > div.x6s0dn4 div.x9f619 div[aria-expanded] span.x193iq5w",
                                      parent=ele, waitable=False)
        if comments:
            shares = self.scrap.integer(
                "div.x1n2onr6 > div.x6s0dn4 > div.x9f619 > div.x9f619:nth-of-type(2) span.x4k7w5x span.x193iq5w",
                parent=ele, waitable=False)
        else:
            shares = self.scrap.integer(
                "div.x1n2onr6 > div.x6s0dn4 > div.x9f619 > div.x9f619 > span.x4k7w5x span.x193iq5w",
                parent=ele, waitable=False)
        return dict(created_time_kst=ts, message=message, post_likes=likes, post_comments=comments, post_shares=shares,
                    permalink=permalink)

    def scrap_data(self, start_time):
        data_df = pd.DataFrame()

        ended = False
        row = None
        fails = 0
        while True:
            try:
                all_elements = self.scrap.elements("div.x19h7ccj div[role='main'] > div.xh8yej3 > div.x1yztbdb")
                elements = all_elements[len(data_df.index):]
                for ele in elements:
                    row = self.scrap_row(ele)
                    if not row:
                        continue
                    if not self.greater_than_start_date(start_time, row['created_time_kst']):
                        ended = True
                        break
                    data_df = pd.concat([data_df, pd.DataFrame([row])], ignore_index=True)
                    fails = 0
                if ended:
                    break
            except Exception as e:
                fails += 1
                if fails > self.max_tries:
                    break
                self.scrap.scroll_down()
                self.logger.info(e)
                self.logger.info(f"Fail Count: {fails}, Before Element: {row}")
