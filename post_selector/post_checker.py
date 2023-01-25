import re

import logging_config as log
from utils.data_utils import DataUtils


class PostChecker:
    """
    포스트가 "query"의 패턴과 일치하는지 체크한다.
    """

    def __init__(self):
        self.logger = log.get_logger(self.__class__.__name__)
        self.__SPACE = re.compile('\s+')
        self.__SPACE_SEP = "_|_"

    def check_post(self, post, query, preprocess_post=False):
        """
        포스트가 "query"의 패턴과 일치하는지 체크한다.
        :param query: 정의된 패턴
        :param post: 포스트 데이터
        :param preprocess_post: 포스트 데이터를 전처리 했는지 여무
        :return:
        """
        if preprocess_post is False:
            post = self.preprocess_post(post)

        result = self.examine_conditions(query, post)
        return 'Y' if result else 'N'

    def check_post_for_queries(self, post, queries, columns=None):
        """
        포스트가 "query"의 패턴과 일치하는지 체크한다.
        :param post: 포스트 데이터
        :param queries: 정의된 패턴들
        :param columns: 컬럼 명들
        :return:
        """
        if columns is None:
            columns = queries

        post = self.preprocess_post(post)
        values = {}
        for query, column in zip(queries, columns):
            values[column] = self.check_post(post, query, True)
        return values

    def preprocess_post(self, post):
        if not isinstance(post, str):
            post = str(post)
        post = self.replace_text(post)
        return " " + self.__SPACE.sub(" ", post.strip().lower()) + " "

    def examine_conditions(self, query, post):
        """
        쿼리의 조건들을 조사한다.
        :param query: 정의된 패턴
        :param post: 포스트 데이터
        :return:
        """
        if isinstance(query, str):
            return self.exist(query, post)

        operator = query["operator"]
        operands = query["operands"]
        if operator == 'OR':
            result = self.examine_or_condition(operands, post)
        elif operator == 'AND':
            result = self.examine_and_condition(operands, post)
        elif operator == 'NOT':
            result = self.examine_not_condition(operands, post)
        elif operator == 'NEAR':
            result_idx = self.examine_near_condition(operands, query['distance'], post)
            result = len(result_idx) > 0
        else:
            result = self.exist(operands[0], post)
        return result

    @staticmethod
    def split_query(operation, query):
        """
        쿼리를 조건에 해당하는 함수에 의해 분리한다.
        :param operation: 조건에 해당하는 함수
        :param query: 정의된 패턴
        :return:
        """
        words = operation.split(query)
        words = [word.strip().lower() for word in words]
        return words

    def examine_or_condition(self, or_words, post):
        """
        OR 조건
        :param or_words: OR 조건의 단어들
        :param post: 포스트 데이터
        :return:
        """
        for word in or_words:
            if self.exist(word, post):
                return True
        return False

    def examine_and_condition(self, and_words, post):
        """
        AND 조건
        :param and_words: AND 조건의 단어들
        :param post: 포스트 데이터
        :return:
        """
        for word in and_words:
            if not self.exist(word, post):
                return False
        return True

    def examine_not_condition(self, not_words, post):
        """
        NOT 조건
        :param not_words: NOT 조건의 단어들
        :param post: 포스트 데이터
        :return:
        """
        exist_word = not_words[0]
        not_word = not_words[1]
        if self.exist(exist_word, post) and not self.exist(not_word, post):
            return True
        return False

    def examine_near_condition(self, near_ops, near_num, post):
        """
        NEAR 조건
        :param near_ops: NEAR 피연산자
        :param near_num: NEAR 수
        :param post: 포스트 데이터
        :return:
        """
        near_op1 = near_ops[0]
        near_op2 = near_ops[1]
        indexes = []
        op1_indexes = self.words_to_index(near_op1, post)
        op2_indexes = self.words_to_index(near_op2, post)
        for op1_index in op1_indexes:
            for op2_index in op2_indexes:
                if op1_index - near_num - 1 <= op2_index <= op1_index + near_num + 1:
                    min_index = min(op1_index, op2_index)
                    max_index = max(op1_index, op2_index)
                    for i in range(min_index, max_index + 1):
                        indexes.append(i)
                    break
        return list(set(indexes))

    def words_to_index(self, words, post):
        """
        NEAR 조건에 해당하는 단어들에 대한 index 를 구한다.
        :param words: NEAR 조건에 해당하는 단어들
        :param post: 포스트 데이터
        :return: 단어들의 index 들
        """
        indexes = []
        for word in words:
            idx = self.word_to_index(word, post)
            indexes.extend(idx)
        return indexes

    def word_to_index(self, word, post):
        """
        단어에 매칭되는 포스트의 index 를 구한다.
        :param word: 단어
        :param post: 포스트 데이터
        :return: 단어에 매칭되는 포스트의 index 들
        """
        if isinstance(word, list):
            return word

        indexes = []
        word_len = word.count(" ")
        finds = re.finditer(word, post)
        for r in finds:
            index = post[:r.start()].count(' ')
            for i in range(word_len + 1):
                indexes.append(index + i)
        return indexes

    @staticmethod
    def strip_parentheses(text):
        """
        괄호를 제거한다.
        :param text: 문자열
        :return: 앞뒤에 있는 괄호를 제거한 문자열
        """
        return text.strip().lstrip("(").rstrip(")").strip()

    def exist(self, word, post):
        """
        포스트에 단어가 존재하는 지 여부
        :param word: 검색할 단어
        :param post: 포스트 데이터
        :return: 존재하는 지 여부
        """
        if isinstance(word, dict):
            return self.examine_conditions(word, post)
        elif isinstance(word, list):
            return len(word) > 0
        return bool(re.search(word, post))

    def replace_query(self, query):
        """
        쿼리를 정비한다.
        :param query:
        :return:
        """
        query = self.__SPACE.sub(" ", query.strip())
        query = self.replace_text(query)
        query = self.replace_quotes(query)
        return query

    def replace_text(self, text):
        return DataUtils.replace_tuples(text, (("“", '"'), ("”", '"'), ("é", "é")))

    def replace_quotes(self, query, start_quotes='"', end_quotes='"'):
        while True:
            first = query.find(start_quotes)
            if first > -1:
                last = query.find(end_quotes, first + 1) + 1
                word = query[first:last]
                word = word.lstrip(start_quotes)
                word = word.rstrip(end_quotes)
                word = word.replace(" ", self.__SPACE_SEP)
                query = query[:first] + word + query[last:]
            else:
                break
        return query
