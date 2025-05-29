# TaskTracker

*A lightweight, one-task-at-a-time CLI productivity tool for makers, managers, and minimalists.*

## 🚀 What is TaskTracker?

TaskTracker helps you build momentum, focus, and clarity throughout your day.
**Add one simple task. Do it. Mark it done.**
Each completed task is logged for daily reflection.
No clutter, no bloat—just what you need to keep moving forward.

## ✨ Features

* ✅ One active task at a time—encourages focus
* ✅ Simple CLI commands—add, complete, show, start new day
* ✅ Displays completed tasks with ✅ emoji and timestamps
* ✅ Highlights your current task in cyan (if terminal supports it)
* ✅ Starts fresh every day, while preserving prior completions
* ✅ Zero dependencies—runs on any Python 3.7+ environment

## 🛠️ Setup

1. **Clone this repository**

   ```bash
   git clone https://github.com/your-username/TaskTracker.git
   cd TaskTracker
   ```

2. **(Optional) Create a virtual environment**

   ```bash
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```

3. No external dependencies required!

## 🏃 Usage

**Start a new day**

```bash
python tasktracker.py newday
```

**Add a new task**

```bash
python tasktracker.py add "Write documentation for TaskTracker"
```

**Mark the current task as complete**

```bash
python tasktracker.py done
```

**Show your status**

```bash
python tasktracker.py status
```

## 🧮 Example Output

```
=== TODAY: 2025-05-28 ===
✅ Write documentation for TaskTracker [08:32:01]
Design CLI backlog feature
===========================
```

## 🧠 How It Works

* One task at a time: keeps you focused.
* Completed tasks are timestamped and marked with ✅.
* Each new day initializes a clean slate.
* Task history is stored locally in `storage.json`.

## 🗸️ Roadmap

* [ ] Task backlog support (add/view/pull)
* [ ] Task categories and priority tags
* [ ] Ability to mark tasks as no longer needed
* [ ] Sort backlog by due date, project, or priority
* [ ] Built-in Pomodoro timer with progress bar
* [ ] Track estimated vs. actual time
* [ ] AI-powered backlog prioritization (stretch)

See [`TODO.md`](TODO.md) for development notes.

## 🙌 Contributing

Pull requests, feature suggestions, and improvements welcome.
Use this project, improve it, and share back what works for you!

## 📝 License

MIT License — do whatever you want. Attribution appreciated.

## 🡩‍💻 Author

Created by Daniel Judge, a fan of single-tasking and meaningful momentum.
