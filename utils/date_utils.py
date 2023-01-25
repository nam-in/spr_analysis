import calendar
import time
from datetime import datetime, date, timezone, timedelta
from typing import Union

import pandas as pd
from dateutil import relativedelta


class DateUtils:
    """
    날짜 관련 메소드
    """

    # 기본 날짜 포멧
    DATE_FORMAT = '%Y-%m-%d'

    @staticmethod
    def add_years(d: date, add: int = 1) -> date:
        return d + relativedelta.relativedelta(years=add)

    @staticmethod
    def add_months(d: date, add: int = 1) -> date:
        return d + relativedelta.relativedelta(months=add)

    @staticmethod
    def add_days(d: Union[date, str] = None, add: int = 1, format_str: str = DATE_FORMAT) -> Union[date, str]:
        """
        날짜를 더한다.
        :param d: 날짜
        :param add: 더할 숫자
        :param format_str: 날짜 포멧, 날짜를 문자열 형태로 입력했을 경우 필요한 파라미터
        """
        is_str_type = isinstance(d, str)
        if d is None:
            d = DateUtils.get_today()
        elif is_str_type:
            d = DateUtils.to_date(d, format_str)
        if add != 0:
            d = d + relativedelta.relativedelta(days=add)
        if is_str_type:
            d = DateUtils.to_str_date(d, format_str)
        return d

    @staticmethod
    def get_date_str(add=0, format_str: str = DATE_FORMAT):
        if add == 0:
            return DateUtils.get_today_str(format_str)
        d = DateUtils.add_days(add=add)
        return DateUtils.to_str_date(d, format_str)

    @staticmethod
    def get_today_str(format_str: str = DATE_FORMAT) -> str:
        """
        오늘의 날짜를 가져온다.
        :param format_str: 날짜 포멧
        :return: 오늘의 날짜
        """
        return datetime.today().strftime(format_str)

    @staticmethod
    def to_str_date(d: date, format_str: str = DATE_FORMAT) -> str:
        """
        날짜를 문자형태로 변경한다.
        :param d: 날짜
        :param format_str: 날짜 포멧
        :return:
        """
        return d.strftime(format_str)

    @staticmethod
    def get_today(tz_hours=9) -> date:
        """
        오늘의 날짜를 가져온다.
        :return: 오늘의 날짜
        """
        return datetime.now(tz=timezone(timedelta(hours=tz_hours))).date()

    @staticmethod
    def to_date(date_str: str, date_format: str = DATE_FORMAT) -> date:
        """
        문자열을 데이트 형대로 변환한다.
        :param date_str: 날짜 문자열
        :param date_format: 날짜 포멧
        :return:
        """
        return datetime.strptime(date_str, date_format)

    @staticmethod
    def get_last_month(format_str='%Y-%m'):
        today = DateUtils.get_today()
        last_month_date = DateUtils.add_months(today, -1)
        return last_month_date.strftime(format_str)

    @staticmethod
    def get_datetime_str(fmt="%Y-%m-%d %H:%M:%S.%f"):
        now = datetime.now()
        return now.strftime(fmt)

    @staticmethod
    def get_days_of_last_month(format_str=DATE_FORMAT):
        given_date = datetime.today().date()
        last_day = given_date.replace(day=1) - timedelta(days=1)
        first_day = last_day.replace(day=1)
        return first_day.strftime(format_str), last_day.strftime(format_str)

    @staticmethod
    def get_days_of_month(month, return_format_str=DATE_FORMAT):
        first_day = datetime.strptime(month, "%Y-%m")
        _, end = calendar.monthrange(first_day.year, first_day.month)
        last_day = first_day.replace(day=end)
        return first_day.strftime(return_format_str), last_day.strftime(return_format_str)

    @staticmethod
    def get_month_range(from_month, to_month, return_format_str='%Y-%m'):
        return pd.date_range(from_month, to_month, freq='MS').strftime(return_format_str).tolist()

    @staticmethod
    def get_date_range(start_date, end_date):
        dates = pd.date_range(start_date, end_date)
        dates = [str(d)[:10] for d in dates]
        return dates

    @staticmethod
    def str_to_time(str_time, date_format="%Y-%m-%dT%H:%M:%S.%f"):
        return datetime.strptime(str_time, date_format)

    @staticmethod
    def time_to_str(time):
        return time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]

    @staticmethod
    def seconds_to_hhmmss(seconds, date_format="%H:%M:%S"):
        return time.strftime(date_format, time.gmtime(seconds))
