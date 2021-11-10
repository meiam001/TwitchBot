import sys, os
import logging

class CustomFormatter(logging.Formatter):
    """ Custom Formatter does these 2 things:
    1. Overrides 'funcName' with the value of 'func_name_override', if it exists.
    2. Overrides 'filename' with the value of 'file_name_override', if it exists.
    """
    def format(self, record):
        if hasattr(record, 'func_name_override'):
            record.funcName = record.func_name_override
        if hasattr(record, 'file_name_override'):
            record.filename = record.file_name_override
        return super(CustomFormatter, self).format(record)


def get_logger(log_file: str, log_dir='.', level=40) -> logging.Logger:
    """

    :param log_file:
    :param log_dir:
    :param level:
        CRITICAL = 50
        ERROR = 40
        WARNING = 30
        WARN = WARNING
        INFO = 20
        DEBUG = 10
        NOTSET = 0
    :return:
    """
    logPath = os.path.join(log_dir, log_file + '.log')
    if not os.path.exists(log_dir):
        os.makedirs(logPath)
    logger = logging.Logger(logPath)
    logger.setLevel(level)
    handler = logging.FileHandler(logPath, 'a+')
    handler.setFormatter(CustomFormatter(
        '%(asctime)s - %(levelname)-10s - %(filename)s - %(funcName)s - %(message)s'
    ))
    logger.addHandler(handler)
    return logger


def x():
    return f'Exception: {str(sys.exc_info())}'
