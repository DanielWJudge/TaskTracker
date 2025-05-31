"""Integration tests for end-to-end CLI workflows."""

import pytest
import subprocess
import json
import tempfile
import shutil
from pathlib import Path


class TestCLIIntegration:
    """Test complete CLI workflows using subprocess calls."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary directory with tasker.py for testing."""
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)

        # Copy tasker.py to temp directory
        original_tasker = Path(__file__).parent.parent / "tasker.py"
        temp_tasker = temp_path / "tasker.py"
        shutil.copy2(original_tasker, temp_tasker)

        # Create temp storage file path
        temp_storage = temp_path / "test_storage.json"

        yield temp_path, temp_tasker, temp_storage

        # Cleanup
        shutil.rmtree(temp_dir)

    def run_cli(self, temp_tasker, temp_storage, command, stdin_input=None):
        """Helper to run CLI commands and return result."""
        # Handle quoted arguments properly for Windows
        if "add '" in command or "backlog add '" in command:
            # Split manually to preserve quoted strings
            parts = [
                "python",
                str(temp_tasker),
                "--plain",
                "--store",
                str(temp_storage),
            ]

            # Parse the command part
            cmd_parts = command.split("'")
            if len(cmd_parts) >= 3:  # Has quoted content
                # e.g., "add 'Write integration tests'" becomes ["add", "Write integration tests"]
                base_cmd = cmd_parts[0].strip().split()
                quoted_content = cmd_parts[1]
                parts.extend(base_cmd)
                parts.append(quoted_content)
            else:
                parts.extend(command.split())
        else:
            parts = [
                "python",
                str(temp_tasker),
                "--plain",
                "--store",
                str(temp_storage),
            ] + command.split()

        # Set environment to handle Unicode properly
        env = {
            **subprocess.os.environ,
            "PYTHONIOENCODING": "utf-8",
            "PYTHONLEGACYWINDOWSSTDIO": "1",
        }

        result = subprocess.run(
            parts,
            capture_output=True,
            text=True,
            input=stdin_input,
            timeout=10,
            env=env,
        )
        return result

    def load_storage(self, temp_storage):
        """Helper to load and return storage data."""
        if temp_storage.exists():
            return json.loads(temp_storage.read_text(encoding="utf-8"))
        return {}


class TestBasicWorkflows(TestCLIIntegration):
    """Test basic daily workflows."""

    def test_new_day_workflow(self, temp_project_dir):
        """Test initializing a new day."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Initialize new day
        result = self.run_cli(temp_tasker, temp_storage, "newday")
        assert result.returncode == 0
        assert "New day initialized" in result.stdout

        # Verify storage was created
        data = self.load_storage(temp_storage)
        assert "backlog" in data
        # Should have today's date key
        assert len([k for k in data.keys() if k.startswith("2025-")]) >= 1

    def test_add_task_workflow(self, temp_project_dir):
        """Test adding a task."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add a task
        result = self.run_cli(
            temp_tasker, temp_storage, "add 'Write integration tests'"
        )
        assert result.returncode == 0
        assert "Added:" in result.stdout
        assert "Write integration tests" in result.stdout
        assert "=== TODAY:" in result.stdout  # status should be shown

        # Verify task was stored
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        todo_task = data[today_key]["todo"]
        if isinstance(todo_task, dict):
            assert todo_task["task"] == "Write integration tests"
        else:
            assert "Write integration tests" in todo_task

    def test_status_workflow(self, temp_project_dir):
        """Test status display."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Start with empty status
        result = self.run_cli(temp_tasker, temp_storage, "status")
        assert result.returncode == 0
        assert "=== TODAY:" in result.stdout
        assert "No completed tasks yet." in result.stdout
        assert "TBD" in result.stdout

        # Add a task and check status
        self.run_cli(temp_tasker, temp_storage, "add 'Test task'")
        result = self.run_cli(temp_tasker, temp_storage, "status")
        assert result.returncode == 0
        assert "Test task" in result.stdout
        assert "TBD" not in result.stdout  # should show actual task

    def test_complete_task_workflow(self, temp_project_dir):
        """Test completing a task with no next action."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add and complete a task
        self.run_cli(temp_tasker, temp_storage, "add 'Complete this task'")
        result = self.run_cli(
            temp_tasker, temp_storage, "done", stdin_input="\n"
        )  # Skip next action

        assert result.returncode == 0
        assert "Completed:" in result.stdout
        assert "Complete this task" in result.stdout
        assert "Select next task:" in result.stdout

        # Verify task was moved to done
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        assert data[today_key]["todo"] is None
        assert len(data[today_key]["done"]) == 1
        done_task = data[today_key]["done"][0]["task"]
        if isinstance(done_task, dict):
            assert done_task["task"] == "Complete this task"
        else:
            assert "Complete this task" in done_task


class TestBacklogWorkflows(TestCLIIntegration):
    """Test backlog-related workflows."""

    def test_backlog_add_list_workflow(self, temp_project_dir):
        """Test adding to and listing backlog."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add items to backlog
        result = self.run_cli(temp_tasker, temp_storage, "backlog add 'Future task 1'")
        assert result.returncode == 0
        assert "Backlog task added:" in result.stdout
        assert "Future task 1" in result.stdout

        result = self.run_cli(temp_tasker, temp_storage, "backlog add 'Future task 2'")
        assert result.returncode == 0

        # List backlog
        result = self.run_cli(temp_tasker, temp_storage, "backlog list")
        assert result.returncode == 0
        assert "Backlog:" in result.stdout
        assert "1. Future task 1" in result.stdout
        assert "2. Future task 2" in result.stdout

        # Verify storage
        data = self.load_storage(temp_storage)
        assert len(data["backlog"]) == 2
        assert "Future task 1" in data["backlog"][0]["task"]
        assert "Future task 2" in data["backlog"][1]["task"]

    def test_backlog_pull_workflow(self, temp_project_dir):
        """Test pulling from backlog."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add backlog items
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Backlog task 1'")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Backlog task 2'")

        # Pull first item
        result = self.run_cli(temp_tasker, temp_storage, "backlog pull")
        assert result.returncode == 0
        assert "Pulled from backlog:" in result.stdout
        assert "Backlog task 1" in result.stdout

        # Verify task is now active and backlog reduced
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        todo_task = data[today_key]["todo"]
        if isinstance(todo_task, dict):
            assert todo_task["task"] == "Backlog task 1"
        else:
            assert "Backlog task 1" in todo_task
        assert len(data["backlog"]) == 1
        assert "Backlog task 2" in data["backlog"][0]["task"]

    def test_backlog_remove_workflow(self, temp_project_dir):
        """Test removing from backlog."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add backlog items
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Keep this'")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Remove this'")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Keep this too'")

        # Remove middle item
        result = self.run_cli(temp_tasker, temp_storage, "backlog remove 2")
        assert result.returncode == 0
        assert "Removed from backlog:" in result.stdout
        assert "Remove this" in result.stdout

        # Verify correct item was removed
        data = self.load_storage(temp_storage)
        assert len(data["backlog"]) == 2
        assert "Keep this" in data["backlog"][0]["task"]
        assert "Keep this too" in data["backlog"][1]["task"]


class TestComplexWorkflows(TestCLIIntegration):
    """Test complex multi-step workflows."""

    def test_full_task_lifecycle(self, temp_project_dir):
        """Test complete task lifecycle with backlog interaction."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # 1. Initialize day
        result = self.run_cli(temp_tasker, temp_storage, "newday")
        assert result.returncode == 0

        # 2. Add backlog items for later
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Future task A'")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Future task B'")

        # 3. Add active task
        result = self.run_cli(temp_tasker, temp_storage, "add 'Current task'")
        assert result.returncode == 0

        # 4. Try to add another task (should offer backlog)
        result = self.run_cli(
            temp_tasker, temp_storage, "add 'Another task'", stdin_input="y\n"
        )
        assert result.returncode == 0
        assert "Active task already exists" in result.stdout
        assert "Added to backlog:" in result.stdout

        # 5. Complete current task and pull from backlog
        result = self.run_cli(temp_tasker, temp_storage, "done", stdin_input="1\n")
        assert result.returncode == 0
        assert "Completed:" in result.stdout
        assert "Current task" in result.stdout
        assert "Pulled from backlog:" in result.stdout
        assert "Future task A" in result.stdout

        # 6. Check final state
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]

        # Should have completed task
        assert len(data[today_key]["done"]) == 1
        done_task = data[today_key]["done"][0]["task"]
        if isinstance(done_task, dict):
            assert done_task["task"] == "Current task"
        else:
            assert "Current task" in done_task

        # Should have pulled task as active
        todo_task = data[today_key]["todo"]
        if isinstance(todo_task, dict):
            assert todo_task["task"] == "Future task A"
        else:
            assert "Future task A" in todo_task

        # Should have remaining backlog items
        assert len(data["backlog"]) == 2  # Future task B + Another task
        backlog_tasks = [item["task"] for item in data["backlog"]]
        assert any("Future task B" in task for task in backlog_tasks)
        assert any("Another task" in task for task in backlog_tasks)

    def test_interactive_done_workflow_new_task(self, temp_project_dir):
        """Test completing task and adding new task interactively."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add and complete task, then add new one
        self.run_cli(temp_tasker, temp_storage, "add 'First task'")
        result = self.run_cli(
            temp_tasker, temp_storage, "done", stdin_input="n\nSecond task\n"
        )

        assert result.returncode == 0
        assert "Completed:" in result.stdout
        assert "First task" in result.stdout
        assert "Added:" in result.stdout
        assert "Second task" in result.stdout

        # Verify state
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        todo_task = data[today_key]["todo"]
        if isinstance(todo_task, dict):
            assert todo_task["task"] == "Second task"
        else:
            assert todo_task == "Second task"
        assert len(data[today_key]["done"]) == 1

    def test_multiple_day_persistence(self, temp_project_dir):
        """Test that backlog persists across days."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Day 1: Add backlog items
        self.run_cli(temp_tasker, temp_storage, "newday")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Persistent task 1'")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Persistent task 2'")

        # Simulate new day by directly modifying storage to have different date
        data = self.load_storage(temp_storage)
        # Add a "new day" entry
        data["2025-05-31"] = {"todo": None, "done": []}
        temp_storage.write_text(json.dumps(data, indent=2), encoding="utf-8")

        # Day 2: Check backlog still exists
        result = self.run_cli(temp_tasker, temp_storage, "backlog list")
        assert result.returncode == 0
        assert "Persistent task 1" in result.stdout
        assert "Persistent task 2" in result.stdout

        # Should be able to pull from previous day's backlog
        result = self.run_cli(temp_tasker, temp_storage, "backlog pull")
        assert result.returncode == 0
        assert "Pulled from backlog:" in result.stdout


class TestErrorHandling(TestCLIIntegration):
    """Test error conditions and edge cases."""

    def test_invalid_commands(self, temp_project_dir):
        """Test handling of invalid CLI commands."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Invalid main command
        result = self.run_cli(temp_tasker, temp_storage, "invalid_command")
        assert result.returncode != 0

        # Invalid backlog subcommand
        result = self.run_cli(temp_tasker, temp_storage, "backlog invalid_sub")
        assert result.returncode != 0

    def test_empty_operations(self, temp_project_dir):
        """Test operations on empty state."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Try to complete when no active task
        result = self.run_cli(temp_tasker, temp_storage, "done")
        assert result.returncode == 0
        assert "No active task to complete" in result.stdout

        # Try to pull from empty backlog
        result = self.run_cli(temp_tasker, temp_storage, "backlog pull")
        assert result.returncode == 0
        assert "No backlog items to pull" in result.stdout

        # List empty backlog
        result = self.run_cli(temp_tasker, temp_storage, "backlog list")
        assert result.returncode == 0
        assert "Backlog:" in result.stdout

    def test_invalid_indices(self, temp_project_dir):
        """Test handling of invalid backlog indices."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add one item
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Only item'")

        # Try invalid remove index
        result = self.run_cli(temp_tasker, temp_storage, "backlog remove 5")
        assert result.returncode == 0
        assert "Invalid backlog index" in result.stdout

        # Try remove from empty after removing only item
        self.run_cli(temp_tasker, temp_storage, "backlog remove 1")
        result = self.run_cli(temp_tasker, temp_storage, "backlog remove 1")
        assert result.returncode == 0
        # The code now properly shows "No backlog items to remove" for empty backlog
        assert "No backlog items to remove" in result.stdout

    def test_concurrent_active_task_handling(self, temp_project_dir):
        """Test handling when trying to add task while one exists."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Add first task
        self.run_cli(temp_tasker, temp_storage, "add 'First task'")

        # Try to add second task, decline backlog
        result = self.run_cli(
            temp_tasker, temp_storage, "add 'Second task'", stdin_input="n\n"
        )
        assert result.returncode == 0
        assert "Active task already exists" in result.stdout

        # Verify first task is still active
        data = self.load_storage(temp_storage)
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        todo_task = data[today_key]["todo"]
        if isinstance(todo_task, dict):
            assert todo_task["task"] == "First task"
        else:
            assert "First task" in todo_task

        # Try to pull when active task exists
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Backlog item'")
        result = self.run_cli(temp_tasker, temp_storage, "backlog pull")
        assert result.returncode == 0
        assert "Active task already exists" in result.stdout


class TestDataPersistence(TestCLIIntegration):
    """Test data persistence and storage integrity."""

    def test_storage_file_creation(self, temp_project_dir):
        """Test that storage file is created properly."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Initially no storage file
        assert not temp_storage.exists()

        # First command should create it
        result = self.run_cli(temp_tasker, temp_storage, "newday")
        assert result.returncode == 0
        assert temp_storage.exists()

        # Should be valid JSON
        data = self.load_storage(temp_storage)
        assert isinstance(data, dict)
        assert "backlog" in data

    def test_data_structure_integrity(self, temp_project_dir):
        """Test that data structure remains consistent."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Perform various operations
        self.run_cli(temp_tasker, temp_storage, "newday")
        self.run_cli(temp_tasker, temp_storage, "backlog add 'Test task'")
        self.run_cli(temp_tasker, temp_storage, "add 'Active task'")
        self.run_cli(temp_tasker, temp_storage, "done", stdin_input="\n")

        # Verify data structure
        data = self.load_storage(temp_storage)

        # Should have global backlog
        assert "backlog" in data
        assert isinstance(data["backlog"], list)

        # Should have today's data
        today_keys = [k for k in data.keys() if k.startswith("2025-")]
        assert len(today_keys) >= 1

        today_data = data[today_keys[0]]
        assert "todo" in today_data
        assert "done" in today_data
        assert isinstance(today_data["done"], list)

        # Done items should have required fields
        if today_data["done"]:
            done_item = today_data["done"][0]
            assert "id" in done_item
            assert "task" in done_item
            assert "ts" in done_item

    def test_plain_mode_consistency(self, temp_project_dir):
        """Test that plain mode produces consistent output."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Use ASCII-only task names to avoid Unicode issues in Windows CMD
        self.run_cli(temp_tasker, temp_storage, "newday")
        self.run_cli(temp_tasker, temp_storage, "add 'Test with ASCII only'")
        result = self.run_cli(temp_tasker, temp_storage, "status")

        assert result.returncode == 0
        # In plain mode, should not contain emoji characters in output formatting
        output_lines = result.stdout.split("\n")
        formatting_lines = [line for line in output_lines if "ASCII only" not in line]
        for line in formatting_lines:
            # Check that formatting doesn't contain common emoji
            assert "✅" not in line
            assert "🎉" not in line
            assert "📋" not in line


class TestCommandLineArgs(TestCLIIntegration):
    """Test command line argument handling."""

    def test_custom_storage_path(self, temp_project_dir):
        """Test using custom storage file path."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Use different storage file
        custom_storage = temp_path / "custom_storage.json"

        result = subprocess.run(
            [
                "python",
                str(temp_tasker),
                "--plain",
                "--store",
                str(custom_storage),
                "newday",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert custom_storage.exists()
        assert not temp_storage.exists()  # original storage not created

    def test_plain_mode_flag(self, temp_project_dir):
        """Test that --plain flag works."""
        temp_path, temp_tasker, temp_storage = temp_project_dir

        # Without --plain (though our helper always uses it)
        # Test by running without our helper
        result = subprocess.run(
            ["python", str(temp_tasker), "--store", str(temp_storage), "newday"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should work regardless of plain mode
        assert "New day initialized" in result.stdout
