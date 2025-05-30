#!/usr/bin/env python3
"""
TaskTracker - A minimal, one-task-at-a-time CLI tracker.

A command-line task management tool that enforces focus by allowing only one
active task at a time. Features a persistent backlog, interactive prompts,
and clean status displays with optional emoji/color output.

Usage:
    python tasker.py add "Task description"
    python tasker.py done
    python tasker.py backlog add "Future task"
    python tasker.py status
"""

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
EMOJI = {
    "added": "✅", "complete": "🎉", "backlog_add": "📥",
    "backlog_list": "📋", "backlog_pull": "📤", "newday": "🌅", "error": "❌"
}

def style_option(s):
    """Return styled text or empty string if plain mode is enabled."""
    return "" if USE_PLAIN else s

def emoji(k):
    """Return emoji for given key or empty string if plain mode is enabled."""
    return "" if USE_PLAIN else EMOJI.get(k, "")

RESET, CYAN, GRAY, BOLD, GREEN = map(style_option, (RESET, CYAN, GRAY, BOLD, GREEN))

# ===== Display/Formatting helpers =====

def format_backlog_timestamp(ts):
    """Format timestamp for display in backlog listings."""
    try:
        dt = datetime.fromisoformat(ts)
        date_str = dt.strftime('%m/%d')
        time_str = dt.strftime('%H:%M')
        return f"[{date_str} {time_str}]"
    except (ValueError, KeyError):
        return f"[{ts if ts else 'no timestamp'}]"

def print_backlog_list(backlog, title="Backlog"):
    """Print formatted backlog with consistent styling."""
    print(f"{emoji('backlog_list')} {title}:")
    for i, item in enumerate(backlog, 1):
        timestamp = format_backlog_timestamp(item.get('ts', ''))
        print(f" {i}. {item['task']} {timestamp}")

# ===== Storage helpers =====

def load():
    """Load data from storage file, returning empty dict if file doesn't exist."""
    if STORE.exists():
        return json.loads(STORE.read_text(encoding='utf-8'))
    return {}

def save(data):
    """Save data to storage file with UTF-8 encoding."""
    STORE.write_text(json.dumps(data, indent=2), encoding='utf-8')

def today_key():
    """Function to return today's date in a string."""
    return str(date.today())

def ensure_today(data):
    """Function to ensure today's date exists with proper structure."""
    # Ensure global backlog exists
    if "backlog" not in data:
        data["backlog"] = []

    # Ensure today's entry exists
    today = data.setdefault(today_key(), {"todo": None, "done": []})

    return today

def get_backlog(data):
    """Get the global backlog."""
    return data.setdefault("backlog", [])

def complete_current_task(today):
    """Mark the current task as completed."""
    today["done"].append({
        "id": uuid.uuid4().hex[:8],
        "task": today["todo"],
        "ts": datetime.now().isoformat(timespec="seconds")
    })
    print(f"{emoji('complete')} Completed: {repr(today['todo'])}")
    today["todo"] = None

def handle_next_task_selection(data, today):
    """Handle user selection of next task after completing current one."""
    backlog = get_backlog(data)

    # Show current backlog
    if backlog:
        print()
        print_backlog_list(backlog)
    else:
        print("\nBacklog is empty.")

    print("\nSelect next task:")
    print(" - Enter a number to pull from backlog")
    print(" - [n] Add a new task")
    print(" - [Enter] to skip")

    choice = input("> ").strip()

    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(backlog):
            task = backlog.pop(index)
            today["todo"] = task["task"]
            save(data)
            print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task['task'])}")
            cmd_status(None)  # Show status after pulling
        else:
            print(f"{emoji('error')} Invalid backlog index.")
    elif choice.lower() == "n":
        new_task = input("Enter new task: ").strip()
        if new_task:
            today["todo"] = new_task
            save(data)
            print(f"{emoji('added')} Added: {repr(new_task)}")
            cmd_status(None)  # Show status after adding
    else:
        print("No new task added.")

# ===== Command functions =====
def prompt_next_action(data):
    """
    Ask user what to do after completing a task.
    
    Args:
        data: The full data dictionary containing backlog
    
    Returns:
        tuple: ("pull", None) to pull from backlog,
               ("add", str) to add the given task,
               (None, None) to skip
    """
    backlog = get_backlog(data)
    has_backlog = bool(backlog)
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
    """Add a new task or offer to add to backlog if active task exists."""
    data = load()
    today = ensure_today(data)
    if today["todo"]:
        print(f"{emoji('error')} Active task already exists: {today['todo']}")
        response = input(f"{style(BOLD)}➕ Would you like to add '{args.task}' to the backlog instead? [y/N]: {style(RESET)}")
        if response.strip().lower() == 'y':
            ts = datetime.now().isoformat(timespec='seconds')
            get_backlog(data).append({"task": args.task, "ts": ts})
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

    # Complete the task
    complete_current_task(today)
    save(data)
    cmd_status(args)
    
    # Handle next task selection
    handle_next_task_selection(data, today)


def cmd_status(_):
    data = load()
    today = ensure_today(data)
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
    backlog = get_backlog(data)
    
    if args.subcmd == "add":
        backlog.append({"task": args.task,
                       "ts": datetime.now().isoformat(timespec='seconds')})
        save(data)
        print(f"{emoji('backlog_add')} Backlog task added: {args.task}")
    elif args.subcmd == "list":
        print_backlog_list(backlog)
    elif args.subcmd == "pull":
        if today["todo"]:
            print(f"{emoji('error')} Active task already exists: {today['todo']}")
            return
        if not backlog:
            print("No backlog items to pull.")
            return
        if hasattr(args, "index") and args.index:
            idx = args.index - 1
            if idx < 0 or idx >= len(backlog):
                print(f"{emoji('error')} Invalid index: {args.index}")
                return
        elif not USE_PLAIN:
            print_backlog_list(backlog)
            try:
                idx = int(input("Select task to pull [1-n]: ")) - 1
            except ValueError:
                print(f"{emoji('error')} Invalid input. Must be a number.")
                return
            if idx < 0 or idx >= len(backlog):
                print(f"{emoji('error')} Invalid index selected.")
                return
        else:
            idx = 0  # default to top item in plain/CI mode

        task = backlog.pop(idx)
        today["todo"] = task["task"]
        save(data)
        print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task['task'])}")
        cmd_status(args)
    elif args.subcmd == "remove":
        index = args.index - 1
        if 0 <= index < len(backlog):
            removed = backlog.pop(index)
            save(data)
            print(f"{emoji('error')} Removed from backlog: {repr(removed['task'])}")
        else:
            print(f"{emoji('error')} Invalid backlog index: {args.index}")

# ===== Argparse + main =====

def build_parser():
    """Build and configure the argument parser for all CLI commands."""
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
    """Main entry point for the task tracker CLI."""
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
