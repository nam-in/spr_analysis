import re

import pandas as pd
from tqdm import tqdm

import logging_config as log
from scraper.scraper import Scraper
from scraper.scraper_config import ScraperConfig
from utils.data_utils import DataUtils
from utils.date_utils import DateUtils
from utils.scrap_utils import ScrapUtils


# %%
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
        likes = scrap.integer("div#segmented-like-button span[role='text']")
        comments = scrap.integer("h2#count yt-formatted-string.ytd-comments-header-renderer")
        date = self.scrap_date()
        message = row['title'] + "\n " + self.scrap_message()
        del row['title']
        row.update(post_likes=likes, post_comments=comments, created_time_kst=date, message=message)
        return row

    def scrap_data(self, url, start_time):
        data_df = pd.DataFrame()
        data = self.scrap_lists(url)
        for row in tqdm(data, desc="Scrap details"):
            row = self.scrap_row(row)
            data_df = pd.concat([data_df, pd.DataFrame([row])], ignore_index=True)
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
        return dict(title=title, permalink=link, video_view=views, before=before)

    def scrap_list(self, url):
        self.scrap.go(url)
        scrap.scroll_down()
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


# %%
cfg = ScraperConfig()
scrap = ScrapUtils()
# %%
scraper = YoutubeScraper(scrap)

# %%
links_df = DataUtils.read(cfg.data_dir / 'account_links.xlsx')
youtube_url = links_df.loc[3, 'Link']
scraper.scrap.go(youtube_url)
# %% 동영상
scraper.scrap_lists(youtube_url)
# %%
likes = scrap.integer("div#segmented-like-button span[role='text']")
#%%
scrap.integer("h2#count yt-formatted-string.ytd-comments-header-renderer")
#%%
scrap.text("div#info-strings yt-formatted-string.ytd-video-primary-info-renderer")
#%%
date_str = scrap.text("div#info-strings yt-formatted-string.ytd-video-primary-info-renderer")
dt = DateUtils.str_to_time(date_str, "%Y. %m. %d.")
print(dt)
#%%
scrap.click("tp-yt-paper-button#expand")
message = scrap.text("ytd-text-inline-expander#description-inline-expander > yt-formatted-string")
print(message)
# %%
scrap.scroll_down()
# %%


# %%
data_df = scraper.scrap_data('2023-01-25 01:00')
print(data_df)
# %%
re.search("조회수 ([0-9,]+)회", "4초 조회수 7,683회").groups()

# %%
data_df['created_time_kst'] = data_df['created_time_kst'].dt.tz_localize(None)
DataUtils.save(data_df, scraper.cfg.results_dir / 'twitter.xlsx')

# %%
scraper.scrap.quit()
