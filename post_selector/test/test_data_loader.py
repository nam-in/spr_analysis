from unittest import TestCase

from post_selector.data_loader import DataLoader


class TestDataLoader(TestCase):

    def setUp(self) -> None:
        self.loader = DataLoader()

    def test_load_query(self):
        query = self.loader.load_query()
        print(query)

    def test_load_post(self):
        posts = self.loader.load_post()
        print(posts)

    def test(self):
        posts = self.loader.load_post("post_21_02", sep="\t")
        result = posts[posts['Permalink'] == 'https://www.facebook.com/122787028507/posts/10160920625513508/']
        print(result)