import pandas as pd

import logging_config as log
from scraper.scraper import Scraper
from scraper.scraper_config import ScraperConfig
from utils.data_utils import DataUtils
from utils.date_utils import DateUtils
from utils.scrap_utils import ScrapUtils

# %%
cfg = ScraperConfig()
scrap = ScrapUtils()
# %%
links_df = DataUtils.read(cfg.data_dir / 'account_links.xlsx')
# %%
class TwitterScraper(Scraper):

    def __init__(self, scrap: ScrapUtils = None):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = ScraperConfig()
        if scrap:
            self.scrap = scrap
        else:
            self.scrap = ScrapUtils()
        super().__init__(self.scrap, self.logger, self.cfg)

    def to_date(self, date_str):
        dt = DateUtils.str_to_time(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        dt = dt.astimezone()
        return dt

    def scrap_row(self, ele):
        ts = self.scrap.attr("time", "datetime", parent=ele, waitable=False)
        ts_kst = self.to_date(ts)
        message = self.scrap.text("div[data-testid='tweetText']", parent=ele, waitable=False)
        likes = self.scrap.integer("div[data-testid='like']", "aria-label", parent=ele, waitable=False)
        comments = self.scrap.integer("div[data-testid='reply']", "aria-label", parent=ele, waitable=False)
        shares = self.scrap.integer("div[data-testid='retweet']", "aria-label", parent=ele, waitable=False)
        reaches = self.scrap.integer("a[aria-label$='트윗 애널리틱스 보기']", 'aria-label', parent=ele, waitable=False)
        if not reaches:
            reaches = self.scrap.integer("a[aria-label$='View Tweet analytics']", 'aria-label', parent=ele, waitable=False)
        permalink = self.scrap.attr("div.r-1q142lx a", "href", parent=ele, waitable=False)
        row = dict(created_time_utc=ts, created_time_kst=ts_kst, message=message, post_likes=likes,
                   post_comments=comments, post_shares=shares, post_reach=reaches, permalink=permalink)
        return row

    def scrap_data(self, start_time, max_tries=5, max_less=5):
        data_df = pd.DataFrame()

        ended = False
        row = None
        fails = 0
        less_cnt = 0
        while True:
            try:
                all_elements = self.scrap.elements("section[aria-labelledby='accessible-list-1'] div[data-testid='cellInnerDiv']")
                for ele in all_elements:
                    row = self.scrap_row(ele)
                    if not row:
                        continue
                    if not data_df.empty and row['permalink'] in data_df['permalink'].values:
                        continue
                    if not self.greater_than_start_date(start_time, row['created_time_kst']):
                        less_cnt += 1
                        if less_cnt > max_less:
                            ended = True
                            break
                        continue
                    data_df = pd.concat([data_df, pd.DataFrame([row])], ignore_index=True)
                    fails = 0
                if ended:
                    break
                y_offset = scrap.execute_script("return window.pageYOffset")
                size = self.scrap.driver.get_window_size()
                height = size.get("height")
                scrap.scroll_down(y_offset + height)
            except Exception as e:
                fails += 1
                if fails > max_tries:
                    break
                self.scrap.scroll_down()
                self.logger.info(e)
                self.logger.info(f"Fail Count: {fails}, Before Element: {row}")
        return data_df


# %%
scraper = TwitterScraper(scrap)

#%%
twitter_url = links_df.loc[2, 'Link']
scraper.scrap.go(twitter_url)

#%%
data_df = scraper.scrap_data('2023-01-25 01:00')
print(data_df)
#%%


#%%
data_df['created_time_kst'] = data_df['created_time_kst'].dt.tz_localize(None)
DataUtils.save(data_df, scraper.cfg.results_dir / 'twitter.xlsx')

#%%
scraper.scrap.quit()
