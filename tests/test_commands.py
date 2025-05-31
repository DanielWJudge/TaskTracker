"""Tests for CLI command functions."""

from unittest.mock import patch, MagicMock
import json

import tasker
from tasker import (
    cmd_add, cmd_done, cmd_status, cmd_newday, cmd_backlog,
    complete_current_task, handle_next_task_selection
)


class TestCmdAdd:
    """Test the cmd_add command function."""
    
    def test_add_valid_task_to_empty_todo(self, temp_storage, plain_mode, mock_datetime, capsys):
        """Test adding a valid task when no active task exists."""
        # Create mock args
        args = MagicMock()
        args.task = "Test task"
        args.store = str(temp_storage) # Ensure cmd_add uses temp_storage
        
        with patch('tasker.STORE', temp_storage): # Patch STORE for tasker.load()
            cmd_add(args)
            
            # Check output
            captured = capsys.readouterr()
            assert "Added: Test task" in captured.out
            assert "=== TODAY:" in captured.out  # status should be shown
            
            # Check data was saved - now expecting structured format
            data = tasker.load() # Loads from temp_storage due to patch
            today = tasker.ensure_today(data)
        assert isinstance(today["todo"], dict)
        assert today["todo"]["task"] == "Test task"
        assert today["todo"]["categories"] == []
        assert today["todo"]["tags"] == []
    
    def test_add_task_when_active_task_exists_decline(self, temp_storage, plain_mode, capsys):
        """Test adding task when active task exists and user declines backlog."""
        # Setup existing active task - use new format
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Existing task",
                    "categories": [],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00"
                },
                "done": []
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.task = "New task"
        args.store = str(temp_storage)
        with patch('tasker.safe_input', return_value='n'), \
             patch('tasker.today_key', return_value='2025-05-30'):
            cmd_add(args)
        
        captured = capsys.readouterr()
        assert "Active task already exists: Existing task" in captured.out
        
        # Verify task wasn't added to backlog
        updated_data = tasker.load()
        assert len(updated_data["backlog"]) == 0
    
    @patch('tasker.save', return_value=True)
    def test_add_task_when_active_task_exists_accept_backlog(self, mock_save, temp_storage, plain_mode, capsys):
        """Test adding task to backlog when active task exists and user accepts."""
        # Setup existing active task - use new format
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Existing task",
                    "categories": [],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00"
                },
                "done": []
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.task = "New task"
        args.store = str(temp_storage)
        with patch('tasker.safe_input', return_value='y'), \
             patch('tasker.today_key', return_value='2025-05-30'):
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
        data = tasker.load()
        today = tasker.ensure_today(data)
        assert today["todo"] is None
    
    def test_add_task_with_whitespace(self, temp_storage, plain_mode, capsys):
        """Test adding task with leading/trailing whitespace."""
        args = MagicMock()
        args.task = "  Test task with spaces  "
        args.store = str(temp_storage)
        cmd_add(args)
        
        # Check that whitespace was stripped - now expecting structured format
        data = tasker.load()
        today = tasker.ensure_today(data)
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
    
    @patch('tasker.handle_next_task_selection')
    def test_done_with_active_task(self, mock_handle_next, temp_storage, plain_mode, mock_datetime, capsys):
        """Test completing an active task."""
        # Setup active task - use legacy string format to test migration
        data = {"2025-05-30": {"todo": "Test task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_done uses temp_storage
        
        captured_out = ""
        today_data_after_cmd = None

        with patch('tasker.today_key', return_value='2025-05-30'), \
             patch('tasker.STORE', temp_storage): # Patch global STORE for the test's load and ensure_today
            cmd_done(args)
            
            # Capture output from cmd_done itself
            # capsys needs to be read after the command if we want its output
            # but for data checks, load must happen under the same patch.
            captured = capsys.readouterr() # Capture output of cmd_done
            captured_out = captured.out

            # Check data was updated by loading within the patch context
            updated_data = tasker.load() # Should load from temp_storage due to patch
            today_data_after_cmd = tasker.ensure_today(updated_data)
        
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
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_done uses temp_storage
        
        with patch('tasker.save', return_value=False), \
             patch('tasker.handle_next_task_selection') as mock_handle_next, \
             patch('tasker.today_key', return_value='2025-05-30'):
            cmd_done(args)
            
            # With the updated code, cmd_done returns early if save fails
            # so handle_next_task_selection should NOT be called
            mock_handle_next.assert_not_called()


class TestCompleteCurrentTask:
    """Test the complete_current_task helper function."""
    
    def test_complete_current_task(self, mock_datetime, capsys):
        """Test marking current task as complete."""
        today = {"todo": "Test task", "done": []}
        
        with patch('tasker.today_key', return_value='2025-05-30'): # Not strictly necessary here but good for consistency
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
                {"task": "Second task", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        
        today = data["2025-05-30"]
        
        with patch('tasker.safe_input', return_value='2'), \
             patch('tasker.save', return_value=True), \
             patch('tasker.cmd_status'), \
             patch('tasker.today_key', return_value='2025-05-30'):
            
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
            "2025-05-30": {"todo": None, "done": []}
        }
        today = data["2025-05-30"]
        
        with patch('tasker.safe_input', return_value='5'), \
             patch('tasker.today_key', return_value='2025-05-30'):  # invalid index
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
        
        with patch('tasker.safe_input', side_effect=['n', 'New interactive task']), \
             patch('tasker.save', return_value=True), \
             patch('tasker.cmd_status'), \
             patch('tasker.today_key', return_value='2025-05-30'):
            
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
        
        with patch('tasker.safe_input', return_value=''), \
             patch('tasker.today_key', return_value='2025-05-30'): # User presses Enter
            handle_next_task_selection(data, today)
        
        # Check nothing was changed
        assert today["todo"] is None
    
    def test_user_cancels_input(self, plain_mode):
        """Test user cancelling input (Ctrl+C)."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        today = data["2025-05-30"]
        
        with patch('tasker.safe_input', return_value=None), \
             patch('tasker.today_key', return_value='2025-05-30'): # safe_input returns None on cancel
            handle_next_task_selection(data, today)
        
        # Check nothing was changed
        assert today["todo"] is None


class TestCmdStatus:
    """Test the cmd_status command function."""
    
    def test_status_no_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with no tasks."""
        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_status uses temp_storage
        args.filter = None # Ensure filter is None if not provided

        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_status(args)

        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "No completed tasks yet." in captured.out
        assert "TBD" in captured.out
    
    def test_status_with_active_task(self, temp_storage, plain_mode, capsys):
        """Test status display with active task."""
        # Use legacy string format to test backward compatibility
        data = {"2025-05-30": {"todo": "Current task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_status uses temp_storage
        args.filter = None # Ensure filter is None if not provided

        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_status(args)

        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "Current task" in captured.out
    
    def test_status_with_completed_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with completed tasks."""
        data = {
            "2025-05-30": {
                "todo": "Active task", # Use new format for active task
                "done": [
                    # Use new dict format for completed tasks
                    {"id": "abc123", "task": {"task":"Completed task 1", "categories":[], "tags":[]}, "ts": "2025-05-30T09:00:00"},
                    {"id": "def456", "task": {"task":"Completed task 2", "categories":[], "tags":[]}, "ts": "2025-05-30T10:30:00"}
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')

        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_status uses temp_storage
        args.filter = None # Ensure filter is None if not provided

        with patch('tasker.today_key', return_value='2025-05-30'):
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
        args.store = str(temp_storage) # Ensure cmd_newday uses temp_storage
        
        today_key_val = '2025-05-30'
        loaded_data_after_cmd = None

        with patch('tasker.today_key', return_value=today_key_val), \
             patch('tasker.STORE', temp_storage): # Patch STORE for tasker.load()
            cmd_newday(args)
            loaded_data_after_cmd = tasker.load() # Load within patch context
        
        captured = capsys.readouterr()
        assert "New day initialized" in captured.out
        assert today_key_val in captured.out
        
        # Check data structure was created
        assert today_key_val in loaded_data_after_cmd
        assert "backlog" in loaded_data_after_cmd
    
    def test_newday_save_failure(self, temp_storage, plain_mode, capsys):
        """Test new day initialization when save fails."""
        args = MagicMock()
        args.store = str(temp_storage) # Ensure cmd_newday uses temp_storage
        
        with patch('tasker.save', return_value=False), \
             patch('tasker.today_key', return_value='2025-05-30'):
            cmd_newday(args)
        
        captured = capsys.readouterr()
        # With the updated code, cmd_newday only shows success message if save succeeds
        assert "New day initialized" not in captured.out


class TestCmdBacklog:
    """Test the cmd_backlog command function."""
    
    def test_backlog_add_valid_task(self, temp_storage, plain_mode, mock_datetime, capsys):
        """Test adding valid task to backlog."""
        args = MagicMock()
        args.subcmd = "add"
        args.task = "Backlog task"
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        backlog_after_cmd = None
        with patch('tasker.STORE', temp_storage): # Patch STORE for tasker.load()
            cmd_backlog(args)
            # Check data was saved - now expecting structured format
            data = tasker.load() # Loads from temp_storage
            backlog_after_cmd = tasker.get_backlog(data)

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
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        # The validation now properly works for empty tasks
        assert "Task name cannot be empty" in captured.out
    
    def test_backlog_list_empty(self, temp_storage, plain_mode, capsys):
        """Test listing empty backlog."""
        args = MagicMock()
        args.subcmd = "list"
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog:" in captured.out
    
    def test_backlog_list_with_items(self, temp_storage, plain_mode, capsys):
        """Test listing backlog with items."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
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
                    "ts": "2025-05-30T10:00:00"
                },
                "done": []
            }
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "pull"
        args.index = None
        args.filter = None # Ensure filter is None for status call
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage

        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Active task already exists" in captured.out
    
    def test_backlog_pull_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test pulling from empty backlog."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "pull"
        args.index = None
        args.filter = None
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage

        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "No backlog items to pull" in captured.out
    
    def test_backlog_pull_by_index(self, temp_storage, plain_mode, capsys):
        """Test pulling specific backlog item by index."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "pull"
        args.index = 2  # pull second item
        args.filter = None
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage

        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Pulled from backlog:" in captured.out
        assert "Second task" in captured.out
    
    def test_backlog_remove_valid_index(self, temp_storage, plain_mode, capsys):
        """Test removing backlog item by valid index."""
        data = {
            "backlog": [
                {"task": "First task", "ts": "2025-05-30T10:00:00"},
                {"task": "Second task", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 1  # remove first item (1-based)
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        with patch('tasker.save', return_value=True):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Removed from backlog:" in captured.out
        assert "First task" in captured.out
    
    def test_backlog_remove_invalid_index(self, temp_storage, plain_mode, capsys):
        """Test removing backlog item by invalid index."""
        data = {
            "backlog": [{"task": "Only task", "ts": "2025-05-30T10:00:00"}],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 5  # invalid index
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Invalid backlog index: 5" in captured.out
        # The current code doesn't show valid range, just the basic error message
    
    def test_backlog_remove_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test removing from empty backlog."""
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 1
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        # The updated code properly shows "No backlog items to remove" for empty backlog
        assert "No backlog items to remove" in captured.out
