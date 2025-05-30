#!/usr/bin/env python3

import argparse
import json
import uuid
from datetime import datetime, date
from pathlib import Path

from click import style

# ===== Global toggles =====
USE_PLAIN = False
STORE: Path = Path("storage.json")

# ===== Styling helpers =====
RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
GRAY = "\033[90m"
BOLD = "\033[1m"
STYLE = lambda s: "" if USE_PLAIN else s
RESET, CYAN, GRAY, BOLD, GREEN = map(STYLE, (RESET, CYAN, GRAY, BOLD, GREEN))
EMOJI = {
    "added": "✅", "complete": "🎉", "backlog_add": "📥",
    "backlog_list": "📋", "backlog_pull": "📤", "newday": "🌅", "error": "❌"
}
emoji = lambda k: "" if USE_PLAIN else EMOJI.get(k, "")

# ===== Storage helpers =====

def load():
    """Function to load data."""
    return json.loads(STORE.read_text()) if STORE.exists() else {}

def save(data):
    """Function to save data."""
    STORE.write_text(json.dumps(data, indent=2))

def today_key():
    """Function to return today's date in a string."""
    return str(date.today())

def ensure_today(data):
    """Function to ensure today."""
    return data.setdefault(today_key(), {"todo": None, "done": [], "backlog": []})

# ===== Command functions =====
def prompt_next_action(today):
    """
    Ask user what to do after completing a task.
    Returns ("pull", None)  → pull from backlog
            ("add",  str)   → add the given task
            (None,   None)  → skip
    """
    has_backlog = bool(today["backlog"])
    if has_backlog:
        choice = input("[p] pull next from backlog, [a] add new, ENTER to skip ▶ ").strip().lower()
    else:
        choice = input("[a] add new, ENTER to skip ▶ ").strip().lower()

    if choice == "p" and has_backlog:
        return ("pull", None)
    if choice == "a":
        new_task = input("Describe the next task ▶ ").strip()
        if new_task:
            return ("add", new_task)
    return (None, None)


def cmd_add(args):
    data = load()
    today = ensure_today(data)
    if today["todo"]:
        print(f"{emoji('error')} Active task already exists: {today['todo']}")
        response = input(f"{style(BOLD)}➕ Would you like to add '{args.task}' to the backlog instead? [y/N]: {RESET}")
        if response.strip().lower() == 'y':
            ts = datetime.now().time().isoformat(timespec='seconds')
            today["backlog"].append({"task": args.task, "ts": ts})
            save(data)
            print(f"{emoji('backlog_add')} Added to backlog: {repr(args.task)}")
        return

    today["todo"] = args.task
    save(data)
    print(f"{emoji('added')} Added: {args.task}")
    cmd_status(args)

def cmd_done(args):
    data = load()
    today = ensure_today(data)
    if not today["todo"]:
        print(f"{emoji('error')} No active task to complete.")
        return

    # Mark task done
    today["done"].append({
        "id": uuid.uuid4().hex[:8],
        "task": today['todo'],
        "ts": datetime.now().isoformat(timespec='seconds')
    })
    print(f"{emoji('complete')} Completed: {repr(today['todo'])}")
    today["todo"] = None
    save(data)

    # Show summary
    cmd_status(args)

    # Skip interactive prompt in --plain mode
    if USE_PLAIN:
        return

    if today["backlog"]:
        print("\nWhat would you like to do next?")
        print("[b] Select task from backlog")
        print("[n] Add a new task")
        print("[Enter] Skip")

        choice = input("Enter your choice: ").strip().lower()

        if choice == "b":
            for i, item in enumerate(today["backlog"], 1):
                print(f" {i}. {item['task']} [{item['ts']}]")
            try:
                idx = input("Select a task [1-n]: ").strip()
                if idx == "":
                    print("Skipped selection.")
                    return
                idx = int(idx) - 1
                if 0 <= idx < len(today["backlog"]):
                    task = today["backlog"].pop(idx)
                    today["todo"] = task["task"]
                    print(f"{emoji('backlog_pull')} Pulled: {task['task']}")
                    save(data)
                    cmd_status(args)
            except ValueError:
                print(f"{emoji('error')} Invalid input.")

        elif choice == "n":
            new_task = input("Enter new task: ").strip()
            if new_task:
                today["todo"] = new_task
                save(data)
                print(f"{emoji('added')} Added: {new_task}")
                cmd_status(args)
        elif choice == "":
            print("No new task added.")
        else:
            print("Unknown input. Skipping.")


def cmd_status(_):
    today = ensure_today(load())
    today_str = today_key()
    print(f"\n=== TODAY: {today_str} ===")
    for it in today["done"]:
        ts = it['ts'].split('T')[1]
        print(f"{emoji('added')} {GREEN}{it['task']}{RESET} [{ts}]")
    if not today["done"]:
        print("No completed tasks yet.")
    print(f"{BOLD+CYAN if today['todo'] else GRAY}{today['todo'] or 'TBD'}{RESET}")
    print("="*(17+len(today_str)))

def cmd_newday(_):
    data = load()
    ensure_today(data)
    save(data)
    print(f"{emoji('newday')} New day initialized -> {today_key()}")

def cmd_backlog(args):
    data = load()
    today = ensure_today(data)
    if args.subcmd == "add":
        today["backlog"].append({"task": args.task,
                                 "ts": datetime.now().time().isoformat(timespec='seconds')})
        save(data)
        print(f"{emoji('backlog_add')} Backlog task added: {args.task}")
    elif args.subcmd == "list":
        print(f"{emoji('backlog_list')} Backlog:")
        for i, it in enumerate(today["backlog"],1):
            print(f" {i}. {it['task']} [{it['ts']}]")
    elif args.subcmd == "pull":
        if today["todo"]:
            print(f"{emoji('error')} Active task already exists: {today['todo']}")
            return
        if not today["backlog"]:
            print("No backlog items to pull.")
            return
        if hasattr(args, "index") and args.index:
            idx = args.index - 1
            if idx < 0 or idx >= len(today["backlog"]):
                print(f"{emoji('error')} Invalid index: {args.index}")
                return
        elif not USE_PLAIN:
            print(f"{emoji('backlog_list')} Backlog:")
            for i, item in enumerate(today["backlog"], 1):
                print(f" {i}. {repr(item['task'])} [{item['ts']}]")
            try:
                idx = int(input("Select task to pull [1-n]: ")) - 1
            except ValueError:
                print(f"{emoji('error')} Invalid input. Must be a number.")
                return
            if idx < 0 or idx >= len(today["backlog"]):
                print(f"{emoji('error')} Invalid index selected.")
                return
        else:
            idx = 0  # default to top item in plain/CI mode

        task = today["backlog"].pop(idx)
        today["todo"] = task["task"]
        save(data)
        print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task['task'])}")
        cmd_status(args)
    elif args.subcmd == "remove":
        index = args.index - 1
        if 0 <= index < len(today["backlog"]):
            removed = today["backlog"].pop(index)
            save(data)
            print(f"{emoji('error')} Removed from backlog: {repr(removed['task'])}")
        else:
            print(f"{emoji('error')} Invalid backlog index: {args.index}")

# ===== Argparse + main =====

def build_parser():
    p = argparse.ArgumentParser(description="One-task-at-a-time tracker")
    p.add_argument("--store", default=None, help="Custom storage path")
    p.add_argument("--plain", action="store_true", help="Disable emoji / colour")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("task", nargs="+")
    a.set_defaults(func=cmd_add)
    sub.add_parser("done").set_defaults(func=cmd_done)
    sub.add_parser("status").set_defaults(func=cmd_status)
    sub.add_parser("newday").set_defaults(func=cmd_newday)
    b = sub.add_parser("backlog")
    b_sub = b.add_subparsers(dest="subcmd", required=True)
    b_a = b_sub.add_parser("add")
    b_a.add_argument("task", nargs="+")
    b_a.set_defaults(func=cmd_backlog)
    b_sub.add_parser("list").set_defaults(func=cmd_backlog)
    b_pull = b_sub.add_parser("pull", help="Pull next backlog item as active")
    b_pull.add_argument("--index", type=int, help="Select specific backlog item by 1-based index")
    b_pull.set_defaults(func=cmd_backlog)
    b_remove = b_sub.add_parser("remove", help="Remove a backlog item by index")
    b_remove.add_argument("index", type=int, help="1-based index of item to remove")
    b_remove.set_defaults(func=cmd_backlog)
    return p

def main():
    args = build_parser().parse_args()

    if args.cmd == "add" or (args.cmd == "backlog" and args.subcmd == "add"):
        args.task = " ".join(args.task)

    global USE_PLAIN, STORE
    USE_PLAIN = args.plain
    if args.store:
        STORE = Path(args.store)

    args.func(args)

if __name__ == "__main__":
    main()
