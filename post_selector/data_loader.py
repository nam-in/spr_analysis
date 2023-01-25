import os

import logging_config as log
from post_selector.post_selector_config import PostSelectorConfig
from utils.data_utils import DataUtils


class DataLoader:
    """
    필요한 데이터를 불러들인다.
    """

    def __init__(self):
        self.logger = log.get_logger(self.__class__.__name__)
        self.cfg = PostSelectorConfig()

    def load_query(self, file_name="query"):
        """
        쿼리를 가져온다.
        :param file_name: 쿼리의 파일 명
        :return:
        """
        file_path = self.cfg.query_dir / f"{file_name}.txt"
        with open(file_path, 'r', encoding="utf8") as f:
            query = f.read()
        return query.strip()

    def load_post(self):
        """
        포스트를 가져온다.
        :return:
        """
        file_path = DataUtils.get_first_file(self.cfg.run_dir)
        self.logger.debug(f"File Path: {file_path}")
        posts = DataUtils.read(file_path)
        return posts, file_path.name

    def save_result(self, data, file_name):
        """
        결과를 저장한다.
        :param data: 저장할 데이터
        :param file_name: 저장할 파일 명
        :return:
        """
        name, ext = os.path.splitext(file_name)
        file_path = self.cfg.results_dir / f"{name}_result{ext}"
        DataUtils.save(data, file_path, backup=True)
