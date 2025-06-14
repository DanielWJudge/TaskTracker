# Filtering

Momentum supports filtering tasks and workflows by categories and tags.

## Filter Active Tasks
Show only tasks with a specific category or tag:

```bash
momentum status --filter "@work"
```

```bash
momentum status --filter "#urgent"
```

You can combine filters:

```bash
momentum status --filter "@work,#urgent"
```

## Filter Backlog
List backlog items with a filter:

```bash
momentum backlog list --filter "@home,#feature"
```

**Tip:** Always quote filters containing `#` to avoid shell issues.

Filtering helps you focus on what matters most!
