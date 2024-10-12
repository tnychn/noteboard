import argparse
import sys
import os
import re
import shlex
import logging
from colorama import init, deinit, Fore, Back, Style

from . import DEFAULT_BOARD, TAGS
from .__version__ import __version__
from .storage import Storage, History, NoteboardException
from .utils import time_diff, add_date, to_timestamp, to_datetime

logger = logging.getLogger("noteboard")
COLORS = {
    "add": "GREEN",
    "remove": "LIGHTMAGENTA_EX",
    "clear": "RED",
    "run": "BLUE",

    "tick": "GREEN",
    "mark": "YELLOW",
    "star": "YELLOW",
    "tag": "LIGHTBLUE_EX",
    "untick": "GREEN",
    "unmark": "YELLOW",
    "unstar": "YELLOW",
    "untag": "LIGHTBLUE_EX",

    "due": "LIGHTBLUE_EX",
    "edit": "LIGHTCYAN_EX",
    "move": "LIGHTCYAN_EX",
    "rename": "LIGHTCYAN_EX",
    "undo": "LIGHTCYAN_EX",
    "import": "",
    "export": "",
}


def p(*args, **kwargs):
    # print text with spaces indented
    print(" ", *args, **kwargs)


def error_print(text):
    print(Style.BRIGHT + Fore.LIGHTRED_EX + "✘ " + text)


def get_fore_color(action):
    color = COLORS.get(action, "")
    if color == "":
        return ""
    return eval("Fore." + color)


def get_back_color(action):
    color = COLORS.get(action, "")
    if color == "":
        return Back.LIGHTWHITE_EX
    return eval("Back." + color)


def print_footer():
    with Storage() as s:
        shelf = dict(s.shelf)
    ticks = 0
    marks = 0
    stars = 0
    for board in shelf:
        for item in shelf[board]:
            if item["tick"] is True:
                ticks += 1
            if item["mark"] is True:
                marks += 1
            if item["star"] is True:
                stars += 1
    p(Fore.GREEN + str(ticks), Fore.LIGHTBLACK_EX + "done •", Fore.LIGHTRED_EX + str(marks), Fore.LIGHTBLACK_EX + "marked •", Fore.LIGHTYELLOW_EX + str(stars), Fore.LIGHTBLACK_EX + "starred")


def print_total():
    with Storage() as s:
        total = s.total
    p(Fore.LIGHTCYAN_EX + "Total Items:", Style.DIM + str(total))


def run(args):
    color = get_fore_color("run")
    item = args.item
    with Storage() as s:
        i = s.get_item(item)
    # Run
    import subprocess
    cmd = shlex.split(i["text"])
    if "|" in cmd:
        command = i["text"]
        shell = True
    elif len(cmd) == 1:
        command = i["text"]
        shell = True
    else:
        command = cmd
        shell = False
    execuatble = os.environ.get("SHELL", None)
    process = subprocess.Popen(command, shell=shell, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, stdin=subprocess.PIPE, executable=execuatble)
    # Live stdout output
    deinit()
    print(color + "[>] Running item" + Fore.RESET, Style.BRIGHT + str(i["id"]) + Style.RESET_ALL, color + "as command...\n" + Fore.RESET)
    for line in iter(process.stdout.readline, b""):
        sys.stdout.write(line.decode("utf-8"))
    process.wait()


def add(args):
    color = get_fore_color("add")
    items = args.item
    board = args.board
    print()
    with Storage() as s:
        for item in items:
            if not item:
                error_print("Text must not be empty")
                return
            s.save_history()
            i = s.add_item(board, item)
            p(color + "[+] Added item", Style.BRIGHT + str(i["id"]), color + "to", Style.BRIGHT + (board or DEFAULT_BOARD))
            s.write_history("add", "added item {} [{}] to board [{}]".format(str(i["id"]), item, (board or DEFAULT_BOARD)))
    print_total()
    print()


def remove(args):
    color = get_fore_color("remove")
    items = args.item
    print()
    with Storage() as s:
        for item in items:
            s.save_history()
            i, board = s.remove_item(item)
            p(color + "[-] Removed item", Style.BRIGHT + str(i["id"]), color + "on", Style.BRIGHT + board)
            s.write_history("remove", "removed item {} [{}] from board [{}]".format(str(i["id"]), item, (board or DEFAULT_BOARD)))
    print_total()
    print()


def clear(args):
    color = get_fore_color("clear")
    boards = args.board
    print()
    with Storage() as s:
        if boards:
            for board in boards:
                s.save_history()
                amt = s.clear_board(board)
                p(color + "[x] Cleared", Style.DIM + str(amt) + Style.RESET_ALL, color + "items on", Style.BRIGHT + board)
                s.write_history("clear", "cleared {} items on board [{}]".format(str(amt), board))
        else:
            s.save_history()
            amt = s.clear_board(None)
            p(color + "[x] Cleared", Style.DIM + str(amt) + Style.RESET_ALL, color + "items on all boards")
            s.write_history("clear", "cleared {} items on all board".format(str(amt)))
    print_total()
    print()


def tick(args):
    color = get_fore_color("tick")
    items = args.item
    with Storage() as s:
        print()
        for item in items:
            state = not s.get_item(item)["tick"]
            s.save_history()
            i = s.modify_item(item, "tick", state)
            if state is True:
                p(color + "[✓] Ticked item", Style.BRIGHT + str(i["id"]), color)
                s.write_history("tick", "ticked item {} [{}]".format(str(i["id"]), i["text"]))
            else:
                p(color + "[✓] Unticked item", Style.BRIGHT + str(i["id"]), color)
                s.write_history("untick", "unticked item {} [{}]".format(str(i["id"]), i["text"]))
    print()


def mark(args):
    color = get_fore_color("mark")
    items = args.item
    with Storage() as s:
        print()
        for item in items:
            state = not s.get_item(item)["mark"]
            s.save_history()
            i = s.modify_item(item, "mark", state)
            if state is True:
                p(color + "[!] Marked item", Style.BRIGHT + str(i["id"]))
                s.write_history("mark", "marked item {} [{}]".format(str(i["id"]), i["text"]))
            else:
                p(color + "[!] Unmarked item", Style.BRIGHT + str(i["id"]))
                s.write_history("unmark", "unmarked item {} [{}]".format(str(i["id"]), i["text"]))
    print()


def star(args):
    color = get_fore_color("star")
    items = args.item
    with Storage() as s:
        print()
        for item in items:
            state = not s.get_item(item)["star"]
            s.save_history()
            i = s.modify_item(item, "star", state)
            if state is True:
                p(color + "[*] Starred item", Style.BRIGHT + str(i["id"]))
                s.write_history("star", "starred item {} [{}]".format(str(i["id"]), i["text"]))
            else:
                p(color + "[*] Unstarred item", Style.BRIGHT + str(i["id"]))
                s.write_history("unstar", "unstarred item {} [{}]".format(str(i["id"]), i["text"]))
    print()


def edit(args):
    color = get_fore_color("edit")
    item = args.item
    text = (args.text or "").strip()
    if text == "":
        error_print("Text must not be empty")
        return
    with Storage() as s:
        s.save_history()
        i = s.modify_item(item, "text", text)
        s.write_history("edit", "editted item {} from [{}] to [{}]".format(str(i["id"]), i["text"], text))
    print()
    p(color + "[~] Edited text of item", Style.BRIGHT + str(i["id"]), color + "from", i["text"], color + "to", text)
    print()


def tag(args):
    color = get_fore_color("tag")
    items = args.item
    text = (args.text or "").strip()
    if len(text) > 10:
        error_print("Tag text length should not be longer than 10 characters")
        return
    if text != "":
        c = TAGS.get(text, "") or TAGS["default"]
        tag_color = eval("Fore." + c.upper())
        tag_text = text.replace(" ", "-")
    else:
        tag_text = ""
    with Storage() as s:
        print()
        for item in items:
            s.save_history()
            i = s.modify_item(item, "tag", tag_text)
            if text != "":
                p(color + "[#] Tagged item", Style.BRIGHT + str(i["id"]), color + "with", tag_color + tag_text)
                s.write_history("tag", "tagged item {} [{}] with tag text [{}]".format(str(i["id"]), i["text"], text))
            else:
                p(color + "[#] Untagged item", Style.BRIGHT + str(i["id"]))
                s.write_history("tag", "untagged item {} [{}]".format(str(i["id"]), i["text"]))
    print()


def due(args):
    color = get_fore_color("due")
    items = args.item
    date = args.date or ""
    if date and not re.match(r"\d+[d|w]", date):
        error_print("Invalid date pattern format")
        return
    match = re.findall(r"\d+[d|w]", date)
    if date:
        days = 0
        for m in match:
            if m[-1] == "d":
                days += int(m[:-1])
            elif m[-1] == "w":
                days += int(m[:-1]) * 7
        duedate = add_date(days)
        ts = to_timestamp(duedate)
    else:
        ts = None

    with Storage() as s:
        print()
        for item in items:
            s.save_history()
            i = s.modify_item(item, "due", ts)
            if ts:
                p(color + "[:] Assigned due date", duedate, color + "to", Style.BRIGHT + str(item))
                s.write_history("due", "assiged due date [{}] to item {} [{}]".format(duedate, str(i["id"]), i["text"]))
            else:
                p(color + "[:] Unassigned due date of item", Style.BRIGHT + str(item))
                s.write_history("due", "unassiged due date of item {} [{}]".format(str(i["id"]), i["text"]))
    print()


def move(args):
    color = get_fore_color("move")
    items = args.item
    board = args.board
    with Storage() as s:
        print()
        for item in items:
            s.save_history()
            i, b = s.move_item(item, board)
            p(color + "[&] Moved item", Style.BRIGHT + str(i["id"]), color + "to", Style.BRIGHT + board)
            s.write_history("move", "moved item {} [{}] from board [{}] to [{}]".format(str(i["id"]), i["text"], b, board))
    print()


def rename(args):
    color = get_fore_color("rename")
    board = args.board
    new = (args.new or "").strip()
    if new == "":
        error_print("Board name must not be empty")
        return
    with Storage() as s:
        print()
        s.get_board(board)  # try to get -> to test existence of the board
        s.save_history()
        s.shelf[new] = s.shelf.pop(board)
        p(color + "[~] Renamed", Style.BRIGHT + board, color + "to", Style.BRIGHT + new)
        s.write_history("rename", "renamed board [{}] to [{}]".format(board, new))
    print()


def undo(_):
    color = get_fore_color("undo")
    with Storage() as s:
        all_hist = s.history.load()
        hist = [i for i in all_hist if i["data"] is not None]
        if len(hist) == 0:
            error_print("Already at oldest change")
            return
        state = hist[-1]
        print()
        p(color + Style.BRIGHT + "Last Action:")
        p("=>", get_fore_color(state["action"]) + state["info"])
        print()
        ask = input("[?] Continue (y/n) ? ")
        if ask != "y":
            error_print("Operation aborted")
            return
        s.history.revert()
        print(color + "[^] Undone", "=>", get_fore_color(state["action"]) + state["info"])


def import_(args):
    color = get_fore_color("import")
    path = args.path
    with Storage() as s:
        s.save_history()
        full_path = s.import_(path)
        s.write_history("import", "imported boards from [{}]".format(full_path))
    print()
    p(color + "[I] Imported boards from", Style.BRIGHT + full_path)
    print_total()
    print()


def export(args):
    color = get_fore_color("export")
    dest = args.dest
    path = os.path.abspath(os.path.expanduser(dest))
    if os.path.isfile(path):
        print("[i] File {} already exists".format(path))
        ask = input("[?] Overwrite (y/n) ? ")
        if ask != "y":
            error_print("Operation aborted")
            return
    with Storage() as s:
        full_path = s.export(path)
        s.write_history("export", "exported boards to [{}]".format(full_path))
    print()
    p(color + "[E] Exported boards to", Style.BRIGHT + full_path)
    print()


def history(_):
    hist = History.load()
    for action in hist:
        name = action["action"]
        info = action["info"]
        date = action["date"]
        print(Fore.LIGHTYELLOW_EX + date, get_back_color(name) + Fore.BLACK + name.upper().center(9), info)


def display_board(shelf, date=False, timeline=False):
    # print initial help message
    if not shelf:
        print()
        c = "`board --help`"
        p(Style.BRIGHT + "Type", Style.BRIGHT + Fore.YELLOW + c, Style.BRIGHT + "to get started")

    for board in shelf:
        # Print Board title
        if len(shelf[board]) == 0:
            continue
        print()
        p("\033[4m" + Style.BRIGHT + board, Fore.LIGHTBLACK_EX + "[{}]".format(len(shelf[board])))

        # Print Item
        for item in shelf[board]:
            mark = Fore.BLUE + "●"
            text_color = ""
            tag_text = ""

            # tick
            if item["tick"] is True:
                mark = Fore.GREEN + "✔"
                text_color = Fore.LIGHTBLACK_EX

            # mark
            if item["mark"] is True:
                if item["tick"] is False:
                    mark = Fore.LIGHTRED_EX + "!"
                text_color = Style.BRIGHT + Fore.RED

            # tag
            if item["tag"]:
                c = TAGS.get(item["tag"], "") or TAGS["default"]
                tag_color = eval("Fore." + c.upper())
                tag_text = " " + tag_color + "(" + item["tag"] + ")"

            # Star
            star = " "
            if item["star"] is True:
                star = Fore.LIGHTYELLOW_EX + "⭑"

            # Day difference
            days = time_diff(item["time"]).days
            if days <= 0:
                day_text = ""
            else:
                day_text = Fore.LIGHTBLACK_EX + "{}d".format(days)

            # Due date
            due_text = ""
            color = ""
            if item["due"]:
                due_days = time_diff(item["due"], reverse=True).days + 1  # + 1 because today is included
                if due_days == 0:
                    text = "today"
                    color = Fore.RED
                elif due_days == 1:
                    text = "tomorrow"
                    color = Fore.YELLOW
                elif due_days == -1:
                    text = "yesterday"
                    color = Fore.BLUE
                elif due_days < 0:
                    text = "{}d ago".format(due_days*-1)
                elif due_days > 0:
                    text = "{}d".format(due_days)
                due_text = "{}(due: {}{})".format(Fore.LIGHTBLACK_EX, color + text, Style.RESET_ALL + Fore.LIGHTBLACK_EX)

            # print text all together
            if date is True and timeline is False:
                p(star, Fore.LIGHTMAGENTA_EX + str(item["id"]).rjust(2), mark, text_color + item["text"], tag_text, Fore.LIGHTBLACK_EX + str(item["date"]),
                  (Fore.LIGHTBLACK_EX + "(due: {})".format(color + str(to_datetime(item["due"])) + Fore.LIGHTBLACK_EX)) if item["due"] else "")
            else:
                p(star, Fore.LIGHTMAGENTA_EX + str(item["id"]).rjust(2), mark, text_color + item["text"] + (Style.RESET_ALL + Fore.LIGHTBLUE_EX + "  @" + item["board"] if timeline else ""),
                  tag_text, day_text, due_text)
    print()
    print_footer()
    print_total()
    print()


def main():
    description = (Style.BRIGHT + "    \033[4mNoteboard" + Style.RESET_ALL + " lets you manage your " + Fore.YELLOW + "notes" + Fore.RESET + " & " + Fore.CYAN + "tasks" + Fore.RESET
                   + " in a " + Fore.LIGHTMAGENTA_EX + "tidy" + Fore.RESET + " and " + Fore.LIGHTMAGENTA_EX + "fancy" + Fore.RESET + " way.")
    epilog = (
        "Examples:\n"
        '  $ board add "improve cli" -b "Todo List"\n'
        '  $ board remove 2 4\n'
        '  $ board clear "Todo List" "Coding"\n'
        '  $ board edit 1 "improve cli"\n'
        '  $ board tag 1 6 -t "enhancement" -c GREEN\n'
        '  $ board tick 1 5 9\n'
        '  $ board move 2 3 -b "Destination"\n'
        '  $ board import ~/Documents/board.json\n'
        '  $ board export ~/Documents/save.json\n\n'
        "{0}crafted with {1}\u2764{2} by tnychn{3} (https://github.com/tnychn/noteboard)".format(Style.BRIGHT, Fore.RED, Fore.RESET, Style.RESET_ALL)
    )
    parser = argparse.ArgumentParser(
        prog="board",
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser._positionals.title = "Actions"
    parser._optionals.title = "Options"
    parser.add_argument("--version", action="version", version="noteboard " + __version__)
    parser.add_argument("-d", "--date", help="show boards with the added date of every item", default=False, action="store_true", dest="d")
    parser.add_argument("-s", "--sort", help="show boards with items on each board sorted alphabetically", default=False, action="store_true", dest="s")
    parser.add_argument("-t", "--timeline", help="show boards in timeline view, ignore the -d/--date option", default=False, action="store_true", dest="t")
    subparsers = parser.add_subparsers()

    add_parser = subparsers.add_parser("add", help=get_fore_color("add") + "[+] Add an item to a board" + Fore.RESET)
    add_parser.add_argument("item", help="the item you want to add", type=str, metavar="<item text>", nargs="+")
    add_parser.add_argument("-b", "--board", help="the board you want to add the item to (default: {})".format(DEFAULT_BOARD), type=str, metavar="<name>")
    add_parser.set_defaults(func=add)

    remove_parser = subparsers.add_parser("remove", help=get_fore_color("remove") + "[-] Remove items" + Fore.RESET)
    remove_parser.add_argument("item", help="id of the item you want to remove", type=int, metavar="<item id>", nargs="+")
    remove_parser.set_defaults(func=remove)

    clear_parser = subparsers.add_parser("clear", help=get_fore_color("clear") + "[x] Clear all items on a/all board(s)" + Fore.RESET)
    clear_parser.add_argument("board", help="clear this specific board", type=str, metavar="<name>", nargs="*")
    clear_parser.set_defaults(func=clear)

    tick_parser = subparsers.add_parser("tick", help=get_fore_color("tick") + "[✓] Tick/Untick an item" + Fore.RESET)
    tick_parser.add_argument("item", help="id of the item you want to tick/untick", type=int, metavar="<item id>", nargs="+")
    tick_parser.set_defaults(func=tick)

    mark_parser = subparsers.add_parser("mark", help=get_fore_color("mark") + "[!] Mark/Unmark an item" + Fore.RESET)
    mark_parser.add_argument("item", help="id of the item you want to mark/unmark", type=int, metavar="<item id>", nargs="+")
    mark_parser.set_defaults(func=mark)

    star_parser = subparsers.add_parser("star", help=get_fore_color("star") + "[*] Star/Unstar an item" + Fore.RESET)
    star_parser.add_argument("item", help="id of the item you want to star/unstar", type=int, metavar="<item id>", nargs="+")
    star_parser.set_defaults(func=star)

    edit_parser = subparsers.add_parser("edit", help=get_fore_color("edit") + "[~] Edit the text of an item" + Fore.RESET)
    edit_parser.add_argument("item", help="id of the item you want to edit", type=int, metavar="<item id>")
    edit_parser.add_argument("text", help="new text to replace the old one", type=str, metavar="<new text>")
    edit_parser.set_defaults(func=edit)

    tag_parser = subparsers.add_parser("tag", help=get_fore_color("tag") + "[#] Tag an item with text" + Fore.RESET)
    tag_parser.add_argument("item", help="id of the item you want to tag", type=int, metavar="<item id>", nargs="+")
    tag_parser.add_argument("-t", "--text", help="text of tag (do not specify this argument to untag)", type=str, metavar="<tag text>")
    tag_parser.set_defaults(func=tag)

    due_parser = subparsers.add_parser("due", help=get_fore_color("due") + "[:] Assign a due date to an item" + Fore.RESET)
    due_parser.add_argument("item", help="id of the item", type=int, metavar="<item id>", nargs="+")
    due_parser.add_argument("-d", "--date", help="due date of the item in the format of `<digit><d|w>` e.g. '1w4d' for 1 week and 4 days (11 days)", type=str, metavar="<due date>")
    due_parser.set_defaults(func=due)

    run_parser = subparsers.add_parser("run", help=get_fore_color("run") + "[>] Run an item as command" + Fore.RESET)
    run_parser.add_argument("item", help="id of the item you want to run", type=int, metavar="<item id>")
    run_parser.set_defaults(func=run)

    move_parser = subparsers.add_parser("move", help=get_fore_color("move") + "[&] Move an item to another board" + Fore.RESET)
    move_parser.add_argument("item", help="id of the item you want to move", type=int, metavar="<item id>", nargs="+")
    move_parser.add_argument("-b", "--board", help="name of the destination board", type=str, metavar="<name>", required=True)
    move_parser.set_defaults(func=move)

    rename_parser = subparsers.add_parser("rename", help=get_fore_color("rename") + "[~] Rename the name of the board" + Fore.RESET)
    rename_parser.add_argument("board", help="name of the board you want to rename", type=str, metavar="<name>")
    rename_parser.add_argument("new", help="new name to replace the old one", type=str, metavar="<new name>")
    rename_parser.set_defaults(func=rename)

    undo_parser = subparsers.add_parser("undo", help=get_fore_color("undo") + "[^] Undo the last action" + Fore.RESET)
    undo_parser.set_defaults(func=undo)

    import_parser = subparsers.add_parser("import", help=get_fore_color("import") + "[I] Import and load boards from JSON file" + Fore.RESET)
    import_parser.add_argument("path", help="path to the target import file", type=str, metavar="<path>")
    import_parser.set_defaults(func=import_)

    export_parser = subparsers.add_parser("export", help=get_fore_color("export") + "[E] Export boards as a JSON file" + Fore.RESET)
    export_parser.add_argument("-d", "--dest", help="destination of the exported file (default: ./board.json)", type=str, default="./board.json", metavar="<destination path>")
    export_parser.set_defaults(func=export)

    history_parser = subparsers.add_parser("history", help="[.] Prints out the historical changes")
    history_parser.set_defaults(func=history)

    args = parser.parse_args()
    init(autoreset=True)
    try:
        args.func
    except AttributeError:
        with Storage() as s:
            shelf = dict(s.shelf)

        if args.s:
            # sort alphabetically
            for board in shelf:
                shelf[board] = sorted(shelf[board], key=lambda x: x["text"].lower())
        elif args.d:
            # sort by date
            for board in shelf:
                shelf[board] = sorted(shelf[board], key=lambda x: x["time"], reverse=True)

        if args.t:
            data = {}
            for board in shelf:
                for item in shelf[board]:
                    if item["date"]:
                        if item["date"] not in data:
                            data[item["date"]] = []
                        item.update({"board": board})
                        data[item["date"]].append(item)
            shelf = data
        display_board(shelf, date=args.d, timeline=args.t)
    else:
        try:
            args.func(args)
        except KeyboardInterrupt:
            error_print("Operation aborted")
        except NoteboardException as e:
            error_print(str(e))
            logger.debug("(ERROR)", exc_info=True)
        except Exception as e:
            error_print(str(e))
            logger.debug("(ERROR)", exc_info=True)
    deinit()


if __name__ == "__main__":
    main()
