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
import sys
import locale
from datetime import datetime, date
from pathlib import Path

# ===== Global toggles =====
USE_PLAIN = False
STORE: Path = Path("storage.json")

# ===== Configuration =====
class Config:
    """Configuration constants for TaskTracker."""
    MAX_TASK_LENGTH = 500
    STORAGE_ENCODING = 'utf-8'
    DATE_FORMAT = '%m/%d'
    TIME_FORMAT = '%H:%M'

# ===== Console setup =====
def setup_console_encoding():
    """Set up console encoding for better Unicode support."""
    if sys.platform == "win32":
        try:
            # Try to enable UTF-8 mode on Windows
            import codecs
            if hasattr(sys.stdout, 'detach'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
            if hasattr(sys.stderr, 'detach'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
        except:
            # If that fails, we'll rely on safe_print fallbacks
            pass

def safe_print(text, **kwargs):
    """Print text with Unicode error handling."""
    try:
        print(text, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacement characters
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(safe_text, **kwargs)

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

def style(s):
    """Return styled text or empty string if plain mode is enabled."""
    if USE_PLAIN:
        return ""
    try:
        # Test if the string can be encoded safely
        encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
        s.encode(encoding, errors='strict')
        return s
    except (UnicodeEncodeError, LookupError, AttributeError):
        # If can't encode safely, return empty
        return ""

def emoji(k):
    """Return emoji for given key or empty string if plain mode is enabled."""
    if USE_PLAIN:
        return ""
    
    emoji_char = EMOJI.get(k, "")
    if not emoji_char:
        return ""
    
    try:
        # Test if emoji can be encoded safely
        encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
        emoji_char.encode(encoding, errors='strict')
        return emoji_char
    except (UnicodeEncodeError, LookupError, AttributeError):
        # Return ASCII alternatives in plain mode or encoding issues
        ascii_alternatives = {
            "added": "[OK]",
            "complete": "[DONE]", 
            "backlog_add": "[+]",
            "backlog_list": "[-]",
            "backlog_pull": "[>]",
            "newday": "[NEW]",
            "error": "[!]"
        }
        return ascii_alternatives.get(k, "")

RESET, CYAN, GRAY, BOLD, GREEN = map(style, (RESET, CYAN, GRAY, BOLD, GREEN))

# ===== Input Validation =====

def validate_task_name(task):
    """
    Validate task name input.
    
    Args:
        task: The task name to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not task:
        return False, "Task name cannot be empty."
    
    task_stripped = task.strip()
    if not task_stripped:
        return False, "Task name cannot be only whitespace."
    
    if len(task_stripped) > Config.MAX_TASK_LENGTH:
        return False, f"Task name too long (max {Config.MAX_TASK_LENGTH} characters)."
    
    # Check for potentially problematic characters
    if '\n' in task_stripped or '\r' in task_stripped:
        return False, "Task name cannot contain line breaks."
        
    return True, ""

def safe_input(prompt, validator=None):
    """
    Get user input with optional validation and Unicode safety.
    
    Args:
        prompt: The input prompt to display
        validator: Optional function that takes input and returns (valid, error_msg)
        
    Returns:
        str: The validated input, or None if user cancels/validation fails
    """
    try:
        # Make prompt safe for current console encoding
        safe_prompt = prompt
        try:
            # Get encoding safely, with fallbacks
            encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
            prompt.encode(encoding, errors='strict')
        except (UnicodeEncodeError, LookupError, AttributeError):
            # Fallback to ASCII-safe version
            safe_prompt = prompt.encode('ascii', errors='replace').decode('ascii')
        
        user_input = input(safe_prompt).strip()
        if validator:
            is_valid, error_msg = validator(user_input)
            if not is_valid:
                safe_print(f"{emoji('error')} {error_msg}")
                return None
        return user_input
    except (KeyboardInterrupt, EOFError):
        safe_print(f"\n{emoji('error')} Input cancelled.")
        return None

def safe_int_input(prompt, min_val=None, max_val=None):
    """
    Get integer input with validation and Unicode safety.
    
    Args:
        prompt: The input prompt to display
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        int or None: The validated integer, or None if invalid/cancelled
    """
    try:
        # Make prompt safe for current console encoding
        safe_prompt = prompt
        try:
            # Get encoding safely, with fallbacks
            encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
            prompt.encode(encoding, errors='strict')
        except (UnicodeEncodeError, LookupError, AttributeError):
            safe_prompt = prompt.encode('ascii', errors='replace').decode('ascii')
            
        user_input = input(safe_prompt).strip()
        if not user_input:
            return None
            
        value = int(user_input)
        if min_val is not None and value < min_val:
            safe_print(f"{emoji('error')} Value must be at least {min_val}.")
            return None
        if max_val is not None and value > max_val:
            safe_print(f"{emoji('error')} Value must be at most {max_val}.")
            return None
        return value
    except ValueError:
        safe_print(f"{emoji('error')} Invalid input. Must be a number.")
        return None
    except (KeyboardInterrupt, EOFError):
        safe_print(f"\n{emoji('error')} Input cancelled.")
        return None

# ===== Storage helpers =====

def load():
    """Load data from storage file, returning empty dict if file doesn't exist."""
    try:
        if STORE.exists():
            content = STORE.read_text(encoding=Config.STORAGE_ENCODING)
            return json.loads(content)
        return {}
    except json.JSONDecodeError as e:
        safe_print(f"{emoji('error')} Storage file corrupted: {e}")
        safe_print(f"Creating backup and starting fresh...")
        # Create backup of corrupted file
        backup_path = STORE.with_suffix('.json.backup')
        try:
            STORE.rename(backup_path)
            safe_print(f"Corrupted file backed up to: {backup_path}")
        except OSError:
            safe_print("Could not create backup of corrupted file.")
        return {}
    except (OSError, PermissionError) as e:
        safe_print(f"{emoji('error')} Cannot read storage file: {e}")
        return {}

def save(data):
    """Save data to storage file with UTF-8 encoding and error handling."""
    try:
        content = json.dumps(data, indent=2)
        STORE.write_text(content, encoding=Config.STORAGE_ENCODING)
        return True
    except (OSError, PermissionError) as e:
        safe_print(f"{emoji('error')} Cannot save to storage file: {e}")
        safe_print("Changes will be lost when the program exits.")
        return False
    except (TypeError, ValueError) as e:
        safe_print(f"{emoji('error')} Data serialization error: {e}")
        return False

def today_key():
    """Return today's date as a string in YYYY-MM-DD format."""
    return str(date.today())

def ensure_today(data):
    """Ensure today's date exists in data with proper structure and return today's data."""
    # Ensure global backlog exists
    if "backlog" not in data:
        data["backlog"] = []
    
    # Ensure today's entry exists
    today = data.setdefault(today_key(), {"todo": None, "done": []})
    
    return today

def get_backlog(data):
    """Get the global backlog, creating it if it doesn't exist."""
    return data.setdefault("backlog", [])

# ===== Display/Formatting helpers =====

def format_backlog_timestamp(ts):
    """Format timestamp for display in backlog listings."""
    try:
        dt = datetime.fromisoformat(ts)
        date_str = dt.strftime(Config.DATE_FORMAT)
        time_str = dt.strftime(Config.TIME_FORMAT)
        return f"[{date_str} {time_str}]"
    except (ValueError, KeyError):
        return f"[{ts if ts else 'no timestamp'}]"

def print_backlog_list(backlog, title="Backlog"):
    """Print formatted backlog with consistent styling."""
    safe_print(f"{emoji('backlog_list')} {title}:")
    for i, item in enumerate(backlog, 1):
        timestamp = format_backlog_timestamp(item.get('ts', ''))
        safe_print(f" {i}. {item['task']} {timestamp}")

def complete_current_task(today):
    """Mark the current task as completed."""
    today["done"].append({
        "id": uuid.uuid4().hex[:8],
        "task": today["todo"],
        "ts": datetime.now().isoformat(timespec="seconds")
    })
    safe_print(f"{emoji('complete')} Completed: {repr(today['todo'])}")
    today["todo"] = None

def handle_next_task_selection(data, today):
    """Handle user selection of next task after completing current one."""
    backlog = get_backlog(data)
    
    # Show current backlog
    if backlog:
        safe_print("")  # Empty line - need to provide empty string
        print_backlog_list(backlog)
    else:
        safe_print("\nBacklog is empty.")

    safe_print("\nSelect next task:")
    safe_print(" - Enter a number to pull from backlog")
    safe_print(" - [n] Add a new task")
    safe_print(" - [Enter] to skip")

    choice = safe_input("> ")
    if choice is None:
        return  # User cancelled or error occurred

    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(backlog):
            task = backlog.pop(index)
            today["todo"] = task["task"]
            if save(data):
                safe_print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task['task'])}")
                cmd_status(None)  # Show status after pulling
        else:
            safe_print(f"{emoji('error')} Invalid backlog index.")
    elif choice.lower() == "n":
        new_task = safe_input("Enter new task: ", validate_task_name)
        if new_task:
            today["todo"] = new_task
            if save(data):
                safe_print(f"{emoji('added')} Added: {repr(new_task)}")
                cmd_status(None)  # Show status after adding
    # Empty choice (Enter) - skip, no action needed

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
        choice = safe_input("[p] pull next from backlog, [a] add new, ENTER to skip ▶ ")
        if choice is None:
            return (None, None)
        choice = choice.strip().lower()
    else:
        choice = safe_input("[a] add new, ENTER to skip ▶ ")
        if choice is None:
            return (None, None)
        choice = choice.strip().lower()

    if choice == "p" and has_backlog:
        return ("pull", None)
    if choice == "a":
        new_task = safe_input("Describe the next task ▶ ")
        if new_task and new_task.strip():
            return ("add", new_task.strip())
    return (None, None)


def cmd_add(args):
    """Add a new task or offer to add to backlog if active task exists."""
    # Validate task name
    is_valid, error_msg = validate_task_name(args.task)
    if not is_valid:
        safe_print(f"{emoji('error')} {error_msg}")
        return

    data = load()
    today = ensure_today(data)
    
    # Clean the task name
    clean_task = args.task.strip()
    
    if today["todo"]:
        safe_print(f"{emoji('error')} Active task already exists: {today['todo']}")
        # Use ASCII-safe prompt character
        prompt_char = "+" if USE_PLAIN else "+"  # Always use + for Windows compatibility
        response = safe_input(f"{prompt_char} Would you like to add '{clean_task}' to the backlog instead? [y/N]: ")
        if response and response.lower() == 'y':
            ts = datetime.now().isoformat(timespec='seconds')
            get_backlog(data).append({"task": clean_task, "ts": ts})
            if save(data):
                safe_print(f"{emoji('backlog_add')} Added to backlog: {repr(clean_task)}")
        return

    today["todo"] = clean_task
    if save(data):
        safe_print(f"{emoji('added')} Added: {clean_task}")
        cmd_status(args)

def cmd_done(args):
    """Complete the current active task and prompt for next action."""
    data = load()
    today = ensure_today(data)
    
    if not today["todo"]:
        safe_print(f"{emoji('error')} No active task to complete.")
        return

    # Complete the task
    complete_current_task(today)
    if not save(data):
        return  # Don't proceed if save failed
        
    cmd_status(args)
    
    # Handle next task selection
    handle_next_task_selection(data, today)


def cmd_status(args):
    """Display current status showing completed tasks and active task."""
    data = load()
    today = ensure_today(data)
    today_str = today_key()
    safe_print(f"\n=== TODAY: {today_str} ===")
    for it in today["done"]:
        ts = it['ts'].split('T')[1]
        safe_print(f"{emoji('added')} {style(GREEN)}{it['task']}{style(RESET)} [{ts}]")
    if not today["done"]:
        safe_print("No completed tasks yet.")
    safe_print(f"{style(BOLD+CYAN) if today['todo'] else style(GRAY)}{today['todo'] or 'TBD'}{style(RESET)}")
    safe_print("="*(17+len(today_str)))

def cmd_newday(args):
    """Initialize a new day's data structure."""
    data = load()
    ensure_today(data)
    if save(data):
        safe_print(f"{emoji('newday')} New day initialized -> {today_key()}")

def cmd_backlog(args):
    """Handle backlog subcommands: add, list, pull, remove."""
    data = load()
    today = ensure_today(data)
    backlog = get_backlog(data)
    
    if args.subcmd == "add":
        # Validate task name
        is_valid, error_msg = validate_task_name(args.task)
        if not is_valid:
            safe_print(f"{emoji('error')} {error_msg}")
            return
            
        clean_task = args.task.strip()
        backlog.append({"task": clean_task,
                       "ts": datetime.now().isoformat(timespec='seconds')})
        if save(data):
            safe_print(f"{emoji('backlog_add')} Backlog task added: {clean_task}")
            
    elif args.subcmd == "list":
        print_backlog_list(backlog)
        
    elif args.subcmd == "pull":
        if today["todo"]:
            safe_print(f"{emoji('error')} Active task already exists: {today['todo']}")
            return
        if not backlog:
            safe_print("No backlog items to pull.")
            return
            
        if hasattr(args, "index") and args.index:
            idx = args.index - 1
            if idx < 0 or idx >= len(backlog):
                safe_print(f"{emoji('error')} Invalid index: {args.index}")
                return
        elif not USE_PLAIN:
            print_backlog_list(backlog)
            idx = safe_int_input("Select task to pull [1-n]: ", min_val=1, max_val=len(backlog))
            if idx is None:
                return
            idx -= 1  # Convert to 0-based index
        else:
            idx = 0  # default to top item in plain/CI mode

        task = backlog.pop(idx)
        today["todo"] = task["task"]
        if save(data):
            safe_print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task['task'])}")
            cmd_status(args)
            
    elif args.subcmd == "remove":
        if not backlog:
            safe_print("No backlog items to remove.")
            return
            
        index = args.index - 1
        if 0 <= index < len(backlog):
            removed = backlog.pop(index)
            if save(data):
                safe_print(f"{emoji('error')} Removed from backlog: {repr(removed['task'])}")
        else:
            safe_print(f"{emoji('error')} Invalid backlog index: {args.index} (valid range: 1-{len(backlog)})")

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
    setup_console_encoding()  # Set up Unicode handling
    
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
