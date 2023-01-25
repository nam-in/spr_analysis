import datetime
from functools import wraps

import logging_config as log


class LogUtils:

    @staticmethod
    def timeit(func):
        @wraps(func)
        def timed(*args, **kw):
            ts = datetime.datetime.now()
            result = func(*args, **kw)
            te = datetime.datetime.now()
            msg = f'{func.__qualname__} {te - ts} sec'
            log.get_logger("LogUtils").info(msg)
            return result

        return timed
