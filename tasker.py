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
import re
from datetime import datetime
from typing import Tuple, List
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
    """Print formatted backlog with consistent styling and tag highlighting."""
    safe_print(f"{emoji('backlog_list')} {title}:")
    for i, item in enumerate(backlog, 1):
        timestamp = format_backlog_timestamp(item.get('ts', ''))
        
        # Handle both old and new format backlog items
        if isinstance(item, dict) and "task" in item:
            if isinstance(item["task"], dict):
                # New format with structure
                task_text = item["task"]["task"]
                categories = item["task"].get("categories", [])
                tags = item["task"].get("tags", [])
            else:
                # Old format - parse tags
                task_text = item["task"]
                _, categories, tags = parse_tags(task_text)
        else:
            # Very old format
            task_text = str(item)
            _, categories, tags = parse_tags(task_text)
        
        # Format with tag highlighting
        formatted_task = format_task_with_tags(task_text, categories, tags, USE_PLAIN)
        safe_print(f" {i}. {formatted_task} {timestamp}")


def complete_current_task(today):
    """Mark the current task as completed."""
    # Handle both old format (string) and new format (dict)
    if isinstance(today["todo"], dict):
        task_data = today["todo"]
        task_text = task_data["task"]
    else:
        # Legacy format - convert string to dict
        task_text = today["todo"]
        task_data = create_task_data(task_text)
    
    # Store complete task data in done list
    done_item = {
        "id": uuid.uuid4().hex[:8],
        "task": task_data,  # Store full task data structure
        "ts": datetime.now().isoformat(timespec="seconds")
    }
    
    today["done"].append(done_item)
    safe_print(f"{emoji('complete')} Completed: {repr(task_text)}")
    today["todo"] = None

def handle_next_task_selection(data, today):
    """Handle user selection of next task after completing current one."""
    backlog = get_backlog(data)
    
    # Show current backlog
    if backlog:
        safe_print("")  # Empty line
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
            task_item = backlog.pop(index)
            
            # Handle both old and new format backlog items
            if isinstance(task_item, dict) and "task" in task_item:
                if isinstance(task_item["task"], dict):
                    # New format - already has structure
                    today["todo"] = task_item["task"]
                    task_text = task_item["task"]["task"]
                else:
                    # Old format - convert to new format
                    task_text = task_item["task"]
                    today["todo"] = create_task_data(task_text)
            else:
                # Very old format - just a string
                task_text = str(task_item)
                today["todo"] = create_task_data(task_text)
            
            if save(data):
                safe_print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task_text)}")
                cmd_status(None)  # Show status after pulling
        else:
            safe_print(f"{emoji('error')} Invalid backlog index.")
    elif choice.lower() == "n":
        new_task = safe_input("Enter new task: ", validate_task_name)
        if new_task:
            today["todo"] = create_task_data(new_task)  # Use structured data
            if save(data):
                safe_print(f"{emoji('added')} Added: {repr(new_task)}")
                cmd_status(None)  # Show status after adding
    # Empty choice (Enter) - skip, no action needed

# ===== Tag Parsing Functions =====

def parse_tags(task_text: str) -> Tuple[str, List[str], List[str]]:
    """
    Parse @categories and #tags from task text.
    
    Args:
        task_text: The task description potentially containing tags
        
    Returns:
        tuple: (original_text, categories_list, tags_list)
        
    Examples:
        >>> parse_tags("Fix bug @work #urgent")
        ("Fix bug @work #urgent", ["work"], ["urgent"])
        
        >>> parse_tags("Simple task")
        ("Simple task", [], [])
    """
    if not task_text:
        return task_text, [], []
    
    # Regular expressions for matching tags
    category_pattern = r'@([a-zA-Z0-9_-]+)'
    tag_pattern = r'#([a-zA-Z0-9_-]+)'
    
    # Find all categories and tags
    categories = re.findall(category_pattern, task_text)
    tags = re.findall(tag_pattern, task_text)
    
    # Normalize to lowercase and remove duplicates while preserving order
    categories = list(dict.fromkeys(cat.lower() for cat in categories))
    tags = list(dict.fromkeys(tag.lower() for tag in tags))
    
    return task_text, categories, tags


def validate_tag_format(tag: str) -> bool:
    """
    Validate if a tag follows the correct format.
    
    Args:
        tag: The tag to validate (without @ or # prefix)
        
    Returns:
        bool: True if valid, False otherwise
        
    Valid format:
        - Only letters, numbers, underscores, hyphens
        - 1-50 characters long
        - No spaces or special characters
    """
    if not tag:
        return False
    
    if len(tag) > 50:  # reasonable limit
        return False
    
    # Only allow alphanumeric, underscore, and hyphen
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, tag))


def format_task_with_tags(task_text: str, categories: List[str], tags: List[str], plain_mode: bool = False) -> str:
    """
    Format task text with highlighted categories and tags.
    
    Args:
        task_text: The original task text
        categories: List of categories found in the task
        tags: List of tags found in the task  
        plain_mode: If True, don't add color codes
        
    Returns:
        str: Formatted task text with highlighted tags
    """
    if plain_mode or USE_PLAIN:
        # In plain mode, just return the original text
        return task_text
    
    # Color codes for highlighting
    CATEGORY_COLOR = "\033[94m"  # Blue
    TAG_COLOR = "\033[93m"       # Yellow
    RESET_COLOR = "\033[0m"
    
    formatted_text = task_text
    
    # Highlight categories (@category)
    for category in categories:
        pattern = f"@{category}"
        replacement = f"{CATEGORY_COLOR}@{category}{RESET_COLOR}"
        # Use word boundaries to avoid partial matches
        formatted_text = re.sub(f"@{re.escape(category)}\\b", replacement, formatted_text, flags=re.IGNORECASE)
    
    # Highlight tags (#tag)
    for tag in tags:
        pattern = f"#{tag}"
        replacement = f"{TAG_COLOR}#{tag}{RESET_COLOR}"
        formatted_text = re.sub(f"#{re.escape(tag)}\\b", replacement, formatted_text, flags=re.IGNORECASE)
    
    return formatted_text


def create_task_data(task_text: str) -> dict:
    """
    Create a task data structure with parsed tags.
    
    Args:
        task_text: The task description
        
    Returns:
        dict: Task data with text, categories, tags, and timestamp
    """
    text, categories, tags = parse_tags(task_text)
    
    return {
        "task": text,
        "categories": categories,
        "tags": tags,
        "ts": datetime.now().isoformat(timespec="seconds")
    }


# ===== Update existing validation function =====

def validate_task_name_with_tags(task: str) -> Tuple[bool, str]:
    """
    Enhanced task validation that includes tag format validation.
    
    Args:
        task: The task name to validate (may include tags)
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    # First run the basic validation
    is_valid, error_msg = validate_task_name(task)
    if not is_valid:
        return is_valid, error_msg
    
    # Parse and validate tags
    text, categories, tags = parse_tags(task)
    
    # Validate each category format
    for category in categories:
        if not validate_tag_format(category):
            return False, f"Invalid category format: @{category}. Use only letters, numbers, underscores, and hyphens."
    
    # Validate each tag format  
    for tag in tags:
        if not validate_tag_format(tag):
            return False, f"Invalid tag format: #{tag}. Use only letters, numbers, underscores, and hyphens."
    
    return True, ""


# ===== Helper functions for filtering (we'll implement these next) =====

def extract_categories_from_tasks(tasks: List[dict]) -> List[str]:
    """Extract all unique categories from a list of tasks."""
    categories = set()
    for task in tasks:
        if isinstance(task, dict) and "categories" in task:
            categories.update(task["categories"])
        elif isinstance(task, dict) and "task" in task:
            # Handle legacy tasks without category field
            _, cats, _ = parse_tags(task["task"])
            categories.update(cats)
    return sorted(list(categories))


def extract_tags_from_tasks(tasks: List[dict]) -> List[str]:
    """Extract all unique tags from a list of tasks."""
    tags = set()
    for task in tasks:
        if isinstance(task, dict) and "tags" in task:
            tags.update(task["tags"])
        elif isinstance(task, dict) and "task" in task:
            # Handle legacy tasks without tags field
            _, _, task_tags = parse_tags(task["task"])
            tags.update(task_tags)
    return sorted(list(tags))


def filter_tasks_by_tags(tasks: List[dict], filter_categories: List[str] = None, filter_tags: List[str] = None) -> List[dict]:
    """
    Filter tasks by categories and/or tags.
    
    Args:
        tasks: List of task dictionaries
        filter_categories: Categories to filter by (e.g., ["work", "personal"])
        filter_tags: Tags to filter by (e.g., ["urgent", "low"])
        
    Returns:
        List of tasks matching the filters
    """
    if not filter_categories and not filter_tags:
        return tasks
    
    filtered_tasks = []
    
    for task in tasks:
        # Handle both new format (with categories/tags fields) and legacy format
        if isinstance(task, dict):
            if "categories" in task and "tags" in task:
                task_categories = task["categories"]
                task_tags = task["tags"] 
            else:
                # Legacy format - parse from task text
                _, task_categories, task_tags = parse_tags(task.get("task", ""))
            
            # Check if task matches category filter
            category_match = not filter_categories or any(cat in task_categories for cat in filter_categories)
            
            # Check if task matches tag filter
            tag_match = not filter_tags or any(tag in task_tags for tag in filter_tags)
            
            # Task must match both filters (if specified)
            if category_match and tag_match:
                filtered_tasks.append(task)
    
    return filtered_tasks

def parse_filter_categories(filter_str: str) -> Tuple[bool, List[str], str]:
    """
    Parse filter string into list of categories.
    
    Args:
        filter_str: Comma-separated category string like "@work,@personal"
        
    Returns:
        tuple: (is_valid: bool, categories: List[str], error_message: str)
        
    Examples:
        >>> parse_filter_categories("@work,@personal")
        (True, ["work", "personal"], "")
        
        >>> parse_filter_categories("@work, @personal")  # spaces ok
        (True, ["work", "personal"], "")
        
        >>> parse_filter_categories("work,personal")  # missing @
        (False, [], "Categories must start with @. Use: @work,@personal")
    """
    if not filter_str:
        return True, [], ""
    
    # Split by comma and strip whitespace
    raw_categories = [cat.strip() for cat in filter_str.split(",")]
    
    # Remove empty strings
    raw_categories = [cat for cat in raw_categories if cat]
    
    if not raw_categories:
        return True, [], ""
    
    categories = []
    for cat in raw_categories:
        # Check if category starts with @
        if not cat.startswith("@"):
            return False, [], f"Categories must start with @. Invalid: '{cat}'"
        
        # Extract category name (remove @)
        cat_name = cat[1:]
        
        # Validate category format
        if not validate_tag_format(cat_name):
            return False, [], f"Invalid category format: '{cat}'. Use letters, numbers, underscores, and hyphens only."
        
        # Normalize to lowercase and add to list
        categories.append(cat_name.lower())
    
    # Remove duplicates while preserving order
    categories = list(dict.fromkeys(categories))
    
    return True, categories, ""


def filter_tasks_by_categories(tasks: List[dict], filter_categories: List[str]) -> List[dict]:
    """
    Filter tasks by categories.
    
    Args:
        tasks: List of task dictionaries
        filter_categories: List of category names to filter by (without @)
        
    Returns:
        List of tasks that match any of the filter categories
    """
    if not filter_categories:
        return tasks  # No filter means show all
    
    filtered_tasks = []
    
    for task in tasks:
        # Handle both new format (with categories field) and legacy format
        if isinstance(task, dict):
            if "categories" in task:
                # New structured format - use existing categories
                task_categories = task["categories"]
            elif "task" in task:
                # Handle nested task structure (like in done items)
                if isinstance(task["task"], dict):
                    # Nested structured format
                    if "categories" in task["task"]:
                        task_categories = task["task"]["categories"]
                    else:
                        # Parse from nested task text
                        _, task_categories, _ = parse_tags(task["task"]["task"])
                else:
                    # Legacy format - parse categories from task text
                    _, task_categories, _ = parse_tags(task["task"])
            else:
                # Very old format - parse from task string
                _, task_categories, _ = parse_tags(str(task))
        else:
            # Old string format
            _, task_categories, _ = parse_tags(str(task))
        
        # Check if any task category matches any filter category
        if any(cat in task_categories for cat in filter_categories):
            filtered_tasks.append(task)
    
    return filtered_tasks

def filter_single_task_by_categories(task, filter_categories: List[str]) -> bool:
    """
    Check if a single task matches the category filter.
    
    Args:
        task: Task object (dict or string)
        filter_categories: List of category names to filter by
        
    Returns:
        bool: True if task matches any filter category, False otherwise
    """
    if not filter_categories:
        return True  # No filter means include all
    
    # Handle both new format and legacy format
    if isinstance(task, dict):
        if "categories" in task:
            # New structured format
            task_categories = task["categories"]
        elif "task" in task:
            # Handle nested task structure
            if isinstance(task["task"], dict):
                # Nested structured format
                if "categories" in task["task"]:
                    task_categories = task["task"]["categories"]
                else:
                    # Parse from nested task text
                    _, task_categories, _ = parse_tags(task["task"]["task"])
            else:
                # Legacy format - parse from task text
                _, task_categories, _ = parse_tags(task["task"])
        else:
            # Very old format
            _, task_categories, _ = parse_tags(str(task))
    else:
        # Old string format
        _, task_categories, _ = parse_tags(str(task))
    
    # Check if any task category matches any filter category
    return any(cat in task_categories for cat in filter_categories)

# ===== Data migration helper =====

def migrate_task_to_tagged_format(task_data: dict) -> dict:
    """
    Migrate a legacy task to include categories and tags fields.
    
    Args:
        task_data: Legacy task dictionary
        
    Returns:
        Updated task dictionary with categories and tags
    """
    if "categories" in task_data and "tags" in task_data:
        # Already migrated
        return task_data
    
    # Parse tags from task text
    task_text = task_data.get("task", "")
    text, categories, tags = parse_tags(task_text)
    
    # Update task data
    updated_task = task_data.copy()
    updated_task["categories"] = categories
    updated_task["tags"] = tags
    
    return updated_task

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

    # Parse tags from the task
    task_data = create_task_data(clean_task)
    
    if today["todo"]:
         # Extract task name for display - handle both old and new formats
        if isinstance(today["todo"], dict):
            existing_task_name = today["todo"]["task"]
        else:
            existing_task_name = today["todo"]
            
        safe_print(f"{emoji('error')} Active task already exists: {existing_task_name}")
        # Use ASCII-safe prompt character
        prompt_char = "+" if USE_PLAIN else "+"  # Always use + for Windows compatibility
        response = safe_input(f"{prompt_char} Would you like to add '{clean_task}' to the backlog instead? [y/N]: ")
        if response and response.lower() == 'y':
            get_backlog(data).append(task_data)  # Use task_data instead of separate dict
            if save(data):
                safe_print(f"{emoji('backlog_add')} Added to backlog: {repr(clean_task)}")
        return

    # Store the full task data structure instead of just text
    today["todo"] = task_data
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
    
    # Parse filter if provided
    filter_categories = []
    if hasattr(args, 'filter') and args.filter:
        is_valid, filter_categories, error_msg = parse_filter_categories(args.filter)
        if not is_valid:
            safe_print(f"{emoji('error')} {error_msg}")
            return
    
    # Show filter info if filtering
    filter_info = ""
    if filter_categories:
        formatted_cats = ", ".join(f"@{cat}" for cat in filter_categories)
        filter_info = f" (filtered by: {formatted_cats})"
    
    safe_print(f"\n=== TODAY: {today_str}{filter_info} ===")
    
    # Filter and display completed tasks
    completed_tasks = today["done"]
    if filter_categories:
        completed_tasks = filter_tasks_by_categories(completed_tasks, filter_categories)
    
    if completed_tasks:
        for it in completed_tasks:
            ts = it['ts'].split('T')[1]
            
            # Handle both old format (string) and new format (dict)
            if isinstance(it['task'], dict):
                task_text = it['task']['task']
                categories = it['task'].get('categories', [])
                tags = it['task'].get('tags', [])
            else:
                # Legacy format - parse tags from text
                task_text = it['task']
                _, categories, tags = parse_tags(task_text)
            
            # Format the completed task with tag highlighting
            formatted_task = format_task_with_tags(task_text, categories, tags, USE_PLAIN)
            safe_print(f"{emoji('added')} {style(GREEN)}{formatted_task}{style(RESET)} [{ts}]")
    else:
        if filter_categories:
            safe_print("No completed tasks match the filter.")
        else:
            safe_print("No completed tasks yet.")
    
    # Display active task (if it matches filter)
    if today["todo"]:
        # Check if active task matches filter
        if filter_single_task_by_categories(today["todo"], filter_categories):
            # Handle both old format (string) and new format (dict)
            if isinstance(today["todo"], dict):
                task_text = today["todo"]["task"]
                categories = today["todo"].get("categories", [])
                tags = today["todo"].get("tags", [])
            else:
                # Legacy format - parse tags from text
                task_text = today["todo"]
                _, categories, tags = parse_tags(task_text)
            
            # Format the active task with tag highlighting
            formatted_task = format_task_with_tags(task_text, categories, tags, USE_PLAIN)
            safe_print(f"{style(BOLD+CYAN)}{formatted_task}{style(RESET)}")
        else:
            if filter_categories:
                safe_print(f"{style(GRAY)}No active task matches filter{style(RESET)}")
            else:
                safe_print(f"{style(GRAY)}TBD{style(RESET)}")
    else:
        safe_print(f"{style(GRAY)}TBD{style(RESET)}")
    
    safe_print("="*(17+len(today_str)+len(filter_info)))

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
        # Create structured task data for backlog
        task_data = create_task_data(clean_task)
        backlog.append(task_data)
        
        if save(data):
            safe_print(f"{emoji('backlog_add')} Backlog task added: {clean_task}")
            
    elif args.subcmd == "list":
        # Parse filter if provided
        filter_categories = []
        if hasattr(args, 'filter') and args.filter:
            is_valid, filter_categories, error_msg = parse_filter_categories(args.filter)
            if not is_valid:
                safe_print(f"{emoji('error')} {error_msg}")
                return
        
        # Filter backlog if categories provided
        filtered_backlog = backlog
        if filter_categories:
            filtered_backlog = filter_tasks_by_categories(backlog, filter_categories)
        
        # Show filter info if filtering
        title = "Backlog"
        if filter_categories:
            formatted_cats = ", ".join(f"@{cat}" for cat in filter_categories)
            title = f"Backlog (filtered by: {formatted_cats})"
        
        if not filtered_backlog and filter_categories:
            safe_print(f"{emoji('backlog_list')} {title}:")
            safe_print("No backlog items match the filter.")
        else:
            print_backlog_list(filtered_backlog, title=title)
            
    elif args.subcmd == "pull":
        if today["todo"]:
            # Handle display of existing active task
            if isinstance(today["todo"], dict):
                existing_task = today["todo"]["task"]
            else:
                existing_task = today["todo"]
            safe_print(f"{emoji('error')} Active task already exists: {existing_task}")
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

        task_item = backlog.pop(idx)
        
        # Handle different backlog item formats
        if isinstance(task_item, dict) and "task" in task_item:
            if isinstance(task_item["task"], dict):
                # New structured format
                today["todo"] = task_item["task"]
                task_text = task_item["task"]["task"]
            else:
                # Old format
                task_text = task_item["task"]
                today["todo"] = create_task_data(task_text)
        else:
            # Very old format
            task_text = str(task_item)
            today["todo"] = create_task_data(task_text)
        
        if save(data):
            safe_print(f"{emoji('backlog_pull')} Pulled from backlog: {repr(task_text)}")
            cmd_status(args)
            
    elif args.subcmd == "remove":
        if not backlog:
            safe_print("No backlog items to remove.")
            return
            
        index = args.index - 1
        if 0 <= index < len(backlog):
            removed = backlog.pop(index)
            
            # Get task text for display
            if isinstance(removed, dict) and "task" in removed:
                if isinstance(removed["task"], dict):
                    task_text = removed["task"]["task"]
                else:
                    task_text = removed["task"]
            else:
                task_text = str(removed)
            
            if save(data):
                safe_print(f"{emoji('error')} Removed from backlog: {repr(task_text)}")
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
    
    # Add --filter to status command
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--filter", help="Filter by categories (e.g., @work,@personal)")
    status_parser.set_defaults(func=cmd_status)
    
    sub.add_parser("done").set_defaults(func=cmd_done)
    sub.add_parser("newday").set_defaults(func=cmd_newday)
    
    b = sub.add_parser("backlog")
    b_sub = b.add_subparsers(dest="subcmd", required=True)
    
    b_a = b_sub.add_parser("add")
    b_a.add_argument("task", nargs="+")
    b_a.set_defaults(func=cmd_backlog)
    
    # Add --filter to backlog list command
    b_list = b_sub.add_parser("list")
    b_list.add_argument("--filter", help="Filter by categories (e.g., @work,@personal)")
    b_list.set_defaults(func=cmd_backlog)
    
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
