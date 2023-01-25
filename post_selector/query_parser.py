import re

import logging_config as log
from utils.data_utils import DataUtils


class QueryParser:

    def __init__(self):
        self.logger = log.get_logger(self.__class__.__name__)
        self.__NEAR = re.compile('\s+NEAR/[0-9]+\s+')
        self.__OR = re.compile('\s+OR\s+')
        self.__AND = re.compile('\s+AND\s+')
        self.__NOT = re.compile('\s+NOT\s+')
        self.__LIST = re.compile('^\[[0-9, ]*]$')
        self.__NUM = re.compile('[0-9]+')
        self.__SPACE_SEP = "_|_"
        self.__COND = re.compile(':[0-9]+:')
        self.__conditions = []

    def query_to_dict(self, query):
        while True:
            parenthesis_query, (first, last) = self.extract_parenthesis_query(query)
            if parenthesis_query is None:
                break
            self.logger.debug(f"Parenthesis query: {parenthesis_query}")
            query_dict = self.conditions_to_dict(parenthesis_query)
            self.__conditions.append(query_dict)
            query = query[:first] + ":" + str(len(self.__conditions) - 1) + ":" + query[last + 1:]
            self.logger.debug(f"Query after parenthesis query: {query}")
        result = self.conditions_to_dict(query)
        return result

    def conditions_to_dict(self, query):
        """
        쿼리의 조건들을 조사한다.
        :param query: 정의된 패턴
        :return:
        """
        query = query.strip()
        or_words = self.split_query(self.__OR, query)
        if len(or_words) > 1:
            return self.condition_to_dict('OR', or_words)
        and_words = self.split_query(self.__AND, query)
        if len(and_words) > 1:
            return self.condition_to_dict('AND', and_words)
        not_words = self.split_query(self.__NOT, query)
        if len(not_words) > 1:
            return self.condition_to_dict('NOT', not_words)
        near_words = self.split_query(self.__NEAR, query)
        if len(near_words) > 1:
            near_num = self.get_near_num(query)
            return self.condition_to_dict('NEAR', near_words, near_num)
        return query

    def condition_to_dict(self, operator, operands, distance=None):
        for i, operand in enumerate(operands):
            if self.__COND.search(operand):
                cond_id = int(self.__NUM.search(operand).group())
                operands[i] = self.__conditions[cond_id]
            else:
                operands[i] = self.to_regex_word(operand)
        cond_dict = {'operator': operator, 'operands': operands}
        if distance:
            cond_dict.update(distance=distance)
        return cond_dict

    def get_near_num(self, query):
        near_op = self.__NEAR.search(query)
        near_num = int(self.__NUM.search(near_op.group()).group())
        return near_num

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

    def to_regex_word(self, word):
        """
        검색할 단어를 정규 표현식으로 변환한다.
        :param word: 검색할 단어
        :return: 정규 표현식
        """
        word = DataUtils.replace_tuples(word, (
            (self.__SPACE_SEP, " "), (".", "[.]"), ("+", "[+]"), ("?", "."), ("*", "[^ ]*")))
        return " " + word + "[?!,. ]"

    @staticmethod
    def extract_parenthesis_query(query):
        """
        괄호가 있는 문자열을 조회한다.
        :param query: 정의된 패턴
        :return: 괄호가 있는 문자열, (시작 index, 끝 index)
        """
        last = query.find(')')
        if last == -1:
            return None, (None, None)
        else:
            query = query[:last]
            first = query.rfind("(")
            return query[first + 1:last], (first, last)
