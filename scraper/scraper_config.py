from config import Config


class ScraperConfig(Config):

    def __init__(self):
        super().__init__()
        self.name = 'scraper'

    @property
    def data_dir(self):
        return self.root_dir / self.name / 'data'

    @property
    def results_dir(self):
        return self.root_dir / self.name / 'results'
