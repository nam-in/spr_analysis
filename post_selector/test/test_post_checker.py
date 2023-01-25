from unittest import TestCase

from post_selector.data_loader import DataLoader
from post_selector.post_checker import PostChecker
from post_selector.query_parser import QueryParser


class TestPostChecker(TestCase):

    def setUp(self) -> None:
        self.checker = PostChecker()

    def test_exist(self):
        parser = QueryParser()
        self.assertTrue(self.checker.exist(parser.to_regex_word("a"), " a b c "))
        self.assertFalse(self.checker.exist(parser.to_regex_word("d"), " a b c "))
        self.assertFalse(self.checker.exist(parser.to_regex_word("a"), " aa bb cc "))
        self.assertTrue(self.checker.exist(parser.to_regex_word("a?"), " aa bb cc "))
        self.assertTrue(self.checker.exist(parser.to_regex_word("a*"), " aa bb cc "))
        self.assertTrue(self.checker.exist(parser.to_regex_word("*a"), " aa bb cc "))
        self.assertTrue(self.checker.exist(parser.to_regex_word("a*a"), " aaa bbb ccc "))
        self.assertFalse(self.checker.exist(parser.to_regex_word("a*b"), " aaa bbb ccc "))
        self.assertTrue(self.checker.exist(parser.to_regex_word("""Director's View*"""), " aaa Director's View ccc "))
        self.assertFalse(self.checker.exist([], " ccc "))
        self.assertFalse(self.checker.exist([ ], " ccc "))
        self.assertTrue(self.checker.exist([1], " ccc "))

    def test_word_to_index(self):
        result = self.checker.word_to_index("b", " a b c b ")
        print(result)
        result = self.checker.word_to_index("b c", " a b c b ")
        print(result)
        result = self.checker.word_to_index([12], " a b c ")
        print(result)

    def test_examine_near_condition(self):
        result = self.checker.examine_near_condition([['a'], ['b c']], 1, ' a b c d ')
        print("Result: ", result)

    def test_replace_query(self):
        result = self.checker.replace_query(' d "addd fdb" "dsafase" c ')
        print(result)

        # loader = DataLoader()
        # query = loader.load_query("camera_v3.1")
        # result = self.checker.replace_query(query)
        # print(result)