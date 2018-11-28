from time import strftime

from core import common

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
INFO = "INFO"
WARN = "WARN"
ERROR = "ERROR"


def info(message):
    log(INFO, message)


def warning(message):
    log(WARN, message)


def error(message):
    log(ERROR, message)


def log(level, message):
    print("%s %s-vision[%s]: %s" % (strftime(TIME_FORMAT), common.PROCESS_NAME, level, message))
