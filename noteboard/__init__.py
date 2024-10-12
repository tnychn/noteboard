# Prepare directory paths
import os

from .utils import init_config, load_config, setup_logger


CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".noteboard.json")

if not os.path.isfile(CONFIG_PATH):
    init_config(CONFIG_PATH)


DIR_PATH = os.path.join(os.path.expanduser("~"), ".noteboard/")
config = load_config(CONFIG_PATH)

path = config.get("StoragePath") or DIR_PATH
path = os.path.expanduser(path)
if not os.path.isdir(path):
    os.mkdir(path)

LOG_PATH = os.path.join(path, "noteboard.log")
HISTORY_PATH = os.path.join(path, "history.json.gz")
STORAGE_PATH = os.path.join(path, "storage")
STORAGE_GZ_PATH = os.path.join(path, "storage.gz")

DEFAULT_BOARD = (config.get("DefaultBoardName") or "Board").strip()
TAGS = config.get("Tags", {"default": "BLUE"})

setup_logger(LOG_PATH)
