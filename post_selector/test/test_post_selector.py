from unittest import TestCase

from post_selector.post_selector import PostSelector


class TestPostSelector(TestCase):

    def setUp(self) -> None:
        self.selector = PostSelector()
        self.selector.input_csv_sep = "\t"

    def test_check_posts(self):
        self.selector.check_posts(
            query_file_names=("with_galaxy_v1.31", "camera_v2.11"),
            column_names=("withGalaxy", "Camera"))
