import logging
from decimal import Decimal


def config_logger(filename):
    log_formatter = '[%(asctime)s] %(levelname)s : %(message)s'
    # create formatter
    formatter = logging.Formatter(log_formatter)
    log_level = logging.INFO

    # create logger
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # add formatter to ch
    ch.setFormatter(formatter)

    fh = logging.FileHandler(
        filename=filename, encoding='utf-8')
    fh.setLevel(log_level)
    # tell the handler to use this format
    fh.setFormatter(formatter)

    # add the handler to the root logger
    logger.addHandler(ch)
    logger.addHandler(fh)

    def print_split(title):
        SPLIT_MARK = '====================== {} ========================='
        logger.info(SPLIT_MARK.format(title))

    logger.print_split = print_split
    return logger


def decimal_from_value(value):
    if value:
        return Decimal(str(value).replace(',', ''))