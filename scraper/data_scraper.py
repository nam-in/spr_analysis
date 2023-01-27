import pandas as pd
from tqdm import tqdm

import logging_config as log
from post_selector.post_selector import PostSelector
from scraper.facebook_scraper import FacebookScraper
from scraper.scraper_config import ScraperConfig
from scraper.twitter_scraper import TwitterScraper
from scraper.youtube_scraper import YoutubeScraper
from utils.data_utils import DataUtils
from utils.scrap_utils import ScrapUtils


class DataScraper:

    def __init__(self, scrapable=True):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = ScraperConfig()
        if scrapable:
            self.scrap = ScrapUtils()

    def scrap_account_data(self, channel, account, link, start_time):

        account_df = None
        if channel == 'Facebook':
            scraper = FacebookScraper(self.scrap)
            account_df = scraper.scrap_data(link, start_time)
        elif channel == 'Twitter':
            scraper = TwitterScraper(self.scrap)
            account_df = scraper.scrap_data(link, start_time)
        elif channel == 'YouTube':
            scraper = YoutubeScraper(self.scrap)
            account_df = scraper.scrap_data(link, start_time)

        if account_df is not None and not account_df.empty:
            account_df['channel'] = channel
            account_df['account'] = account
            account_df['created_time_kst'] = account_df['created_time_kst'].dt.tz_localize(None)
        return account_df

    def scrap_data(self, start_time):
        links_df = DataUtils.read(self.cfg.data_dir / 'account_links.xlsx')
        data_df = pd.DataFrame()
        for row in tqdm(links_df.itertuples(), total=len(links_df.index), desc="Scraping"):
            channel = getattr(row, 'Channel')
            account = getattr(row, 'Account')
            link = getattr(row, 'Link')
            account_df = self.scrap_account_data(channel, account, link, start_time)
            if account_df is not None and not account_df.empty:
                data_df = pd.concat([data_df, account_df], ignore_index=True)

        file_path = f'mx_pr_sns_scraped_{self.cfg.today}.xlsx'
        DataUtils.save(data_df, self.cfg.results_dir / file_path, index=False)
        data_df = self.add_samsung_classification(data_df)
        return data_df

    def add_samsung_classification(self, data_df):
        selector = PostSelector()
        samsung_yn_df = selector.check_posts(query_file_names=("samsung_v1.0",), column_names=("samsung_yn",),
                                             posts=data_df[['message']])
        data_df = data_df.merge(samsung_yn_df, how="left", left_index=True, right_index=True)
        file_path = f'mx_pr_sns_classed_{self.cfg.today}.xlsx'
        data_df['total_engagements'] = data_df[['post_likes', 'post_comments', 'post_shares']].sum(axis=1)
        data_df = data_df[
            ['channel', 'created_time_kst', 'created_time_utc', 'before', 'account', 'post_likes', 'post_comments',
             'post_shares', 'total_engagements', 'post_reach', 'message', 'permalink', 'samsung_yn']]
        DataUtils.save(data_df, self.cfg.results_dir / file_path, index=False)
        return data_df
