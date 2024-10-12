import time
import datetime
import os
import json
import logging


DEFAULT = {
    "StoragePath": "~/.noteboard/",
    "DefaultBoardName": "Board",
    "Tags": {
        "default": "BLUE",
    }
}


def get_time(fmt=None):
    if fmt:
        date = datetime.datetime.now().strftime(fmt)  # str
    else:
        date = datetime.datetime.now().strftime("%a %d %b %Y")  # str
    timestamp = time.time()
    return date, timestamp


def to_timestamp(date):
    return int(time.mktime(date.timetuple()))


def to_datetime(ts):
    return datetime.date.fromtimestamp(ts)  # datetime instance


def time_diff(ts, reverse=False):
    """Get the time difference between the given timestamp and the current time."""
    date = datetime.datetime.fromtimestamp(ts)
    now = datetime.datetime.fromtimestamp(get_time()[1])
    if reverse:
        return date - now  # datetime instance
    return now - date  # datetime instance


def add_date(days):
    """Get the datetime with `days` added to the current datetime."""
    today = datetime.date.today()
    date = today + datetime.timedelta(days=days)
    return date  # datetime instance


def setup_logger(path):
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] (%(funcName)s in %(filename)s) %(message)s", "")
    handler = logging.FileHandler(path, mode="a+")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)

    logger = logging.getLogger("noteboard")
    logger.setLevel(logging.DEBUG)
    if not logger.hasHandlers():
        logger.addHandler(handler)
    return logger


def init_config(path):
    """Initialise configurations file. If file already exists, it will be overwritten."""
    with open(path, "w+") as f:
        json.dump(DEFAULT, f, sort_keys=True, indent=4)


def load_config(path):
    """Load configurations file. If file does not exist, call `init_config()`."""
    if not os.path.isfile(path):
        init_config(path)

    with open(path, "r+") as f:
        config = json.load(f)
    return config
