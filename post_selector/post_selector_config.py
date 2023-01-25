from config import Config


class PostSelectorConfig(Config):

    def __init__(self):
        super().__init__()
        self.name = 'post_selector'

    @property
    def data_dir(self):
        return self.root_dir / self.name / 'data'

    @property
    def results_dir(self):
        return self.root_dir / self.name / 'results'

    @property
    def query_dir(self):
        return self.data_dir / 'query'

    @property
    def run_dir(self):
        return self.data_dir / 'post' / 'run_file'

