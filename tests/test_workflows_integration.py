import pytest
import subprocess
import json
import tempfile
import shutil
from pathlib import Path
import shlex
import time


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with tasker.py for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    original_tasker = Path(__file__).parent.parent / "tasker.py"
    temp_tasker = temp_path / "tasker.py"
    shutil.copy2(original_tasker, temp_tasker)
    temp_storage = temp_path / "test_storage.json"
    yield temp_path, temp_tasker, temp_storage
    shutil.rmtree(temp_dir)


def run_cli(temp_tasker, temp_storage, command, stdin_input=None):
    parts = [
        "python",
        str(temp_tasker),
        "--plain",
        "--store",
        str(temp_storage),
    ] + shlex.split(command)
    env = {
        **subprocess.os.environ,
        "PYTHONIOENCODING": "utf-8",
        "PYTHONLEGACYWINDOWSSTDIO": "1",
        "TASKER_TODAY_KEY": "2025-05-30",
    }
    result = subprocess.run(
        parts, capture_output=True, text=True, input=stdin_input, timeout=10, env=env
    )
    return result


def test_complete_workflow(temp_project_dir):
    """
    Complete Workflow: Add tagged tasks, filter, complete, pull from backlog, verify separation.
    1. Add several @work and @personal tasks
    2. Filter status by @work
    3. Complete work task
    4. Pull next @work task from backlog
    5. Verify personal tasks aren't affected
    """
    temp_path, temp_tasker, temp_storage = temp_project_dir

    # 1. Add several @work and @personal tasks
    result = run_cli(temp_tasker, temp_storage, 'add "Finish report @work #urgent"')
    assert result.returncode == 0
    result = run_cli(temp_tasker, temp_storage, 'backlog add "Plan meeting @work"')
    assert result.returncode == 0
    result = run_cli(temp_tasker, temp_storage, 'backlog add "Buy groceries @personal"')
    assert result.returncode == 0
    result = run_cli(temp_tasker, temp_storage, 'backlog add "Call mom @personal"')
    assert result.returncode == 0

    # 2. Filter status by @work
    result = run_cli(temp_tasker, temp_storage, "status --filter @work")
    assert result.returncode == 0
    assert "Finish report @work #urgent" in result.stdout
    assert "Plan meeting @work" not in result.stdout  # Not active yet
    assert "Buy groceries @personal" not in result.stdout

    # 3. Complete work task
    result = run_cli(temp_tasker, temp_storage, "done", stdin_input="\n")
    assert result.returncode == 0
    # After completion, no active task, so status should show TBD
    result = run_cli(temp_tasker, temp_storage, "status --filter @work")
    assert result.returncode == 0
    assert "TBD" in result.stdout or "No active task matches filter" in result.stdout

    # 4. Pull next @work task from backlog
    # List backlog filtered by @work to get index
    result = run_cli(temp_tasker, temp_storage, "backlog list --filter @work")
    assert result.returncode == 0
    assert "Plan meeting @work" in result.stdout
    # Pull the first @work task
    result = run_cli(temp_tasker, temp_storage, "backlog pull --index 1")
    assert result.returncode == 0
    assert "Plan meeting @work" in result.stdout
    # Now status should show this as active
    result = run_cli(temp_tasker, temp_storage, "status --filter @work")
    assert result.returncode == 0
    assert "Plan meeting @work" in result.stdout

    # 5. Verify personal tasks aren't affected
    result = run_cli(temp_tasker, temp_storage, "backlog list --filter @personal")
    assert result.returncode == 0
    assert "Buy groceries @personal" in result.stdout
    assert "Call mom @personal" in result.stdout
    # They should not appear in status filtered by @work
    result = run_cli(temp_tasker, temp_storage, "status --filter @personal")
    assert result.returncode == 0
    assert "Plan meeting @work" not in result.stdout
    assert "Buy groceries @personal" not in result.stdout  # Not active
    assert "Call mom @personal" not in result.stdout  # Not active


def test_cli_argument_variants(temp_project_dir):
    """
    CLI Argument Tests: All new command line options work correctly (filter quoting, multiple filters, etc).
    """
    temp_path, temp_tasker, temp_storage = temp_project_dir

    # Add some tasks for filtering
    run_cli(temp_tasker, temp_storage, 'add "Task one @work #urgent"')
    run_cli(temp_tasker, temp_storage, 'backlog add "Task two @personal #low"')
    run_cli(temp_tasker, temp_storage, 'backlog add "Task three @work #low"')
    run_cli(temp_tasker, temp_storage, 'backlog add "Task four @personal #urgent"')

    # 1. --filter with quoted tag
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "#urgent"')
    assert result.returncode == 0
    assert (
        "Task one @work #urgent" in result.stdout
        or "Task four @personal #urgent" in result.stdout
    )

    # 2. --filter with quoted category
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work"')
    assert result.returncode == 0
    assert (
        "Task three @work #low" in result.stdout
        or "Task one @work #urgent" in result.stdout
    )

    # 3. --filter with multiple filters (category and tag)
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work,#low"')
    assert result.returncode == 0
    assert "Task three @work #low" in result.stdout
    assert "Task one @work #urgent" not in result.stdout

    # 4. --filter with whitespace
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work, #low"')
    assert result.returncode == 0
    assert "Task three @work #low" in result.stdout

    # 5. --filter with only tag
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "#low"')
    assert result.returncode == 0
    assert (
        "Task three @work #low" in result.stdout
        or "Task two @personal #low" in result.stdout
    )

    # 6. --filter with only category
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@personal"')
    assert result.returncode == 0
    assert (
        "Task two @personal #low" in result.stdout
        or "Task four @personal #urgent" in result.stdout
    )

    # 7. --filter with invalid format (missing @ or #)
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "work"')
    assert result.returncode == 0
    assert (
        "Invalid filter item: 'work'. Must start with @ (category) or # (tag)."
        in result.stdout
    )

    # 8. --filter with invalid characters
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work!"')
    assert result.returncode == 0
    assert "Invalid category format" in result.stdout

    # 9. --filter with empty string
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter ""')
    assert result.returncode == 0
    assert "Backlog:" in result.stdout  # Should show all

    # 10. --filter with multiple categories
    result = run_cli(
        temp_tasker, temp_storage, 'backlog list --filter "@work,@personal"'
    )
    assert result.returncode == 0
    assert "Task three @work #low" in result.stdout
    assert "Task two @personal #low" in result.stdout
    assert "Task four @personal #urgent" in result.stdout


def test_error_scenarios(temp_project_dir):
    """
    Error Scenario Tests: Invalid filters, non-existent categories, corrupted data, edge cases.
    """
    temp_path, temp_tasker, temp_storage = temp_project_dir

    # Add some tasks for error scenarios
    run_cli(temp_tasker, temp_storage, 'add "Task one @work #urgent"')
    run_cli(temp_tasker, temp_storage, 'backlog add "Task two @personal #low"')

    # 1. Invalid filter format (missing @/#)
    result = run_cli(temp_tasker, temp_storage, "backlog list --filter work")
    assert result.returncode == 0
    assert (
        "Invalid filter item: 'work'. Must start with @ (category) or # (tag)."
        in result.stdout
    )

    # 2. Invalid filter format (invalid characters)
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work!"')
    assert result.returncode == 0
    assert "Invalid category format" in result.stdout

    # 3. Filter by non-existent category
    result = run_cli(temp_tasker, temp_storage, "backlog list --filter @nonexistent")
    assert result.returncode == 0
    assert (
        "No backlog items match the filter." in result.stdout
        or "Backlog (filtered by: @nonexistent):" in result.stdout
    )

    # 4. Filter by non-existent tag
    result = run_cli(temp_tasker, temp_storage, "backlog list --filter #doesnotexist")
    assert result.returncode == 0
    assert (
        "No backlog items match the filter." in result.stdout
        or "Backlog (filtered by: #doesnotexist):" in result.stdout
    )

    # 5. Corrupted data (invalid JSON in storage)
    temp_storage.write_text("not a json", encoding="utf-8")
    result = run_cli(temp_tasker, temp_storage, "status")
    assert result.returncode == 0
    assert (
        "Storage file corrupted" in result.stdout
        or "corrupted" in result.stdout.lower()
    )

    # 6. Edge case: empty filter
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter ""')
    assert result.returncode == 0
    assert "Backlog:" in result.stdout

    # 7. Edge case: filter with only commas
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter ",,,"')
    assert result.returncode == 0
    assert "Backlog:" in result.stdout


def test_performance_large_backlog(temp_project_dir):
    """
    Performance Test: Large backlogs with many tags perform well.
    """
    temp_path, temp_tasker, temp_storage = temp_project_dir

    # Prepare 1000 backlog tasks with various tags/categories
    backlog = []
    for i in range(1000):
        tag = "#urgent" if i % 2 == 0 else "#low"
        cat = "@work" if i % 3 == 0 else "@personal"
        backlog.append(
            {
                "task": f"Task {i} {cat} {tag}",
                "categories": [cat[1:]],
                "tags": [tag[1:]],
                "ts": "2025-05-30T10:00:00",
            }
        )
    data = {"backlog": backlog, "2025-05-30": {"todo": None, "done": []}}
    temp_storage.write_text(json.dumps(data), encoding="utf-8")

    # Time the filter operation
    start = time.time()
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "#urgent"')
    elapsed = time.time() - start
    assert result.returncode == 0
    # Should find about half the tasks
    assert "Task 0 @work #urgent" in result.stdout
    assert "Task 2 @personal #urgent" in result.stdout
    assert elapsed < 1.5, f"Filtering took too long: {elapsed:.2f}s"

    # Time a category filter
    start = time.time()
    result = run_cli(temp_tasker, temp_storage, 'backlog list --filter "@work"')
    elapsed = time.time() - start
    assert result.returncode == 0
    assert "Task 0 @work #urgent" in result.stdout
    assert "Task 3 @work #low" in result.stdout
    assert elapsed < 1.5, f"Category filtering took too long: {elapsed:.2f}s"
