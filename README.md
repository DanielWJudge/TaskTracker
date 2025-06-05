# Momentum

A minimal, one-task-at-a-time CLI tracker with built-in Pomodoro timer.

Momentum is a command-line task management tool that enforces focus by allowing only one active task at a time. Features a persistent backlog, interactive prompts, and clean status displays with optional emoji/color output.

---

## Project Structure

```
Momentum/
├── src/
│   └── momentum/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── display.py
│       └── timer.py
├── tests/
├── pyproject.toml
├── LICENSE
└── README.md
```

---

## Installation

You need Python 3.8 or newer.

### Install from PyPI (Recommended)

```sh
pip install momentum-task
```

### Install from Source

For development or to get the latest changes:

```sh
git clone https://github.com/DanielWJudge/Momentum.git
cd momentum
pip install -e .
```

---

## Usage

### Run as a module (no install required):

```sh
python -m momentum add "Task description"
python -m momentum done
python -m momentum backlog add "Future task"
python -m momentum status
```

### Or use the CLI entry point (after install):

```sh
momentum add "Task description"
momentum done
momentum backlog add "Future task"
momentum status
```

---

## Development & Testing

- All source code is under `src/momentum/` (modern src layout)
- Tests are in the `tests/` directory
- Run tests with:

```sh
pytest
```

- The `pytest.ini` ensures the `src` directory is on the Python path for tests.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🚀 Why Momentum?

**Stop juggling endless task lists. Start shipping.**

Most productivity apps encourage **endless lists** that overwhelm your brain. Momentum enforces **laser focus**:

1. **One active task.** Period.
2. Complete it, mark it **done** ✅
3. Choose what's next from your **backlog** or add something new
4. Repeat. Ship faster.

**Built by developers, for developers.** Ready in < 1 second. Runs everywhere.

---

## ✨ Features That Matter

| Feature | Why It Matters |
|---------|---------------|
| 🎯 **Single Active Task** | Your brain works better with one focus. No context switching. |
| ⏱️ **Pomodoro Timer** | Built-in timer for focused work sessions and breaks. |
| 🔄 **Smart Completion Flow** | When you finish a task, Momentum asks: "What's next?" |
| 📋 **Persistent Backlog** | Future tasks survive across days. Never lose track of what matters. |
| ⚡ **Instant Startup** | No databases, no cloud sync delays. Pure speed. |
| 🌍 **Universal Compatibility** | Windows, macOS, Linux. Command Prompt, PowerShell, Terminal. |
| 🛡️ **Bulletproof** | Comprehensive test coverage. Input validation. Error recovery. |
| 🎨 **Beautiful Output** | Color + emoji when available, clean ASCII when needed. |
| 📦 **Zero Dependencies** | Pure Python. No external libraries. No complexity. |

---

## 🏷️ Task Categories and Tags

You can organize your tasks using categories (prefixed with `@`) and tags (prefixed with `#`):

- **Categories**: Use `@category` to group tasks by context (e.g., `@work`, `@personal`).
- **Tags**: Use `#tag` to mark priority, status, or any other attribute (e.g., `#urgent`, `#low`).

**Examples:**
- `python momentum.py add "Finish report @work #urgent"`
- `python momentum.py backlog add "Buy groceries @personal #low"`

---

## 🔍 Filtering by Category and Tag

You can filter your active tasks and backlog by category and/or tag:

- **By category:**  
  `python momentum.py status --filter @work`
- **By tag:**  
  `python momentum.py backlog list --filter "#urgent"`
- **Multiple filters:**  
  `python momentum.py status --filter "@work,#urgent"`
- **Case-insensitive:**  
  `--filter "@WORK,#URGENT"` works the same as lowercase.

**Note:**
If your filter includes `#`, enclose it in quotes to avoid shell comment parsing.

**Examples:**
```sh
python momentum.py status --filter @work
python momentum.py backlog list --filter "#urgent"
python momentum.py status --filter "@work,@personal"
python momentum.py status
```

| Command Example                                 | Description                        |
|-------------------------------------------------|------------------------------------|
| `add "Task @work #urgent"`                      | Add a work task with urgent tag    |
| `status --filter @work`                         | Show only work tasks               |
| `backlog list --filter "#urgent"`               | Show only urgent backlog items     |
| `status --filter "@work,#urgent"`               | Show work tasks tagged urgent      |
| `backlog list --filter @personal`               | Show personal backlog items        |

---

## 🧪 Integration Test Coverage

This project includes comprehensive integration tests to ensure reliability:

- **Complete workflows:** Add, filter, complete, and pull tasks by category/tag.
- **CLI argument handling:** Tests for quoting, multiple filters, and invalid input.
- **Error scenarios:** Invalid filters, non-existent categories/tags, corrupted data.
- **Performance:** Filtering remains fast even with 1000+ backlog tasks.

Run all tests with:
```sh
pytest
```

---

## ⚡ Quick Start

```bash
# Clone and enter
git clone https://github.com/DanielWJudge/Momentum.git
cd Momentum

# Optional: Virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Start fresh
python momentum.py newday

# Add your most important task
python momentum.py add "Ship the new feature"

# Focus. Work. Complete.
python momentum.py done
# → Momentum asks: What's next?
# → [1] Pull from backlog | [n] New task | [Enter] Take a break

# Build your backlog for tomorrow
python momentum.py backlog add "Refactor authentication"
python momentum.py backlog add "Write deployment docs"
python momentum.py backlog add "Review team PRs"

# See everything at a glance
python momentum.py status
```

### Pro Tips

```bash
# Work offline, sync never
python momentum.py --plain status   # Clean output for scripts/CI

# Custom storage location
python momentum.py --store ~/work/tasks.json add "Client work"

# Pull specific backlog item
python momentum.py backlog pull --index 3

# Remove outdated backlog items
python momentum.py backlog remove 2
```

---

## 🧠 How It Works

**Simple data model. Powerful workflow.**

```json
{
  "backlog": [
    {"task": "Future important work", "ts": "2025-05-30T14:30:00"}
  ],
  "2025-05-30": {
    "todo": "Ship the new feature",
    "done": [
      {"id": "a1b2c3d4", "task": "Fix critical bug", "ts": "2025-05-30T09:15:30"}
    ]
  }
}
```

**The Magic:**
- **Global backlog** persists across days
- **Daily completion tracking** with timestamps
- **Atomic file operations** - never lose data
- **Human-readable JSON** - easy to backup/inspect
- **Intelligent prompting** - always knows what to ask next

---

## 🛡️ Battle-Tested Quality

Momentum isn't just another weekend project. It's **production-ready**:

- ✅ **250 automated tests** covering every feature
- ✅ **Cross-platform compatibility** (Windows/macOS/Linux)
- ✅ **Unicode safety** with graceful ASCII fallbacks
- ✅ **Input validation** prevents crashes and data corruption
- ✅ **Error recovery** with automatic backups
- ✅ **Memory-safe operations** - no data loss scenarios

```bash
# Run the full test suite
python -m pytest
# 250 tests pass in < 10 seconds
```

---

## 🎨 Beautiful, Accessible Output

**Rich when possible. Clean when needed.**

### With Colors & Emoji
```
🌅 New day initialized -> 2025-05-30

=== TODAY: 2025-05-30 ===
✅ Fix critical bug [09:15:30]
✅ Ship new feature [14:22:15]
🔄 Write deployment docs
===========================

📋 Backlog:
 1. Refactor authentication [05/29 16:45]
 2. Review team PRs [05/30 11:20]
```

### Plain Mode (--plain)
```
[NEW] New day initialized -> 2025-05-30

=== TODAY: 2025-05-30 ===
[OK] Fix critical bug [09:15:30]
[OK] Ship new feature [14:22:15]
Write deployment docs
===========================

[-] Backlog:
 1. Refactor authentication [05/29 16:45]
 2. Review team PRs [05/30 11:20]
```

---

## 📚 Complete Command Reference

### Core Workflow
```bash
python momentum.py newday                    # Start fresh day
python momentum.py add "Most important task" # Set your focus
python momentum.py done                      # Complete and choose next
python momentum.py status                    # See everything
```

### Backlog Management
```bash
python momentum.py backlog add "Future task"    # Add to backlog
python momentum.py backlog list                 # View all backlog items
python momentum.py backlog pull                 # Interactive: choose from backlog
python momentum.py backlog pull --index 2       # Pull specific item
python momentum.py backlog remove 3             # Remove by index
```

### Options
```bash
--plain              # Disable colors/emoji (great for scripts)
--store PATH         # Use custom storage file
```

---

## 🔧 Development

Momentum welcomes contributions! The codebase is clean, tested, and documented.

```bash
# Set up development environment
git clone https://github.com/DanielWJudge/Momentum.git
cd Momentum
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest                    # All tests
pytest -v                 # Verbose output
pytest --cov=momentum       # With coverage report

# Code structure
momentum.py              # Main application (550 lines, well-documented)
tests/
├── test_commands.py   # Command function tests (29 tests)
├── test_integration.py # End-to-end workflow tests (19 tests)
├── test_storage.py    # File operations tests (11 tests)
├── test_utils.py      # Display/formatting tests (35 tests)
└── test_validation.py # Input validation tests (13 tests)
```

### Testing Philosophy

- **Unit tests** for individual functions
- **Integration tests** for real CLI workflows  
- **Error condition testing** for robustness
- **Cross-platform validation** for reliability

Every feature is tested. Every edge case is covered.

---

## 🗺️ Roadmap

**Proven foundation. Exciting future.**

### ✅ Completed (v1.0)
- [x] Core task management workflow
- [x] Persistent backlog across days
- [x] Interactive completion prompts
- [x] Cross-platform compatibility
- [x] Comprehensive test suite
- [x] Input validation & error handling
- [x] Unicode/Windows support
- [x] **Task categories and tags** (`@work`, `@personal`, `#urgent`)

### 🎯 Next Up (v2.0)
- [ ] **Due dates for backlog items** with smart sorting
- [ ] **Built-in Pomodoro timer** with progress tracking
- [ ] **Time estimation vs actual** reporting
- [ ] **Weekly/monthly completion analytics**
- [ ] **Task templates** for recurring workflows

### 🔮 Future Ideas
- [ ] **Team collaboration features** (shared backlogs)
- [ ] **AI-powered task prioritization** 
- [ ] **Integration with GitHub issues**
- [ ] **Slack/Discord notifications**

---

## 💬 Philosophy

> "The secret to getting ahead is getting started. The secret to getting started is breaking your complex overwhelming tasks into small manageable tasks, and then starting on the first one." - Mark Twain

Momentum embodies this philosophy in code:

- **Simplicity over complexity** - One task, one focus
- **Shipping over planning** - Less organizing, more doing  
- **Progress over perfection** - Done is better than perfect
- **Focus over multitasking** - Depth over breadth

---

## 📄 License

MIT License - Use it, modify it, ship it.

---

## 👤 Author

**Created by Daniel Judge** to fight productivity theater and ship real value.

*"Most task apps make you feel busy. Momentum makes you productive."*

---

## 🙌 Contributing

Found a bug? Have an idea? PRs and issues welcome!

1. **Fork the repo**
2. **Add tests** for your feature
3. **Make sure all 250 tests pass**
4. **Submit a PR** with a clear description

**Questions?** Open an issue. **Want to help?** Check the roadmap above.

---

## ⭐ Star This Repo

If Momentum helps you ship faster, **star this repo** to help others discover it!

**[⭐ Star on GitHub](https://github.com/DanielWJudge/Momentum)**

## ⏱️ Pomodoro Timer

Momentum includes a built-in Pomodoro timer to help you maintain focus and take regular breaks:

```sh
# Start a 25-minute work session with 5-minute break
python -m momentum timer

# Customize work and break durations (in minutes)
python -m momentum timer 45 10

# Use plain mode for simpler output
python -m momentum timer --plain
```

The timer features:
- Visual progress bar showing time remaining
- Clear phase indicators (work/break)
- Optional plain mode for simpler output
- Graceful cancellation with Ctrl+C