import shelve
import gzip
import shutil
import json
import os
import logging

from . import DIR_PATH, HISTORY_PATH, STORAGE_PATH, STORAGE_GZ_PATH, DEFAULT_BOARD
from .utils import get_time, to_datetime

logger = logging.getLogger("noteboard")


class NoteboardException(Exception):
    """Base Exception Class of Noteboard."""


class ItemNotFoundError(NoteboardException):
    """Raised when no item with the specified id found."""

    def __init__(self, id):
        self.id = id

    def __str__(self):
        return "Item {} not found".format(self.id)


class BoardNotFoundError(NoteboardException):
    """Raised when no board with specified name found."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Board '{}' not found".format(self.name)


class History:

    def __init__(self, storage):
        self.storage = storage
        self.buffer = None

    @staticmethod
    def load():
        try:
            with gzip.open(HISTORY_PATH, "r") as j:
                history = json.loads(j.read().decode("utf-8"))
        except FileNotFoundError:
            raise NoteboardException("History file not found for loading")
        return history

    def revert(self):
        history = History.load()
        hist = [i for i in history if i["data"] is not None]
        if len(hist) == 0:
            return {}
        state = hist[-1]
        logger.debug("Revert state: {}".format(state))
        # Update the shelf
        self.storage.shelf.clear()
        self.storage.shelf.update(dict(state["data"]))
        # Remove state from history
        history.remove(state)
        # Update the history file
        with gzip.open(HISTORY_PATH, "w") as j:
            j.write(json.dumps(history).encode("utf-8"))
        return state

    def save(self, data):
        self.buffer = data.copy()

    def write(self, action, info):
        is_new = not os.path.isfile(HISTORY_PATH)

        # Create and initialise history file with an empty list
        if is_new:
            with gzip.open(HISTORY_PATH, "w+") as j:
                j.write(json.dumps([]).encode("utf-8"))

        # Write data to disk
        # => read the current saved states
        history = History.load()
        # => dump history data
        state = {"action": action, "info": info, "date": get_time("%d %b %Y %X")[0], "data": dict(self.buffer) if self.buffer else self.buffer}
        logger.debug("Write history: {}".format(state))
        history.append(state)
        with gzip.open(HISTORY_PATH, "w") as j:
            j.write(json.dumps(history).encode("utf-8"))
        self.buffer = None  # empty the buffer


class Storage:

    def __init__(self):
        self._shelf = None
        self.history = History(self)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
        return False

    def open(self):
        # Open shelf
        if self._shelf is not None:
            raise NoteboardException("Shelf object has already been opened.")

        if not os.path.isdir(DIR_PATH):
            logger.debug("Making directory {} ...".format(DIR_PATH))
            os.mkdir(DIR_PATH)

        if os.path.isfile(STORAGE_GZ_PATH):
            # decompress compressed storage.gz to a storage file
            with gzip.open(STORAGE_GZ_PATH, "rb") as f_in:
                with open(STORAGE_PATH, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(STORAGE_GZ_PATH)

        self._shelf = shelve.open(STORAGE_PATH, "c", writeback=True)

    def close(self):
        if self._shelf is None:
            raise NoteboardException("No opened shelf object to be closed.")

        # Cleanup
        for board in self.shelf:
            # remove empty boards
            if not self.shelf[board]:
                self.shelf.pop(board)
                continue
            # always sort items on the boards before closing
            self.shelf[board] = list(sorted(self.shelf[board], key=lambda x: x["id"]))
        self._shelf.close()

        # compress storage to storage.gz
        with gzip.open(STORAGE_GZ_PATH, "wb") as f_out:
            with open(STORAGE_PATH, "rb") as f_in:
                shutil.copyfileobj(f_in, f_out)
        os.remove(STORAGE_PATH)

    @property
    def shelf(self):
        """Use this property to access the shelf object from the outside."""
        if self._shelf is None:
            raise NoteboardException("No opened shelf object to be accessed.")
        return self._shelf

    @property
    def boards(self):
        """Get all existing board titles."""
        return list(self.shelf.keys())

    @property
    def items(self):
        """Get all existing items with ids and texts."""
        results = {}
        for board in self.shelf:
            for item in self.shelf[board]:
                results[item["id"]] = item["text"]
        return results

    @property
    def total(self):
        """Get the total amount of items in all boards."""
        return len(self.items)

    def get_item(self, id):
        """Get the item with the give ID. ItemNotFoundError will be raised if nothing found."""
        for board in self.shelf:
            for item in self.shelf[board]:
                if item["id"] == id:
                    return item
        raise ItemNotFoundError(id)

    def get_board(self, name):
        """Get the board with the given name. BoardNotFound will be raised if nothing found."""
        for board in self.shelf:
            if board == name:
                return self.shelf[name]
        raise BoardNotFoundError(name)

    def get_all_items(self):
        items = []
        for board in self.shelf:
            for item in self.shelf[board]:
                items.append(item)
        return items

    def _add_board(self, board):
        if board.strip() == "":
            raise ValueError("Board title must not be empty.")
        if board in self.shelf.keys():
            raise KeyError("Board already exists.")
        logger.debug("Added Board: '{}'".format(board))
        self.shelf[board] = []  # register board by adding an empty list

    def _add_item(self, id, board, text):
        date, timestamp = get_time()
        payload = {
            "id": id,           # int
            "text": text,       # str
            "time": timestamp,  # int
            "date": date,       # str
            "due": None,        # int
            "tick": False,      # bool
            "mark": False,      # bool
            "star": False,      # bool
            "tag": ""           # str
        }
        self.shelf[board].append(payload)
        logger.debug("Added Item: {} to Board: '{}'".format(json.dumps(payload), board))
        return payload

    def add_item(self, board, text):
        """[Action]
        * Can be Undone: Yes
        Prepare data to be dumped into the shelf.
        If the specified board not found, it automatically creates and initialise a new board.
        This method passes the prepared dictionary data to self._add_item to encrypt it and really add it to the board.
        
        Returns:
            dict -- data of the added item
        """
        current_id = 1
        # get all existing ids
        ids = list(sorted(self.items.keys()))
        if ids:
            current_id = ids[-1] + 1
        # board name
        board = board or DEFAULT_BOARD
        # add
        if board not in self.shelf:
            # create board
            self._add_board(board)
        # add item
        return self._add_item(current_id, board, text)

    def remove_item(self, id):
        """[Action]
        * Can be Undone: Yes
        Remove an existing item from board.

        Returns:
            dict -- data of the removed item
            str -- board name of the regarding board of the removed item
        """
        status = False
        for board in self.shelf:
            for item in self.shelf[board]:
                if item["id"] == id:
                    # remove
                    self.shelf[board].remove(item)
                    removed = item
                    board_of_removed = board
                    logger.debug("Removed Item: {} on Board: '{}'".format(json.dumps(item), board))
                    status = True
            if len(self.shelf[board]) == 0:
                del self.shelf[board]
        if status is False:
            raise ItemNotFoundError(id)
        return removed, board_of_removed
    
    def clear_board(self, board=None):
        """[Action]
        * Can be Undone: Yes
        Remove all items of a board or of all boards (if no board is specified).

        Returns:
            int -- total amount of items removed
        """
        if not board:
            amt = len(self.items)
            # remove all items of all boards
            self.shelf.clear()
            logger.debug("Cleared all {} Items".format(amt))
        else:
            # remove
            if board not in self.shelf:
                raise BoardNotFoundError(board)
            amt = len(self.shelf[board])
            del self.shelf[board]
            logger.debug("Cleared {} Items on Board: '{}'".format(amt, board))
        return amt

    def modify_item(self, id, key, value):
        """[Action]
        * Can be Undone: Partially (only when modifying text)
        Modify the data of an item, given its ID.
        If the item does not have the key, one will be created.

        Arguments:
            id {int} -- id of the item you want to modify
            key {str} -- one of [id, text, time, tick, star, mark, tag]
            value -- new value to replace the old value
        
        Returns:
            dict -- the item before modification
        """
        item = self.get_item(id)
        old = item.copy()
        item[key] = value
        logger.debug("Modified Item from {} to {}".format(json.dumps(old), json.dumps(item)))
        return old

    def move_item(self, id, board):
        """[Action]
        * Can be undone: No
        Move the whole item to the destination board, given the id of the item and the name of the board.

        If the destination board does not exist, one will be created.

        Arguments:
            id {int} -- id of the item you want to move
            board {str} -- name of the destination board

        Returns:
            item {dict} -- the item that is moved
            b {str} -- the name of board the item originally from
        """
        for b in self.shelf:
            for item in self.shelf[b]:
                if item["id"] == id:
                    if not self.shelf.get(board):
                        # register board with a empty list if board not found
                        self.shelf[board] = []
                    # append to dest board `board`
                    self.shelf[board].append(item)
                    # remove from the current board `b`
                    self.shelf[b].remove(item)
                    return item, b
        raise ItemNotFoundError(id)

    @staticmethod
    def _validate_json(data):
        keys = ["id", "text", "time", "date", "due", "tick", "mark", "star", "tag"]
        for board in data:
            if board.strip() == "":
                return False
            # Check for board type (list)
            if not isinstance(data[board], list):
                return False
            for item in data[board]:
                # Check for item type (dictionary)
                if not isinstance(item, dict):
                    return False
                # Check for existence of keys
                for key in keys:
                    if key not in item.keys():
                        return False
                # Automatically make one from supplied timestamp if date is not supplied
                if not item["date"] and item["time"]:
                    item["date"] = to_datetime(float(item["time"])).strftime("%a %d %b %Y")
        return True

    def import_(self, path):
        """[Action]
        * Can be Undone: Yes
        Import and load a local file (json) and overwrite the current boards.

        Arguments:
            path {str} -- path to the archive file
        
        Returns:
            path {str} -- full path of the imported file
        """
        path = os.path.abspath(path)
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise NoteboardException("File not found ({})".format(path))
        except json.JSONDecodeError:
            raise NoteboardException("Failed to decode JSON")
        else:
            if self._validate_json(data) is False:
                raise NoteboardException("Invalid JSON structure for noteboard")
            # Overwrite the current shelf and update it
            self.shelf.clear()
            self.shelf.update(dict(data))
            return path
    
    def export(self, dest="./board.json"):
        """[Action]
        * Can be Undone: No
        Exoport the current shelf as a JSON file to `dest`.

        Arguments:
            dest {str} -- path of the destination
        
        Returns:
            path {str} -- full path of the exported file
        """
        dest = os.path.abspath(dest)
        data = dict(self.shelf)
        with open(dest, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)
        return dest

    def save_history(self):
        data = {}
        for board in self.shelf:
            data[board] = []
            for item in self.shelf[board]:
                data[board].append(item.copy())
        self.history.save(data)

    def write_history(self, action, info):
        self.history.write(action, info)
