#!/usr/bin/env python3
"""
tasktracker.py (Improved with Color Class, Helpers, and CLI Enhancements)
"""

import argparse, json, sys, uuid
from datetime import datetime, date
from pathlib import Path

VERSION = "0.1.0"

class Color:
    RESET = "\033[0m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"

STORE = Path(__file__).with_name("storage.json")

def load():
    if STORE.exists():
        return json.loads(STORE.read_text())
    return {}

def save(data):
    STORE.write_text(json.dumps(data, indent=2))

def today_key():
    return str(date.today())

def ensure_today(data):
    key = today_key()
    if key not in data:
        data[key] = {"todo": None, "done": [], "backlog": []}
    return data[key]

def print_status(today):
    today_str = today_key()
    print(f"\n=== TODAY: {today_str} ===")
    if today.get("done"):
        for item in today["done"]:
            ts = item["ts"].split('T')[1]
            print(f"✅ {item['task']} [{ts}]")
    else:
        print("No completed tasks yet.")

    if today.get("todo"):
        print(f"{Color.BOLD}{Color.CYAN}{today['todo']}{Color.RESET}")
    else:
        print(f"{Color.GRAY}TBD{Color.RESET}")
    print("=" * (17 + len(today_str)) + "\n")

def cmd_add(args):
    data = load()
    today = ensure_today(data)
    if today.get("todo"):
        print(f"❌ Active task already exists: {today['todo']}")
        return
    today["todo"] = args.task
    save(data)
    print(f"✅ Added: {args.task}")

def cmd_done(args):
    data = load()
    today = ensure_today(data)
    if not today.get("todo"):
        print("❌ No active task to complete.")
        return
    today["done"].append(
        {"id": uuid.uuid4().hex[:8], "task": today["todo"], "ts": datetime.now().isoformat(timespec='seconds')}
    )
    print(f"🎉 Completed: {today['todo']}")
    today["todo"] = None
    save(data)
    print_status(today)

def cmd_status(args):
    data = load()
    today = ensure_today(data)
    print_status(today)

def cmd_newday(args):
    data = load()
    ensure_today(data)
    save(data)
    print(f"🌅 New day initialized -> {today_key()}")

def cmd_about(args):
    print(f"TaskTracker CLI v{VERSION} — One-task-at-a-time tool")

def parse_args():
    p = argparse.ArgumentParser(description="One-task-at-a-time tracker")
    p.add_argument("--store", default="storage.json", help="Optional path to storage file")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add an active task")
    a.add_argument("task", nargs="+", help="Task description")
    a.set_defaults(func=cmd_add)

    d = sub.add_parser("done", help="Mark active task complete")
    d.set_defaults(func=cmd_done)

    s = sub.add_parser("status", help="Show status")
    s.set_defaults(func=cmd_status)

    n = sub.add_parser("newday", help="Initialize a fresh day")
    n.set_defaults(func=cmd_newday)

    v = sub.add_parser("about", help="Show tool version")
    v.set_defaults(func=cmd_about)

    args = p.parse_args()
    if args.cmd == "add":
        args.task = " ".join(args.task)
    return args

def main():
    global STORE
    args = parse_args()
    STORE = Path(args.store)
    args.func(args)

if __name__ == "__main__":
    main()
