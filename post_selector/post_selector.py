from functools import partial

import pandas as pd
from tqdm import tqdm

import logging_config as log
from post_selector.post_checker import PostChecker
from post_selector.data_loader import DataLoader
from post_selector.query_parser import QueryParser
from utils.parallel_utils import ParallelUtils


class PostSelector:
    """
    포스트들이 "query"의 패턴과 일치하는지 체크하여 결과를 저장한다.
    """

    def __init__(self, query_file_names=("query",)):
        self.logger = log.get_logger(self.__class__.__name__)
        self.query_file_names = query_file_names
        self.input_csv_sep = None

        self.loader = DataLoader()
        self.checker = PostChecker()

    def check_posts(self, query_file_names=None, column_names=None, cpu_divide_count=2, posts=None):
        """
        포스트들이 "query"의 패턴과 일치하는지 체크하여 결과를 저장한다.
        :param query_file_names: 쿼리 파일 명들
        :param column_names: 컬럼 명들
        :param cpu_divide_count:
        :param posts:
        :return:
        """
        if query_file_names is not None:
            self.query_file_names = query_file_names
        if isinstance(query_file_names, str):
            query_file_names = (query_file_names,)
        if column_names is None:
            column_names = query_file_names

        file_name = None
        if posts is None:
            posts, file_name = self.loader.load_post()
        posts = self.check_posts_by_post_parallel(posts, query_file_names, column_names,
                                                  cpu_divide_count=cpu_divide_count)
        posts = posts.iloc[:, 1:]
        if file_name is not None:
            self.loader.save_result(posts, file_name)
        return posts

    def check_posts_by_query(self, posts, query_file_names, column_names):
        """
        쿼리 순으로 포스트를 체크함
        :param posts: 포스트들
        :param query_file_names: 쿼리 파일명들
        :param column_names: 컬럼명들
        :return:
        """
        for query_file_name, column_name in zip(query_file_names, column_names):
            query = self.get_query(query_file_name)
            self.logger.debug(f"Query : {query}")
            tqdm.pandas(desc=f"Check Posts::{query_file_name}")
            posts[column_name] = posts.iloc[:, 0].progress_apply(self.checker.check_post, query=query)
        return posts

    def check_posts_by_post(self, posts, query_file_names, column_names, tqdm_disable=False):
        """
        포스트 순으로 쿼리들을 체크함
        :param posts: 포스트들
        :param query_file_names: 쿼리 파일명들
        :param column_names: 컬럼명들
        :param tqdm_disable:
        :return:
        """
        parser = QueryParser()
        queries = []
        for query_file_name in query_file_names:
            query = self.get_query(query_file_name)
            query = parser.query_to_dict(query)
            queries.append(query)

        posts = posts.reset_index(drop=True)
        values = []
        for index, post in tqdm(zip(posts.index, posts.iloc[:, 0]), total=len(posts.index),
                                desc="Check Posts", disable=tqdm_disable):
            self.logger.debug(f"Post index: {index}")
            row = self.checker.check_post_for_queries(post, queries, column_names)
            values.append(row)
        posts = pd.concat([posts, pd.DataFrame(values)], axis=1)
        return posts

    def check_posts_by_post_parallel(self, posts, query_file_names, column_names, cpu_divide_count=2):
        check_posts_by_post = partial(self.check_posts_by_post, query_file_names=query_file_names,
                                      column_names=column_names, tqdm_disable=True)
        return ParallelUtils.parallel(posts, check_posts_by_post, cpu_divide_count=cpu_divide_count, desc="Check Posts")

    def get_query(self, query_file_name):
        """
        쿼리를 불러온다.
        :param query_file_name: 쿼리 파일명
        :return:
        """
        query = self.loader.load_query(query_file_name)
        return self.checker.replace_query(query)
