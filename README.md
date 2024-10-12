<h1 align="center">noteboard</h1>

<p align="center"><em>A <a href="https://github.com/klaussinani/taskbook">taskbook</a> clone written in Python.</em></p>

<p align="center"><img src="./screenshot.png?raw=true" width=70%></p>

<p align="center">
  <a href="https://pypi.python.org/pypi/noteboard"><img src="https://img.shields.io/pypi/v/noteboard.svg"></a>
  <a href="https://pypi.python.org/pypi/noteboard"><img src="https://img.shields.io/pypi/dm/noteboard.svg"></a>
  <a href="./LICENSE.txt"><img src="https://img.shields.io/github/license/tnychn/noteboard.svg"></a>
</p>


**noteboard** is a mini command-line tool which lets you manage and store your notes & tasks in a tidy and fancy way, right inside your terminal.

## Table of Contents
- [Features](#features)
- [Behind the Board](#behind-the-board)
- [Installation](#installation)
  - [Source](#source)
  - [PyPI](#pypi)
  - [Dependencies](#dependencies)
- [Usage](#usage)
  - [View board](#view-board)
  - [Add item](#add-item)
  - [Remove item](#remove-item)
  - [Clear board](#clear-board)
  - [Tick / Mark / Star item](#tick--mark--star-item)
  - [Edit item](#edit-item)
  - [Tag item](#tag-item)
  - [Assign due date to item](#assign-due-date-to-item)
  - [Move item](#move-item)
  - [Rename bard](#rename-board)
  - [Run item as command](#run-item-as-command)
  - [Undo previous actions](#undo-previous-actions)
  - [Import board from external JSON file](#import-board-from-external-json-file)
  - [Export board data as JSON file](#export-board-data-as-json-file)
  - [See historical changes](#see-historical-changes)
- [Configurations](#configurations)
- [Cautions](#cautions)
- [Credit](#credit)

## Features

* Fancy interface ✨
* Simple & Easy to use 🚀
* Fast as lightning ⚡️
* Manage notes & tasks in multiple boards 🗒
* Run item as command inside terminal (subprocess) 💨
* Tag item with color and text 🏷
* Import boards from external JSON files & Export boards as JSON files
* Undo multiple actions / changes
* Keep historical states 🕥
* `Gzip` compressed storage 📚
* Configurable through `~/.noteboard.json`

## Behind the Board

The main storage is powered by `shelve`, a Python standard library, which provides a lightweight & persistent file-based database system.
Whereas the "history" system (the one which allows you to undo previous actions), is backed by a `json` file.

Notably, the storage and the buffer are compressed to `gzip` when it is not being accessed.
This greatly reduces the sizes of the files by more than 50%. 

## Installation

Make sure you have Python 3.6 (or higher) installed in your machine.

**NOTE:** You should remove all the data stored in `<StoragePath>` (default: `~/.noteboard/`) every time you install a new version to avoid conflicts.

### Source

```shell
$ git clone https://github.com/tnychn/noteboard.git
$ cd noteboard
$ python3 setup.py install
```

### PyPI

`$ pip3 install noteboard`

### Dependencies

[colorama](https://github.com/tartley/colorama)

## Usage

```text
Actions:
    add                 [+] Add an item to a board
    remove              [-] Remove items
    clear               [x] Clear all items on a/all boards
    tick                [✓] Tick/Untick an item
    mark                [!] Mark/Unmark an item
    star                [*] Star/Unstar an item
    edit                [~] Edit the text of an item
    tag                 [#] Tag an item with text
    due                 [:] Assign a due date to an item
    run                 [>] Run an item as command
    move                [&] Move an item to another board
    rename              [~] Rename the name of the board
    undo                [^] Undo the last action
    import              [I] Import and load boards from JSON file
    export              [E] Export boards as a JSON file
    history             [.] Prints out the historical changes

Options:
    -h, --help          show this help message and exit
    --version           show program's version number and exit
    -d, --date          show boards with the added date of every item
    -s, --sort          show boards with items on each board sorted alphabetically
    -t, --timeline      show boards in timeline view, ignore the -d/--date option
```

---

### View board

`$ board`

* `-d/--date` : show boards with the last modified date of each item in the format of `<weekday> <day> <month> <year>`. e.g. `Fri 25 Jan 2019`
* `-s/--sort` : show boards with items on each board sorted alphabetically by the text of the items
* `-t, --timeline` : show boards in timeline view, ignore the `-d/--date` option

**NOTE**: If `-d/--date` is specified, items of each board will be sorted by their dates from the most recent to the oldest ones.

---

### Add item

`$ board add <item text> [<item text> ...]`

* `-b/--board <name>` : add the item to this board

If no board `name` is specified, the item will be added to the default board.

Board will be automatically initialized if one does not exist.

---

### Remove item

`$ board remove <item id> [<item id> ...]`

---

### Clear board

Remove all items in the board.

`$ board clear [<name> [<name> ...]]`

If no board `name` is specified, all boards will be cleared.

---

### Tick / Mark / Star item

`$ board {tick, mark, star} <item id> [<item id> ...]`

Run this command again on the same item to untick/unmark/unstar the item.

---

### Edit item

`$ board edit <item id> <new text>`

---

### Tag item

`$ board tag <item id> [<item id> ...]`

* `-t/--text <tag text>` : tag the item with this text

If no `text` is given, existing tag of this item will be removed.

Color of the tag text is specified in [configurations](#configurations).

---

### Assign due date to item

`$ board due <item id> [<item id> ...]`

* `-d/--date` : due date of the item in the format of `<digit><d|w>[<digit><d|w> ...]` (`d` for day and `w` for week) e.g. `1w4d` for 1 week 4 days (11 days)

If no `date` is given, existing due date of this item will be removed.

---

### Move item

`$ board move <item id> [<item id> ...]`

* `-b/--board <name>` : move the item to this board

If board does not exist, one will be created.

---

### Rename board

`$ board rename <name> <new name>`

---

### Run item as command

`$ board run <item id>`

This will spawn a subprocess to execute the command.

**NOTE**: Some commands may not work properly in subprocess, such as pipes.

---

### Undo previous actions

`$ board undo`

#### Actions that cannot be undone:

* run
* undo
* export
* history

---

### Import board from external JSON file

`$ board import <path>`

**NOTE:** This will overwrite all the current data of boards.

The JSON file must be in a valid structure according to the following.

```json
{
    "Board Name": [
        {
            "id": 1,
            "text": "item text",
            "time": "<last modified timestamp>",
            "date": "<human readable date format (auto manipulated by noteboard)>",
            "due": "<due date timstamp>",
            "tick": false,
            "mark": false,
            "star": false,
            "tag": "<tag text>"
        }
    ]
}
```

---

### Export board data as JSON file

`$ board export`

* `-d/--dest <destination path>` : destination path of the exported file (directory)

The exported JSON file is named `board.json`.

---

### See historical changes

`$ board history`

---

## Configurations

**Path:** *~/.noteboard.json*

```json
{
    "StoragePath": "~/.noteboard/",
    "DefaultBoardName": "Board",
    "Tags": {
        "default": "BLUE"
    }
}
```
* `StoragePath` : path to the custom storage path (where the data and log file are stored)
* `DefaultBoardName` : default board name, is used when no board is specified when adding item
* `Tags` : colors preset of tags
  * `default` : **[required]** this color is used if no corresponding color of the tag text is found in config
  * `<tag text>` : specify your custom tag colors by adding `<tag text>: <color>` to `Tags` attribute of the config

**NOTE:** `color` must be upper cased and a valid attribute of `colorama.Fore`. E.g. `LIGHTBLUE_EX` for light blue and `CYAN` for cyan.

## Cautions

Some terminal emulators may not support dimmed (`Style.DIM`) & underlined (`\033[4m`) text.

The program also uses symbols such as `⭑` and `✔` which also may not be displayed properly if a wrong encodings is set.

## Credit

This project is inspired by [@Klaus Sinani](https://github.com/klaussinani)'s [taskbook](https://github.com/klaussinani/taskbook).

---

<div align="center">
    <sub><strong>~ crafted with ♥︎ by tnychn ~</strong></sub>
    <br>
    <sub><strong>MIT © 2019 Tony Chan</strong></sub>
</div>
