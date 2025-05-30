# TODO

A living backlog of ideas, features, and future improvements for the TaskTracker CLI tool.

---

## ✅ Core MVP (Completed)

* [x] Start a new day
* [x] Add one active task
* [x] Mark task as complete
* [x] Show completed tasks with timestamps
* [x] Highlight current task (with color)
* [x] Save to JSON file by date

---

## 🧱 Next-Up Candidates (High Priority)

* [x] Add task backlog support (add/view/pull)
* [x] Prompt user after completing a task: add new or pull from backlog
* [x] Add backlog remove command

---

## 🧠 Future Features (Medium to Low Priority)

* [ ] Task categorization by project/team
* [ ] Assign due dates to backlog tasks
* [ ] Mark task as “no longer needed” (canceled/obsolete)
* [ ] Sort backlog by filters (created date, due date, priority)
* [ ] Pomodoro timer with CLI progress bar + time remaining
* [ ] Capture estimated vs. actual time for tasks
* [ ] View completed tasks by date or range
* [ ] Add start-of-day / end-of-day planning prompts
* [ ] AI-assisted backlog prioritization (stretch goal)

---

## 🔧 Technical Cleanup

* [ ] Refactor repeated print logic into helper functions
* [ ] Add `--help` examples for each CLI command
* [ ] Validate/escape inputs when saving to file
* [ ] Unit tests for core command functions
* [ ] Graceful error handling if JSON is missing/corrupt

---

## 📝 Notes

* Keep CLI interaction minimal—favor speed over features
* No dependencies unless value is extreme (keep it fast and portable)
* All enhancements must preserve the “one active task” philosophy
