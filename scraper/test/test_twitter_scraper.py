from unittest import TestCase

from scraper.data_scraper import DataScraper
from scraper.twitter_scraper import TwitterScraper
from utils.data_utils import DataUtils


class TestDataScraper(TestCase):

    def test_scrap_data(self):
        scraper = TwitterScraper()
        links_df = DataUtils.read(scraper.cfg.data_dir / 'account_links.xlsx')
        url = links_df.loc[2, 'Link']
        scraper.scrap_data(url, "2023-01-27 01:00")
