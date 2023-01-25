import itertools
import os
import platform
import re
import shutil
import time
import urllib.parse
import zipfile
from datetime import datetime
from pathlib import Path, PurePath
from typing import Optional, Any, Sequence

import compress_pickle
import numpy as np
import pandas as pd
import win32com.client
from tqdm import tqdm

import logging_config as log
from utils.exception_utils import ExceptionUtils


class DataUtils:
    """
    데이터 처리 관련 메소드
    """

    @staticmethod
    def read(file_path, sep=None, dtype=None, not_exist_ok=False, sheet_name=0):
        if not_exist_ok and not Path(file_path).exists():
            return pd.DataFrame()
        ext = DataUtils.get_ext(file_path)
        if ext == 'pkl':
            return DataUtils.read_pickle(file_path)
        elif ext in ('txt', 'rawdata', 'csv'):
            return DataUtils.read_csv(file_path, sep=sep, dtype=dtype)
        elif ext in ('xlsx', 'xls'):
            return DataUtils.read_excel(file_path, sheet_name=sheet_name)

    @staticmethod
    def save(df_data: pd.DataFrame, file_path, backup=True, index=True):
        """
        저장한다.
        :param df_data: 저장할 데이터
        :param file_path: 저장할 경로
        :param backup: 백업할지 여부
        :param index: index 출력 여부
        :return:
        """
        if isinstance(file_path, PurePath):
            file_path = str(file_path)
        ext = DataUtils.get_ext(file_path)
        if backup:
            DataUtils.backup_file(file_path)
        if ext == 'pkl':
            return DataUtils.save_pickle(df_data, file_path)
        elif ext in ('txt', 'rawdata', 'csv'):
            return DataUtils.save_csv(df_data, file_path)
        elif ext in ('xlsx', 'xls'):
            return DataUtils.save_excel(df_data, file_path, index)

    @staticmethod
    def read_pickle(file_path, compression="zip") -> pd.DataFrame:
        return pd.read_pickle(file_path, compression=compression)

    @staticmethod
    def save_pickle(data: pd.DataFrame, file_path, compression="zip"):
        DataUtils.create_dir(os.path.dirname(file_path))
        data.to_pickle(file_path, compression=compression)

    @staticmethod
    def backup_file(file_path, max_file_count=5):
        """
        파일을 백업한다.
        :param file_path: 백업할 파일 경로
        :param max_file_count: 백업하는 최대 개수
        :return:
        """
        if Path(file_path).exists():
            max_index = 0
            for max_index in itertools.count(start=1):
                if not Path(f"{file_path}.{max_index}").exists():
                    break
            if max_index > max_file_count:
                for i in range(max_file_count, max_index):
                    Path(f"{file_path}.{i}").unlink(missing_ok=True)
                max_index = max_file_count
            for i in reversed(range(max_index)):
                backup_file_path = f"{file_path}.{i + 1}"
                if i == 0:
                    shutil.copy(file_path, backup_file_path)
                else:
                    Path(f"{file_path}.{i}").rename(backup_file_path)

    @staticmethod
    def save_pickle_plain(data, file_path, compression="zipfile"):
        DataUtils.create_dir(os.path.dirname(file_path))
        kwargs = dict()
        if compression == "zipfile":
            kwargs = dict(zipfile_compression=zipfile.ZIP_DEFLATED)
        compress_pickle.dump(data, file_path, compression=compression, set_default_extension=False, **kwargs)

    @staticmethod
    def read_pickle_plain(file_path, compression="zipfile"):
        kwargs = dict()
        if compression == "zipfile":
            kwargs = dict(zipfile_compression=zipfile.ZIP_DEFLATED)
        return compress_pickle.load(file_path, compression=compression, set_default_extension=False, **kwargs)

    @staticmethod
    def read_parquet(file_path, columns=None):
        return pd.read_parquet(file_path, columns=columns)

    @staticmethod
    def add_prefix(text, prefix="_"):
        """
        문자열의 앞에 prefix를 붙여준다.
        :param text:
        :param prefix:
        :return:
        """
        if text is not None and text != '':
            return f"{prefix}{text}"
        else:
            return text

    @staticmethod
    def to_parquet(data: pd.DataFrame, file_path, compression="gzip") -> None:
        data.to_parquet(file_path, compression=compression, engine="pyarrow")

    @staticmethod
    def unique(array):
        array = [content.strip().lower() for content in array]
        return np.unique(array)

    @staticmethod
    def create_dir(dir_path: str) -> None:
        """
        디렉토리를 생성한다.
        :param dir_path:
        :return:
        """
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    @staticmethod
    def save_csv(df_data: pd.DataFrame, file_path: str) -> None:
        """
        csv 형태의 데이터로 저장한다.
        :param df_data:
        :param file_path:
        :return:
        """
        DataUtils.create_dir(os.path.dirname(file_path))
        df_data.to_csv(file_path, index=False, encoding="utf-8-sig")

    @staticmethod
    def update_csv(data: pd.DataFrame, file_path: str, sort_by: Optional[str] = None,
                   ascending: bool = True) -> pd.DataFrame:
        """
        csv 형태의 데이터로 저장한다.
        :param ascending:
        :param sort_by:
        :param data:
        :param file_path:
        :return:
        """
        if os.path.exists(file_path):
            saved_data = pd.read_csv(file_path, encoding="utf-8")
            data = pd.concat([saved_data, data], ignore_index=True)
        if not (sort_by is None):
            data = data.sort_values(by=sort_by, ascending=ascending)
        DataUtils.save_csv(data, file_path)
        return data

    @staticmethod
    def read_excel(file_path, sheet_name=0) -> pd.DataFrame:
        try:
            return pd.read_excel(file_path, sheet_name=sheet_name)
        except Exception as e:
            log.get_logger("DataUtils").debug(ExceptionUtils.get_error_message(e))
            return DataUtils.get_excel_data(file_path, sheets=sheet_name)

    @staticmethod
    def save_excel(df_data: pd.DataFrame, file_path: str, index=False) -> None:
        """
        엑셀 형태의 데이터로 저장한다.
        :param df_data:
        :param file_path:
        :param index:
        :return:
        """
        DataUtils.create_dir(os.path.dirname(file_path))
        df_data.to_excel(file_path, index=index)

    @staticmethod
    def save_excel_sheets(file_path, sheets, index=False, backup=True):
        if backup:
            DataUtils.backup_file(file_path)
        with pd.ExcelWriter(file_path) as writer:
            for sheet_name, sheet_df in sheets:
                sheet_df.to_excel(writer, sheet_name=sheet_name, index=index)

    @staticmethod
    def read_csv(file_path: str, sep: Optional[str] = None, dtype=None):
        if sep is None:
            sep = DataUtils.get_default_sep(file_path)

        if sep is None:
            return pd.read_csv(file_path, encoding="utf-8", dtype=dtype)
        else:
            return pd.read_csv(file_path, encoding="utf-8", sep=sep, dtype=dtype)

    @staticmethod
    def get_default_sep(file_path):
        ext = DataUtils.get_ext(file_path)
        if ext in ("txt", "rawdata"):
            sep = "\t"
        else:
            sep = ","
        return sep

    @staticmethod
    def get_ext(file_path):
        _, ext = os.path.splitext(str(file_path))
        ext = ext.lstrip(".")
        return ext

    @staticmethod
    def creation_time(path_to_file):
        """
        Try to get the date that a file was created, falling back to when it was
        last modified if that isn't possible.
        See http://stackoverflow.com/a/39501288/1709587 for explanation.
        """
        if platform.system() == 'Windows':
            time = os.path.getctime(path_to_file)
        else:
            stat = os.stat(path_to_file)
            try:
                time = stat.st_birthtime
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates here,
                # so we'll settle for when its content was last modified.
                time = stat.st_mtime
        return datetime.fromtimestamp(time)

    @staticmethod
    def remove_file(file_path: str) -> None:
        """
        파일이 존재하면 삭제한다.
        :param file_path: 파일 경로
        :return:
        """
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger = log.get_logger("DataUtils")
                logger.error(e)

    @staticmethod
    def put_first(n: int, data_df: pd.DataFrame) -> pd.DataFrame:
        """
        n번째 행을 제일 앞으로 보낸다.
        :param n: 제일 앞으로 보낼 행의 index
        :param data_df: 데이터
        :return:
        """
        data_df = data_df.reindex([n] + list(range(0, n)) + list(range(n + 1, data_df.index[-1] + 1))) \
            .reset_index(drop=True)
        return data_df

    @staticmethod
    def list_to_in_query(data_list: Sequence[Any]) -> str:
        """
        리스트를 in 쿼리에 해당하는 문자열을 붙인다.
        :param data_list:
        :return:
        """
        if len(data_list) == 1:
            return "('" + data_list[0] + "')"
        else:
            return str(tuple(data_list))

    @staticmethod
    def list_to_file_name(data_list: Sequence[Any]) -> str:
        """
        리스트를 in 쿼리에 해당하는 문자열을 붙인다.
        :param data_list:
        :return:
        """
        data_list = sorted(data_list)
        return ",".join(data_list)

    @staticmethod
    def loop_groups(data_df, group_cols, loop_func, desc="loop...", **kwargs):
        """
        그룹으로 나누어 반복하여 실행하여 결과를 합한다.
        :param loop_func:
        :param data_df:
        :param group_cols:
        :param desc:
        :param kwargs:
        :return:
        """
        results = []
        group_cols = list(group_cols)
        for _, group in tqdm(data_df.groupby(group_cols), desc):
            result_df = loop_func(group, **kwargs)
            results.append(result_df)
        result_df = pd.concat(results, ignore_index=True)
        return result_df

    @staticmethod
    def get_excel_data(file_path, max_wait_sec=60, sheets=1):
        for _ in range(max_wait_sec):
            if file_path.exists():
                break
            else:
                time.sleep(1)

        excel, workbook, data_df = None, None, pd.DataFrame()
        try:
            excel = win32com.client.Dispatch("Excel.Application")
            workbook = excel.Workbooks.Open(file_path)
            excel.Visible = False
            if isinstance(sheets, (list, tuple)):
                data_df = []
                for sheet in sheets:
                    df = DataUtils.get_excel_sheet_data(workbook, sheet)
                    data_df.append(df)
            else:
                data_df = DataUtils.get_excel_sheet_data(workbook, sheets)
        finally:
            try:
                if workbook:
                    workbook.Close()
                if excel:
                    excel.Quit()
            except Exception as e:
                log.get_logger().error(ExceptionUtils.get_error_message(e))
        return data_df

    @staticmethod
    def get_excel_sheet_data(workbook, sheet):
        sheet = workbook.Sheets(sheet)
        data = sheet.UsedRange()
        columns = data[0]
        items = DataUtils.change_datetime(data[1:])
        data_df = pd.DataFrame(items, columns=columns)
        return data_df

    @staticmethod
    def change_datetime(items):
        if len(items) == 0:
            return items
        for i, item in enumerate(items[0]):
            if isinstance(item, datetime):
                if isinstance(items, tuple):
                    items = [list(row) for row in items]
                for j in range(len(items)):
                    items[j][i] = str(items[j][i])
        return items

    @staticmethod
    def to_list(values: str, sep=","):
        return [v.strip() for v in values.split(sep=sep)]

    @staticmethod
    def update_url_query(url, params):
        url_parts = urllib.parse.urlparse(url)
        query = dict(urllib.parse.parse_qsl(url_parts.query))
        query.update(params)
        return url_parts._replace(query=urllib.parse.urlencode(query)).geturl()

    @staticmethod
    def replace_tuples(text, replace_tuples):
        if not isinstance(text, str):
            text = str(text)
        for r in replace_tuples:
            text = text.replace(*r)
        return text

    @staticmethod
    def get_first_file(dir_path: Path):
        first_path = None
        for path in dir_path.iterdir():
            if path.is_file():
                first_path = path
                break
        return first_path

    @staticmethod
    def fix_columns(data):
        data.columns = [re.sub('[ ]+', '_', col.lower()) for col in data.columns]
        data.columns = [col.strip("_") for col in data.columns]
        return data