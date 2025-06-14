# Advanced Features

Momentum offers several advanced features to boost your productivity.

## Backlog Management
Keep track of future tasks:

- Add to backlog:
  ```bash
  momentum backlog add "Plan next release"
  ```
- List backlog:
  ```bash
  momentum backlog list
  ```
- Pull next backlog item as active:
  ```bash
  momentum backlog pull
  ```
- Remove or cancel backlog items by index:
  ```bash
  momentum backlog remove 2
  momentum backlog cancel 3
  ```

## Pomodoro Timer
Use the built-in Pomodoro timer to stay focused:

```bash
momentum timer 25 5
```
This starts a 25-minute work session followed by a 5-minute break.

## History
View your task history:

```bash
momentum history --type all
```

- `--type` can be `cancelled`, `archived`, or `all`.

Explore these features to get the most out of Momentum!
