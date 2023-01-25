import os
import sys
from pathlib import Path

from utils.date_utils import DateUtils


class Config:

    def __init__(self):
        self.today = DateUtils.get_today_str()

    @property
    def root_dir(self):
        if getattr(sys, 'frozen', False):
            return Path(os.path.dirname(sys.executable))
        else:
            return Path(os.path.abspath(__file__)).parent

    @property
    def data_dir(self):
        return self.root_dir / 'data'

    @property
    def results_dir(self):
        return self.root_dir / 'results'

