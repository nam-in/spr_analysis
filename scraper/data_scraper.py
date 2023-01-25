import logging_config as log
from scraper.scraper_config import ScraperConfig


class DataScraper:

    def __init__(self):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = ScraperConfig()
