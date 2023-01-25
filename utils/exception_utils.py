import traceback


class ExceptionUtils:

    @staticmethod
    def get_error_message(exception):
        tb = traceback.TracebackException.from_exception(exception)
        return f"{str(exception)} \n{''.join(tb.stack.format())}"
