# TaskTracker

_A minimal, one‑task‑at‑a‑time CLI tracker with backlog, color/emoji output, and plain‑text mode._

---

## 🚀 Why TaskTracker?

Most task apps encourage **lists**; TaskTracker enforces **focus**:

1. **Add exactly one active task.**
2. Do it, mark it **done** (✅).
3. Choose your next task or pull from a **backlog**.
4. Start every day with a clean slate while yesterday’s wins are saved.

Dog‑fooded daily, designed to live in your terminal, ready in < 1 s.

---

## ✨ Features

| Feature             | Details                                                                 |
|---------------------|-------------------------------------------------------------------------|
| 📝 One active task  | Keeps your brain on one thing.                                           |
| 🔁 Interactive prompts  | After marking a task `done`, choose the next task interactively — select from backlog, type a new one, or skip with `Enter`.                                           |
| 📋 Backlog          | `backlog add`, `backlog list`, `backlog pull` to manage future tasks.   |
| ⏰ Timestamps        | Completion time recorded in ISO format.                                 |
| 🎨 ANSI colors       | Bold cyan for active task, green for completed.                         |
| 🧼 Emoji output      | Motivating icons! Disable with `--plain`.                               |
| 💾 JSON storage      | Human-readable file per day. Easy to back up or inspect.                |
| 🔄 `--store PATH`    | Point to a custom file (useful for tests or multiple contexts).         |
| 🧪 Testable design   | Fully covered with `test_tracker.py` (plain mode auto-applied).         |
| 🧠 Thoughtful UX     | After `done`, it asks what to do next—backlog pull or quit.             |

---

## 🛠️ Installation

```bash
# Clone
git clone git@github.com:<you>/TaskTracker.git && cd TaskTracker

# (Optional) create virtual env
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

# No dependencies required
```

---

## ⚡ Quick Start

```bash
# start fresh day
python tasker.py newday

# add your first task
python tasker.py add "Write killer README"

# finish it
python tasker.py done  # shows status automatically
# you'll now be prompted:
# [b] select from backlog  |  [n] new task  |  [Enter] skip

# add backlog items
python tasker.py backlog add "Refactor parser"
python tasker.py backlog add "Write unit tests"

# list backlog
python tasker.py backlog list

# remove specific backlog item by index
python tasker.py backlog remove 2

# pull next task when ready
python tasker.py backlog pull
```

### Plain‑text / CI mode

```bash
python tasker.py --plain status   # disables color + emoji
```

---

## 🧠 How It Works

* **Data model**
  ```jsonc
  {
    "2025-05-28": {
      "todo": "Write killer README",
      "done": [
        {"id": "a1b2c3d4", "task": "scaffold tests", "ts": "2025-05-28T08:12:45"}
      ],
      "backlog": [
        {"task": "Refactor parser", "ts": "08:30:10"}
      ]
    }
  }
  ```
* Stored in storage.json (or --store yourfile.json)
* Every CLI command loads → mutates → saves atomically
* Text, emoji, and color are all optional
* ISO timestamps are used for consistency and grepability
* After completing a task, the CLI **asks what you'd like to do next**:
  - `[b]` → shows a numbered list of backlog items to pick from
  - `[n]` → lets you enter a new active task directly
  - `[Enter]` → skips adding a new task

---

## 🗺️ Roadmap

* [x] Add backlog remove command
* [ ] Task categories and priority tags
* [ ] Ability to mark tasks as no longer needed
* [ ] Sort backlog by due date, project, or priority
* [ ] Built-in Pomodoro timer with progress bar
* [ ] Track estimated vs. actual time
* [ ] AI-powered backlog prioritization (stretch)

See [`TODO.md`](TODO.md) for development notes.

---

## 🧪 Running Tests

```bash
python test_tasker.py   # uses its own test_storage.json
```
Runs in plain mode with its own test_storage.json. Verifies:
* Adding a task
* Status rendering
* Backlog add/list/pull
* Clean exit and atomic writes

All core flows must print **✅ ALL TESTS PASSED**.

---

## 🙌 Contributing

PRs and issues welcome. Please run tests and add new ones for any feature.

---

## 📝 License

MIT. Use it, tweak it, share it.

---

## 👤 Author

Created by **Daniel Judge** to fight multitasking overload and ship faster.
