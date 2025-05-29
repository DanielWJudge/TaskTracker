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

| Feature | Details |
|---------|---------|
| 📝 **One active task** | Keeps your brain on one thing.
| 📋 **Backlog** | `backlog add …`, `backlog list`, `backlog pull`.
| 🕓 **Timestamps** | Done tasks logged with ISO time.
| 🎨 **Color / Emoji** | Motivating output; disable with `--plain`.
| 💾 **Portable JSON store** | Single `storage.json` file per user or per test.
| 🔄 **`--store PATH`** | Point to any file (great for unit tests).
| 🧪 **Test scaffold** | `test_tasker_fixed.py` proves core flows.

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
python tasker_fixed.py newday

# add your first task
python tasker_fixed.py add "Write killer README"

# finish it
ython tasker_fixed.py done  # shows status automatically

# add backlog items
python tasker_fixed.py backlog add "Refactor parser"
python tasker_fixed.py backlog add "Write unit tests"

# list backlog
python tasker_fixed.py backlog list

# pull next task when ready
python tasker_fixed.py backlog pull
```

### Plain‑text / CI mode

```bash
python tasker_fixed.py --plain status   # disables color + emoji
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
* Stored in `storage.json` (or your custom `--store`).
* Each CLI command loads → mutates → saves atomically.
* ANSI colors/emoji are wrapped; stripped when `--plain`.

---

## 🗺️ Roadmap

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
python test_tasker_fixed.py   # uses its own test_storage.json
```
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
