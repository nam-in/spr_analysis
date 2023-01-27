from unittest import TestCase

from scraper.data_scraper import DataScraper
from utils.data_utils import DataUtils


class TestDataScraper(TestCase):

    def test_scrap_data(self):
        scraper = DataScraper()
        scraper.scrap_data("2023-01-27 00:00")

    def test_add_samsung_classification(self):
        scraper = DataScraper(scrapable=False)
        data_df = DataUtils.read(scraper.cfg.results_dir / 'mx_pr_sns_scraped_2023-01-27.xlsx')
        scraper.add_samsung_classification(data_df)