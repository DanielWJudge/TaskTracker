"""Tests for CLI command functions."""

from unittest.mock import patch, MagicMock
import json
import sys
import importlib
from momentum.cli import (
    cmd_add,
    cmd_done,
    cmd_status,
    cmd_newday,
    cmd_backlog,
    complete_current_task,
    handle_next_task_selection,
    load,
    ensure_today,
    get_backlog,
    cmd_cancel,
    cmd_history,
    merge_and_dedup_case_insensitive,
    safe_print,
    safe_int_input,
    migrate_task_data,
    parse_filter_string,
    filter_tasks_by_tags_or_categories,
    filter_single_task_by_tags_or_categories,
    validate_tag_format,
    extract_categories_from_tasks,
    prompt_next_action,
    create_task_data,
)


class TestCmdAdd:
    """Test the cmd_add command function."""

    def test_add_valid_task_to_empty_todo(
        self, temp_storage, plain_mode, mock_datetime, capsys
    ):
        """Test adding a valid task when no active task exists."""
        # Create mock args
        args = MagicMock()
        args.task = "Test task"
        args.store = str(temp_storage)  # Ensure cmd_add uses temp_storage

        with patch("momentum.cli.STORE", temp_storage):  # Patch STORE for load()
            cmd_add(args)

            # Check output
            captured = capsys.readouterr()
            assert "Added: Test task" in captured.out
            assert "=== TODAY:" in captured.out  # status should be shown

            # Check data was saved - now expecting structured format
            data = load()  # Loads from temp_storage due to patch
            today = ensure_today(data)
        assert isinstance(today["todo"], dict)
        assert today["todo"]["task"] == "Test task"
        assert today["todo"]["categories"] == []
        assert today["todo"]["tags"] == []

    def test_add_task_when_active_task_exists_decline(
        self, temp_storage, plain_mode, capsys
    ):
        """Test adding task when active task exists and user declines backlog."""
        # Setup existing active task - use new format
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Existing task",
                    "categories": [],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00",
                },
                "done": [],
            },
            "backlog": [],
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.task = "New task"
        args.store = str(temp_storage)
        with patch("momentum.cli.safe_input", return_value="n"), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            cmd_add(args)

        captured = capsys.readouterr()
        assert "Active task already exists: Existing task" in captured.out

        # Verify task wasn't added to backlog
        updated_data = load()
        assert len(updated_data["backlog"]) == 0

    @patch("momentum.cli.save", return_value=True)
    def test_add_task_when_active_task_exists_accept_backlog(
        self, mock_save, temp_storage, plain_mode, capsys
    ):
        """Test adding task to backlog when active task exists and user accepts."""
        # Setup existing active task - use new format
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Existing task",
                    "categories": [],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00",
                },
                "done": [],
            },
            "backlog": [],
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.task = "New task"
        args.store = str(temp_storage)
        with patch("momentum.cli.safe_input", return_value="y"), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            cmd_add(args)

        captured = capsys.readouterr()
        assert "Added to backlog:" in captured.out
        assert "New task" in captured.out

    def test_add_invalid_task(self, temp_storage, plain_mode, capsys):
        """Test adding an invalid task name."""
        args = MagicMock()
        args.task = ""  # empty task
        args.store = str(temp_storage)
        cmd_add(args)

        captured = capsys.readouterr()
        assert "Task name cannot be empty" in captured.out

        # Verify no data was saved
        data = load()
        today = ensure_today(data)
        assert today["todo"] is None

    def test_add_task_with_whitespace(self, temp_storage, plain_mode, capsys):
        """Test adding task with leading/trailing whitespace."""
        args = MagicMock()
        args.task = "  Test task with spaces  "
        args.store = str(temp_storage)
        cmd_add(args)

        # Check that whitespace was stripped - now expecting structured format
        data = load()
        today = ensure_today(data)
        assert isinstance(today["todo"], dict)
        assert today["todo"]["task"] == "Test task with spaces"


class TestCmdDone:
    """Test the cmd_done command function."""

    def test_done_with_no_active_task(self, temp_storage, plain_mode, capsys):
        """Test completing when no active task exists."""
        args = MagicMock()

        cmd_done(args)

        captured = capsys.readouterr()
        assert "No active task to complete" in captured.out

    @patch("momentum.cli.handle_next_task_selection")
    def test_done_with_active_task(
        self, mock_handle_next, temp_storage, plain_mode, mock_datetime, capsys
    ):
        """Test completing an active task."""
        # Setup active task - use legacy string format to test migration
        data = {"2025-05-30": {"todo": "Test task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_done uses temp_storage

        captured_out = ""
        today_data_after_cmd = None

        with patch("momentum.cli.today_key", return_value="2025-05-30"), patch(
            "momentum.cli.STORE", temp_storage
        ):  # Patch global STORE for the test's load and ensure_today
            cmd_done(args)

            # Capture output from cmd_done itself
            # capsys needs to be read after the command if we want its output
            # but for data checks, load must happen under the same patch.
            captured = capsys.readouterr()  # Capture output of cmd_done
            captured_out = captured.out

            # Check data was updated by loading within the patch context
            updated_data = load()  # Should load from temp_storage due to patch
            today_data_after_cmd = ensure_today(updated_data)

        assert "Completed:" in captured_out
        assert "Test task" in captured_out

        assert today_data_after_cmd["todo"] is None
        assert len(today_data_after_cmd["done"]) == 1
        # Task should now be stored in structured format
        assert isinstance(today_data_after_cmd["done"][0]["task"], dict)
        assert today_data_after_cmd["done"][0]["task"]["task"] == "Test task"

        # Check that next task selection was called
        mock_handle_next.assert_called_once()

    def test_done_save_failure(self, temp_storage, plain_mode, capsys):
        """Test behavior when save fails after completing task."""
        # Setup active task
        data = {"2025-05-30": {"todo": "Test task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_done uses temp_storage

        with patch("momentum.cli.save", return_value=False), patch(
            "momentum.cli.handle_next_task_selection"
        ) as mock_handle_next, patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            cmd_done(args)

            # With the updated code, cmd_done returns early if save fails
            # so handle_next_task_selection should NOT be called
            mock_handle_next.assert_not_called()


class TestCompleteCurrentTask:
    """Test the complete_current_task helper function."""

    def test_complete_current_task(self, mock_datetime, capsys):
        """Test marking current task as complete."""
        today = {"todo": "Test task", "done": []}

        with patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):  # Not strictly necessary here but good for consistency
            complete_current_task(today)

        captured = capsys.readouterr()
        assert "Completed:" in captured.out
        assert "Test task" in captured.out

        # Check task was moved to done
        assert today["todo"] is None
        assert len(today["done"]) == 1
        # Task should be stored in structured format
        assert isinstance(today["done"][0]["task"], dict)
        assert today["done"][0]["task"]["task"] == "Test task"
        assert today["done"][0]["ts"] == "2025-05-30T12:00:00"
        assert "id" in today["done"][0]


class TestHandleNextTaskSelection:
    """Test the handle_next_task_selection function."""

    def test_select_backlog_item_by_number(self, temp_storage, plain_mode, capsys):
        """Test selecting a backlog item by number."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }

        today = data["2025-05-30"]

        with patch("momentum.cli.safe_input", return_value="2"), patch(
            "momentum.cli.save", return_value=True
        ), patch("momentum.cli.cmd_status"), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):

            handle_next_task_selection(data, today)

        captured = capsys.readouterr()
        assert "Pulled from backlog:" in captured.out
        assert "Second task" in captured.out

        # Check data was updated - now expecting structured format
        assert isinstance(today["todo"], dict)
        assert today["todo"]["task"] == "Second task"
        assert len(data["backlog"]) == 1  # one item removed
        assert data["backlog"][0]["task"] == "First task"  # correct item remained

    def test_select_invalid_backlog_number(self, plain_mode, capsys):
        """Test selecting invalid backlog number."""
        data = {
            "backlog": [{"task": "Only task", "ts": "2025-05-30T10:00:00"}],
            "2025-05-30": {"todo": None, "done": []},
        }
        today = data["2025-05-30"]

        with patch("momentum.cli.safe_input", return_value="5"), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):  # invalid index
            handle_next_task_selection(data, today)

        captured = capsys.readouterr()
        assert "Invalid backlog index" in captured.out

        # Check nothing was changed
        assert today["todo"] is None
        assert len(data["backlog"]) == 1

    def test_add_new_task(self, temp_storage, plain_mode, capsys):
        """Test adding a new task interactively."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        today = data["2025-05-30"]

        with patch(
            "momentum.cli.safe_input", side_effect=["n", "New interactive task"]
        ), patch("momentum.cli.save", return_value=True), patch(
            "momentum.cli.cmd_status"
        ), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):

            handle_next_task_selection(data, today)

        captured = capsys.readouterr()
        assert "Added:" in captured.out
        assert "New interactive task" in captured.out

        # Check data was updated - now expecting structured format
        assert isinstance(today["todo"], dict)
        assert today["todo"]["task"] == "New interactive task"

    def test_skip_adding_task(self, plain_mode):
        """Test skipping task addition (empty input)."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        today = data["2025-05-30"]

        with patch("momentum.cli.safe_input", return_value=""), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):  # User presses Enter
            handle_next_task_selection(data, today)

        # Check nothing was changed
        assert today["todo"] is None

    def test_user_cancels_input(self, plain_mode):
        """Test user cancelling input (Ctrl+C)."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        today = data["2025-05-30"]

        with patch("momentum.cli.safe_input", return_value=None), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):  # safe_input returns None on cancel
            handle_next_task_selection(data, today)

        # Check nothing was changed
        assert today["todo"] is None

    def test_select_backlog_item_invalid_format(self, temp_storage, plain_mode, capsys):
        """Test selecting backlog item with invalid format."""
        data = {
            "backlog": [
                {"invalid": "format"},  # Missing task field
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        today = data["2025-05-30"]

        with patch("momentum.cli.safe_input", return_value="1"), patch(
            "momentum.cli.save", return_value=True
        ), patch("momentum.cli.cmd_status"), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            handle_next_task_selection(data, today)

        captured = capsys.readouterr()
        assert "Pulled from backlog:" in captured.out
        assert "{'invalid': 'format'}" in captured.out

        # Check data was updated - now expecting structured format
        assert isinstance(today["todo"], dict)
        assert (
            today["todo"]["task"] == "{'invalid': 'format'}"
        )  # Should be converted to string
        assert len(data["backlog"]) == 1  # one item removed
        assert data["backlog"][0]["task"] == "Second task"  # correct item remained


class TestCmdStatus:
    """Test the cmd_status command function."""

    def test_status_no_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with no tasks."""
        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_status uses temp_storage
        args.filter = None  # Ensure filter is None if not provided

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_status(args)

        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "No completed tasks yet." in captured.out
        assert "TBD" in captured.out

    def test_status_with_active_task(self, temp_storage, plain_mode, capsys):
        """Test status display with active task."""
        # Use legacy string format to test backward compatibility
        data = {"2025-05-30": {"todo": "Current task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_status uses temp_storage
        args.filter = None  # Ensure filter is None if not provided

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_status(args)

        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "Current task" in captured.out

    def test_status_with_completed_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with completed tasks."""
        data = {
            "2025-05-30": {
                "todo": "Active task",  # Use new format for active task
                "done": [
                    # Use new dict format for completed tasks
                    {
                        "id": "abc123",
                        "task": {
                            "task": "Completed task 1",
                            "categories": [],
                            "tags": [],
                        },
                        "ts": "2025-05-30T09:00:00",
                    },
                    {
                        "id": "def456",
                        "task": {
                            "task": "Completed task 2",
                            "categories": [],
                            "tags": [],
                        },
                        "ts": "2025-05-30T10:30:00",
                    },
                ],
            },
            "backlog": [],
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_status uses temp_storage
        args.filter = None  # Ensure filter is None if not provided

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_status(args)

        captured = capsys.readouterr()
        assert "Completed task 1" in captured.out
        assert "Completed task 2" in captured.out
        assert "[09:00:00]" in captured.out
        assert "[10:30:00]" in captured.out


class TestCmdNewday:
    """Test the cmd_newday command function."""

    def test_newday_initialization(self, temp_storage, plain_mode, capsys):
        """Test new day initialization."""
        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_newday uses temp_storage

        today_key_val = "2025-05-30"
        loaded_data_after_cmd = None

        with patch("momentum.cli.today_key", return_value=today_key_val), patch(
            "momentum.cli.STORE", temp_storage
        ):  # Patch STORE for load()
            cmd_newday(args)
            loaded_data_after_cmd = load()  # Load within patch context

        captured = capsys.readouterr()
        assert "New day initialized" in captured.out
        assert today_key_val in captured.out

        # Check data structure was created
        assert today_key_val in loaded_data_after_cmd
        assert "backlog" in loaded_data_after_cmd

    def test_newday_save_failure(self, temp_storage, plain_mode, capsys):
        """Test new day initialization when save fails."""
        args = MagicMock()
        args.store = str(temp_storage)  # Ensure cmd_newday uses temp_storage

        with patch("momentum.cli.save", return_value=False), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            cmd_newday(args)

        captured = capsys.readouterr()
        # With the updated code, cmd_newday only shows success message if save succeeds
        assert "New day initialized" not in captured.out


class TestCmdBacklog:
    """Test the cmd_backlog command function."""

    def test_backlog_add_valid_task(
        self, temp_storage, plain_mode, mock_datetime, capsys
    ):
        """Test adding valid task to backlog."""
        args = MagicMock()
        args.subcmd = "add"
        args.task = "Backlog task"
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        backlog_after_cmd = None
        with patch("momentum.cli.STORE", temp_storage):  # Patch STORE for load()
            cmd_backlog(args)
            # Check data was saved - now expecting structured format
            data = load()  # Loads from temp_storage
            backlog_after_cmd = get_backlog(data)

        captured = capsys.readouterr()
        assert "Backlog task added: Backlog task" in captured.out

        assert len(backlog_after_cmd) == 1
        assert backlog_after_cmd[0]["task"] == "Backlog task"
        assert backlog_after_cmd[0]["categories"] == []
        assert backlog_after_cmd[0]["tags"] == []

    def test_backlog_add_invalid_task(self, temp_storage, plain_mode, capsys):
        """Test adding invalid task to backlog."""
        args = MagicMock()
        args.subcmd = "add"
        args.task = ""  # empty task
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        # The validation now properly works for empty tasks
        assert "Task name cannot be empty" in captured.out

    def test_backlog_list_empty(self, temp_storage, plain_mode, capsys):
        """Test listing empty backlog."""
        args = MagicMock()
        args.subcmd = "list"
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Backlog:" in captured.out

    def test_backlog_list_with_items(self, temp_storage, plain_mode, capsys):
        """Test listing backlog with items."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "list"
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "First task" in captured.out
        assert "Second task" in captured.out
        assert "[05/30 10:00]" in captured.out
        assert "[05/30 11:00]" in captured.out

    def test_backlog_pull_with_active_task(self, temp_storage, plain_mode, capsys):
        """Test pulling from backlog when active task exists."""
        data = {
            "backlog": [{"task": "Backlog task", "ts": "2025-05-30T10:00:00"}],
            "2025-05-30": {
                "todo": {
                    "task": "Active task",
                    "categories": [],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00",
                },
                "done": [],
            },
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "pull"
        args.index = None
        args.filter = None  # Ensure filter is None for status call
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Active task already exists" in captured.out

    def test_backlog_pull_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test pulling from empty backlog."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "pull"
        args.index = None
        args.filter = None
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "No backlog items to pull" in captured.out

    def test_backlog_pull_by_index(self, temp_storage, plain_mode, capsys):
        """Test pulling specific backlog item by index."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "pull"
        args.index = 2  # pull second item
        args.filter = None
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Pulled from backlog:" in captured.out
        assert "Second task" in captured.out

    def test_backlog_remove_valid_index(self, temp_storage, plain_mode, capsys):
        """Test removing backlog item by valid index."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "remove"
        args.index = 1  # remove first item (1-based)
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        with patch("momentum.cli.save", return_value=True):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Removed from backlog:" in captured.out
        assert "First task" in captured.out

    def test_backlog_remove_invalid_index(self, temp_storage, plain_mode, capsys):
        """Test removing backlog item by invalid index."""
        data = {
            "backlog": [{"task": "Only task", "ts": "2025-05-30T10:00:00"}],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "remove"
        args.index = 5  # invalid index
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Invalid backlog index: 5" in captured.out
        # The current code doesn't show valid range, just the basic error message

    def test_backlog_remove_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test removing from empty backlog."""
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 1
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        # The updated code properly shows "No backlog items to remove" for empty backlog
        assert "No backlog items to remove" in captured.out

    def test_backlog_cancel_valid_index(self, temp_storage, plain_mode, capsys):
        """Test cancelling a backlog item by valid index."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "cancel"
        args.index = 2  # cancel second item (1-based)
        args.store = str(temp_storage)  # Ensure cmd_backlog uses temp_storage

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Cancelled from backlog:" in captured.out
        assert "Second task" in captured.out

        # Reload and check that the backlog is updated and history contains the cancelled task
        updated_data = load()
        backlog = updated_data["backlog"]
        history = updated_data.get("history", [])
        assert len(backlog) == 1
        assert backlog[0]["task"] == "First task"
        assert any(
            t.get("task") == "Second task" and t.get("state") == "cancelled"
            for t in history
        )
        cancelled_task = next(t for t in history if t.get("task") == "Second task")
        assert "cancellation_date" in cancelled_task

    def test_backlog_cancel_invalid_index(self, temp_storage, plain_mode, capsys):
        """Test cancelling a backlog item with an invalid index."""
        data = {
            "backlog": [
                {"task": "Only task", "ts": "2025-05-30T10:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "cancel"
        args.index = 5  # invalid index
        args.store = str(temp_storage)

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Invalid backlog index: 5" in captured.out
        # Backlog should remain unchanged
        updated_data = load()
        assert len(updated_data["backlog"]) == 1
        assert updated_data["backlog"][0]["task"] == "Only task"
        assert "history" not in updated_data or not updated_data["history"]

    def test_backlog_cancel_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test cancelling from an empty backlog."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "cancel"
        args.index = 1
        args.store = str(temp_storage)

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "No backlog items to cancel" in captured.out
        # Backlog and history should remain empty
        updated_data = load()
        assert updated_data["backlog"] == []
        assert "history" not in updated_data or not updated_data["history"]

    def test_backlog_cancel_non_dict_item(self, temp_storage, plain_mode, capsys):
        """Test cancelling a backlog item that is not a dict (legacy/invalid data)."""
        data = {
            "backlog": [
                "Legacy string task",
                {"task": "Valid task", "ts": "2025-05-30T10:00:00"},
            ],
            "2025-05-30": {"todo": None, "done": []},
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")

        args = MagicMock()
        args.subcmd = "cancel"
        args.index = 1  # try to cancel the legacy string
        args.store = str(temp_storage)

        cmd_backlog(args)

        captured = capsys.readouterr()
        assert "unexpected format" in captured.out.lower()
        # The legacy string should remain in backlog
        updated_data = load()
        assert updated_data["backlog"][0] == "Legacy string task"
        # The valid task should still be present
        assert updated_data["backlog"][1]["task"] == "Valid task"
        # History should not contain the legacy string
        assert "history" not in updated_data or not any(
            t.get("task") == "Legacy string task" for t in updated_data["history"]
        )


class TestCmdCancel:
    """Test the cmd_cancel command function."""

    def test_cancel_active_task(self, temp_storage, plain_mode, capsys):
        """Test cancelling an active task."""

        if "momentum" in sys.modules:
            importlib.reload(sys.modules["momentum.cli"])

        # Setup active task data
        active_task_details = {
            "task": "Task to cancel",
            "categories": [],
            "tags": [],
            "ts": "2025-05-30T10:00:00",
            "state": "active",
        }
        data_to_write = {
            "2025-05-30": {"todo": active_task_details, "done": []},
            "backlog": [],
        }
        temp_storage.write_text(json.dumps(data_to_write), encoding="utf-8")

        args = MagicMock()
        args.store = str(temp_storage)

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_cancel(args)

        with patch("momentum.cli.STORE", temp_storage), patch(
            "momentum.cli.today_key", return_value="2025-05-30"
        ):
            updated_data = load()
            today = ensure_today(updated_data)

        captured = capsys.readouterr()
        assert "Cancelled:" in captured.out

        assert (
            today["todo"] is None
        ), f"Expected todo to be None, but was {today['todo']}"
        assert (
            len(today["done"]) == 1
        ), f"Expected 1 item in done list, found {len(today['done'])}"

        if len(today["done"]) == 1:
            cancelled_outer_wrapper = today["done"][0]
            assert "task" in cancelled_outer_wrapper, "'task' key missing in done item"
            cancelled_task_data = cancelled_outer_wrapper["task"]
            assert isinstance(
                cancelled_task_data, dict
            ), "Cancelled task data should be a dict"
            assert (
                cancelled_task_data.get("state") == "cancelled"
            ), f"Cancelled task state is not 'cancelled', but {cancelled_task_data.get('state')}"
            assert (
                "cancelled_ts" in cancelled_task_data
            ), "'cancelled_ts' missing in cancelled task"
            assert (
                cancelled_task_data.get("task") == "Task to cancel"
            ), f"Cancelled task text is incorrect: {cancelled_task_data.get('task')}"

    def test_cancel_no_active_task(self, temp_storage, plain_mode, capsys):
        """Test cancelling when there is no active task."""

        data = {"2025-05-30": {"todo": None, "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding="utf-8")
        args = MagicMock()
        args.store = str(temp_storage)

        with patch("momentum.cli.today_key", return_value="2025-05-30"):
            cmd_cancel(args)

        captured = capsys.readouterr()
        assert "No active task to cancel" in captured.out


class TestCmdHistory:
    """Test the cmd_history command function."""

    def test_history_cancelled(self, temp_storage, plain_mode, capsys):
        """Test showing only cancelled tasks in history."""
        data = {
            "history": [
                {
                    "task": "Cancelled 1",
                    "state": "cancelled",
                    "cancellation_date": "2025-05-30T10:00:00",
                },
                {
                    "task": "Archived 1",
                    "state": "archived",
                    "archival_date": "2025-05-30T11:00:00",
                },
            ]
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")
        args = MagicMock()
        args.type = "cancelled"
        args.store = str(temp_storage)
        with patch("momentum.cli.STORE", temp_storage):
            cmd_history(args)
        captured = capsys.readouterr()
        assert "HISTORY: cancelled" in captured.out
        assert "Cancelled 1" in captured.out
        assert "Archived 1" not in captured.out

    def test_history_archived(self, temp_storage, plain_mode, capsys):
        """Test showing only archived tasks in history."""
        data = {
            "history": [
                {
                    "task": "Cancelled 1",
                    "state": "cancelled",
                    "cancellation_date": "2025-05-30T10:00:00",
                },
                {
                    "task": "Archived 1",
                    "state": "archived",
                    "archival_date": "2025-05-30T11:00:00",
                },
            ]
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")
        args = MagicMock()
        args.type = "archived"
        args.store = str(temp_storage)
        with patch("momentum.cli.STORE", temp_storage):
            cmd_history(args)
        captured = capsys.readouterr()
        assert "HISTORY: archived" in captured.out
        assert "Archived 1" in captured.out
        assert "Cancelled 1" not in captured.out

    def test_history_all(self, temp_storage, plain_mode, capsys):
        """Test showing all tasks in history."""
        data = {
            "history": [
                {
                    "task": "Cancelled 1",
                    "state": "cancelled",
                    "cancellation_date": "2025-05-30T10:00:00",
                },
                {
                    "task": "Archived 1",
                    "state": "archived",
                    "archival_date": "2025-05-30T11:00:00",
                },
            ]
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")
        args = MagicMock()
        args.type = "all"
        args.store = str(temp_storage)
        with patch("momentum.cli.STORE", temp_storage):
            cmd_history(args)
        captured = capsys.readouterr()
        assert "HISTORY: all" in captured.out
        assert "Cancelled 1" in captured.out
        assert "Archived 1" in captured.out

    def test_history_no_matches(self, temp_storage, plain_mode, capsys):
        """Test showing history when there are no matching tasks."""
        data = {
            "history": [
                {
                    "task": "Archived 1",
                    "state": "archived",
                    "archival_date": "2025-05-30T11:00:00",
                },
            ]
        }
        temp_storage.write_text(json.dumps(data), encoding="utf-8")
        args = MagicMock()
        args.type = "cancelled"
        args.store = str(temp_storage)
        with patch("momentum.cli.STORE", temp_storage):
            cmd_history(args)
        captured = capsys.readouterr()
        assert "No matching tasks in history." in captured.out


class TestUtilityFunctions:
    """Test utility functions in cli.py."""

    def test_merge_and_dedup_case_insensitive(self):
        """Test case-insensitive deduplication of lists."""
        list1 = ["Work", "work", "Personal"]
        list2 = ["WORK", "personal", "Urgent"]
        result = merge_and_dedup_case_insensitive(list1, list2)
        assert len(result) == 3
        assert "Work" in result  # Preserves first occurrence's case
        assert "Personal" in result
        assert "Urgent" in result

    def test_safe_print_unicode_error(self, capsys):
        """Test safe_print handling of Unicode errors."""
        # Create a string that will cause UnicodeEncodeError
        text = "Hello \u2022 World"  # Bullet point character
        with patch("builtins.print") as mock_print:

            def side_effect(*args, **kwargs):
                if args[0] == text:
                    raise UnicodeEncodeError(
                        "ascii", text, 0, 1, "ordinal not in range(128)"
                    )
                return None

            mock_print.side_effect = side_effect
            safe_print(text)
            # Verify the fallback print was called with ASCII-safe version
            mock_print.assert_any_call("Hello ? World")

    def test_safe_int_input_validation(self, capsys):
        """Test safe_int_input validation."""
        with patch("builtins.input", side_effect=["abc", "0", "15", "10"]):
            # Test invalid input
            result = safe_int_input("Enter number: ", min_val=1, max_val=10)
            assert result is None
            captured = capsys.readouterr()
            assert "Invalid input" in captured.out

            # Test below min
            result = safe_int_input("Enter number: ", min_val=1, max_val=10)
            assert result is None
            captured = capsys.readouterr()
            assert "must be at least" in captured.out

            # Test above max
            result = safe_int_input("Enter number: ", min_val=1, max_val=10)
            assert result is None
            captured = capsys.readouterr()
            assert "must be at most" in captured.out

            # Test valid input
            result = safe_int_input("Enter number: ", min_val=1, max_val=10)
            assert result == 10

    def test_migrate_task_data(self):
        """Test task data migration."""
        data = {
            "backlog": [
                {"task": "Task 1"},  # Missing state
                {"task": "Task 2", "state": "active"},  # Has state
            ],
            "2025-05-30": {
                "todo": {"task": "Active task"},  # Missing state
                "done": [
                    {"task": {"task": "Done task"}},  # Missing state
                    {"task": {"task": "Done task 2", "state": "done"}},  # Has state
                ],
            },
        }
        migrated = migrate_task_data(data)
        assert migrated is True
        assert data["backlog"][0]["state"] == "active"
        assert data["backlog"][1]["state"] == "active"
        assert data["2025-05-30"]["todo"]["state"] == "active"
        assert data["2025-05-30"]["done"][0]["task"]["state"] == "done"
        assert data["2025-05-30"]["done"][1]["task"]["state"] == "done"

    def test_parse_filter_string(self):
        """Test filter string parsing."""
        # Test valid filters
        valid, cats, tags, msg = parse_filter_string("@work,#urgent")
        assert valid is True
        assert cats == ["work"]
        assert tags == ["urgent"]
        assert msg == ""

        # Test invalid filters
        valid, cats, tags, msg = parse_filter_string("work,#urgent")
        assert valid is False
        assert cats == []
        assert tags == ["urgent"]
        assert "Must start with @" in msg

        # Test empty/invalid category
        valid, cats, tags, msg = parse_filter_string("@,#urgent")
        assert valid is False
        assert cats == []
        assert tags == ["urgent"]
        assert "Name cannot be empty" in msg

        # Test invalid format
        valid, cats, tags, msg = parse_filter_string("@work!,#urgent")
        assert valid is False
        assert cats == []
        assert tags == ["urgent"]
        assert "Use letters" in msg

    def test_filter_tasks_by_tags_or_categories(self):
        """Test task filtering by tags and categories."""
        tasks = [
            {"task": "Task 1", "categories": ["work"], "tags": ["urgent"]},
            {"task": "Task 2", "categories": ["personal"], "tags": ["low"]},
            {"task": "Task 3 @work #urgent"},  # Legacy format
            "Task 4 @personal #low",  # String format
        ]

        # Test category filter
        filtered = filter_tasks_by_tags_or_categories(tasks, filter_categories=["work"])
        assert len(filtered) == 2
        assert any(t.get("task") == "Task 1" for t in filtered)
        assert any("Task 3" in str(t) for t in filtered)

        # Test tag filter
        filtered = filter_tasks_by_tags_or_categories(tasks, filter_tags=["urgent"])
        assert len(filtered) == 2
        assert any(t.get("task") == "Task 1" for t in filtered)
        assert any("Task 3" in str(t) for t in filtered)

        # Test combined filter
        filtered = filter_tasks_by_tags_or_categories(
            tasks, filter_categories=["work"], filter_tags=["urgent"]
        )
        assert len(filtered) == 2
        assert any(t.get("task") == "Task 1" for t in filtered)
        assert any("Task 3" in str(t) for t in filtered)

    def test_filter_single_task_by_tags_or_categories(self):
        """Test single task filtering by tags and categories."""
        # Test dict format
        task = {"task": "Task 1", "categories": ["work"], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(
            task, filter_categories=["work"]
        )
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent"])
        assert not filter_single_task_by_tags_or_categories(
            task, filter_categories=["personal"]
        )

        # Test legacy format
        task = {"task": "Task 2 @work #urgent"}
        assert filter_single_task_by_tags_or_categories(
            task, filter_categories=["work"]
        )
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent"])

        # Test string format
        task = "Task 3 @work #urgent"
        assert filter_single_task_by_tags_or_categories(
            task, filter_categories=["work"]
        )
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent"])

    def test_validate_tag_format(self):
        """Test tag format validation."""
        # Valid tags
        assert validate_tag_format("work")
        assert validate_tag_format("work-123")
        assert validate_tag_format("work_123")
        assert validate_tag_format("a" * 50)  # Max length

        # Invalid tags
        assert not validate_tag_format("")  # Empty
        assert not validate_tag_format("a" * 51)  # Too long
        assert not validate_tag_format("work!")  # Special char
        assert not validate_tag_format("work space")  # Space
        assert not validate_tag_format("@work")  # @ prefix
        assert not validate_tag_format("#work")  # # prefix

    def test_extract_categories_from_tasks(self):
        """Test category extraction from tasks."""
        tasks = [
            {"categories": ["work", "personal"]},  # New format
            {"task": "Task @work @urgent"},  # Legacy format
            {
                "task": {"task": "Task @meeting", "categories": ["project"]}
            },  # Nested format
            {"task": "Task @review"},  # String format in dict
            {},  # Empty dict
        ]
        categories = extract_categories_from_tasks(tasks)
        # Convert to set for order-independent comparison
        assert set(categories) == {
            "work",
            "personal",
            "urgent",
            "meeting",
            "project",
            "review",
        }

    def test_prompt_next_action(self, capsys):
        """Test next action prompting."""
        data = {"backlog": [{"task": "Backlog task"}]}

        # Test pull from backlog
        with patch("momentum.cli.safe_input", return_value="p"):
            action, task = prompt_next_action(data)
            assert action == "pull"
            assert task is None

        # Test add new task
        with patch("momentum.cli.safe_input", side_effect=["a", "New task"]):
            action, task = prompt_next_action(data)
            assert action == "add"
            assert task == "New task"

        # Test skip
        with patch("momentum.cli.safe_input", return_value=""):
            action, task = prompt_next_action(data)
            assert action is None
            assert task is None

        # Test with empty backlog
        data = {"backlog": []}
        with patch("momentum.cli.safe_input", side_effect=["a", "New task"]):
            action, task = prompt_next_action(data)
            assert action == "add"
            assert task == "New task"  # Should get the task back, not None

    def test_create_task_data(self):
        """Test task data creation."""
        # Test basic task
        task_data = create_task_data("Simple task")
        assert task_data["task"] == "Simple task"
        assert task_data["categories"] == []
        assert task_data["tags"] == []
        assert task_data["state"] == "active"
        assert "ts" in task_data

        # Test task with tags
        task_data = create_task_data("Task @work #urgent")
        assert task_data["task"] == "Task @work #urgent"
        assert task_data["categories"] == ["work"]
        assert task_data["tags"] == ["urgent"]
        assert task_data["state"] == "active"

        # Test task with multiple tags
        task_data = create_task_data("Task @work @personal #urgent #review")
        assert task_data["task"] == "Task @work @personal #urgent #review"
        assert set(task_data["categories"]) == {"work", "personal"}
        assert set(task_data["tags"]) == {"urgent", "review"}
