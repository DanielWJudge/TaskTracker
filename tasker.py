#!/usr/bin/env python3
"""
tasktracker.py (Status with Emoji)
"""

import argparse, json, sys, uuid
from datetime import datetime, date
from pathlib import Path

STORE = Path(__file__).with_name("storage.json")

RESET = "\033[0m"
CYAN = "\033[96m"
GRAY = "\033[90m"
BOLD = "\033[1m"

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

def cmd_add(args):
    data = load()
    today = ensure_today(data)
    if today["todo"]:
        print(f"❌ Active task already exists: {today['todo']}")
        return
    today["todo"] = args.task
    save(data)
    print(f"✅ Added: {args.task}")

def cmd_done(_):
    data = load()
    today = ensure_today(data)
    if not today["todo"]:
        print("❌ No active task to complete.")
        return
    today["done"].append(
        {"id": uuid.uuid4().hex[:8], "task": today["todo"], "ts": datetime.now().isoformat(timespec='seconds')}
    )
    print(f"🎉 Completed: {today['todo']}")
    today["todo"] = None
    save(data)
    cmd_status(None)  # fall-through display

def cmd_status(_):
    data = load()
    today = ensure_today(data)
    today_str = today_key()
    print(f"\n=== TODAY: {today_str} ===")
    if today["done"]:
        for item in today["done"]:
            ts = item["ts"].split('T')[1]
            print(f"✅ {item['task']} [{ts}]")
    else:
        print("No completed tasks yet.")
    # Highlight active task or show TBD in gray
    if today['todo']:
        print(f"{BOLD}{CYAN}{today['todo']}{RESET}")
    else:
        print(f"{GRAY}TBD{RESET}")
    print("=" * (17 + len(today_str)) + "\n")

def cmd_newday(_):
    data = load()
    ensure_today(data)  # side-effect creates bucket if needed
    save(data)
    print(f"🌅 New day initialized -> {today_key()}")

def parse_args():
    p = argparse.ArgumentParser(description="One-task-at-a-time tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add an active task")
    a.add_argument("task", nargs="+", help="Task description")
    a.set_defaults(func=cmd_add, task=lambda x: None)

    d = sub.add_parser("done", help="Mark active task complete")
    d.set_defaults(func=cmd_done)

    s = sub.add_parser("status", help="Show status")
    s.set_defaults(func=cmd_status)

    n = sub.add_parser("newday", help="Initialize a fresh day")
    n.set_defaults(func=cmd_newday)

    args = p.parse_args()
    # fix lambda-artifact for add
    if args.cmd == "add":
        args.task = " ".join(args.task)
    return args

def main():
    args = parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
