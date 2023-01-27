import re

import pandas as pd

import logging_config as log
from scraper.scraper import Scraper
from scraper.scraper_config import ScraperConfig
from utils.date_utils import DateUtils
from utils.scrap_utils import ScrapUtils


class YoutubeScraper(Scraper):

    def __init__(self, scrap: ScrapUtils = None):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = ScraperConfig()
        if scrap:
            self.scrap = scrap
        else:
            self.scrap = ScrapUtils()
        super().__init__(self.scrap, self.logger, self.cfg)

    def scrap_date(self):
        date_str = self.scrap.text("div#info-strings yt-formatted-string.ytd-video-primary-info-renderer")
        dt = DateUtils.str_to_time(date_str, "%Y. %m. %d.")
        return dt

    def scrap_message(self):
        self.scrap.click("tp-yt-paper-button#expand")
        message = self.scrap.text("ytd-text-inline-expander#description-inline-expander > yt-formatted-string")
        return message

    def scrap_row(self, row):
        self.scrap.go(row['permalink'])
        self.scrap.scroll_down()
        likes = self.scrap.integer("div#segmented-like-button span[role='text']")
        comments = self.scrap.integer("h2#count yt-formatted-string.ytd-comments-header-renderer")
        date = self.scrap_date()
        message = row['title'] + "\n " + self.scrap_message()
        del row['title']
        row.update(post_likes=likes, post_comments=comments, created_time_kst=date, message=message)
        return row

    def scrap_category(self, url, category, start_time):
        data_df = pd.DataFrame()
        data = self.scrap_list(f"{url}/{category}")
        for row in data:
            row = self.scrap_row(row)
            if not self.greater_than_start_date(start_time, row['created_time_kst']):
                break
            data_df = pd.concat([data_df, pd.DataFrame([row])], ignore_index=True)
        return data_df

    def scrap_data(self, url, start_time):
        video_df = self.scrap_category(url, 'videos', start_time)
        live_df = self.scrap_category(url, 'streams', start_time)
        data_df = pd.concat([video_df, live_df])
        return data_df

    def get_views(self, ele):
        desc = self.scrap.attr("a#video-title-link", "aria-label", parent=ele, waitable=False)
        views = re.search("조회수 ([0-9,]+)회", desc).groups()[0]
        return int(views.replace(',', ''))

    def scrap_row_for_list(self, ele):
        title = self.scrap.text("yt-formatted-string#video-title", parent=ele, waitable=False)
        link = self.scrap.attr("a#video-title-link", "href", parent=ele, waitable=False)
        views = self.get_views(ele)
        before = self.scrap.text("div#metadata-line > span:nth-of-type(2)", parent=ele, waitable=False)
        return dict(title=title, permalink=link, post_reach=views, before=before)

    def scrap_list(self, url):
        self.scrap.go(url)
        self.scrap.scroll_down()
        data = []
        for ele in self.scrap.elements("div#contents ytd-rich-item-renderer"):
            row = self.scrap_row_for_list(ele)
            before_unit = re.search("[0-9]+(.+) 전", row['before']).groups()[0]
            if before_unit == '개월':
                break
            data.append(row)
        return data

    def scrap_lists(self, url):
        data = []
        video_data = self.scrap_list(f"{url}/videos")
        data.extend(video_data)
        live_data = self.scrap_list(f"{url}/streams")
        data.extend(live_data)
        return data
