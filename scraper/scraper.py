from abc import ABC, abstractmethod

import pandas as pd
import pytz

from utils.date_utils import DateUtils


class Scraper(ABC):
    """
    필요한 데이터를 불러들인다.
    """

    def __init__(self, scrap, logger, cfg):
        self.logger = logger
        self.cfg = cfg
        self.scrap = scrap

    @abstractmethod
    def scrap_row(self, ele):
        pass

    def greater_than_start_date(self, start_time, created_time):
        s_time = DateUtils.str_to_time(start_time, '%Y-%m-%d %H:%M').replace(tzinfo=pytz.UTC)
        c_time = created_time.replace(tzinfo=pytz.UTC)
        self.logger.debug(f"Start Time: {start_time}, Created Time: {created_time}")
        return s_time <= c_time

    @abstractmethod
    def scrap_data(self, url, start_time):
        pass
