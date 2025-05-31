"""Tests for CLI command functions."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
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
        
        cmd_add(args)
        
        # Check output
        captured = capsys.readouterr()
        assert "Added: Test task" in captured.out
        assert "=== TODAY:" in captured.out  # status should be shown
        
        # Check data was saved - now expecting structured format
        data = tasker.load()
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
        
        with patch('tasker.safe_input', return_value='n'):
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
        
        with patch('tasker.safe_input', return_value='y'):
            cmd_add(args)
        
        captured = capsys.readouterr()
        assert "Added to backlog:" in captured.out
        assert "New task" in captured.out
    
    def test_add_invalid_task(self, temp_storage, plain_mode, capsys):
        """Test adding an invalid task name."""
        args = MagicMock()
        args.task = ""  # empty task
        
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
        
        cmd_done(args)
        
        captured = capsys.readouterr()
        assert "Completed:" in captured.out
        assert "Test task" in captured.out
        
        # Check data was updated
        updated_data = tasker.load()
        today = tasker.ensure_today(updated_data)
        assert today["todo"] is None
        assert len(today["done"]) == 1
        # Task should now be stored in structured format
        assert isinstance(today["done"][0]["task"], dict)
        assert today["done"][0]["task"]["task"] == "Test task"
        
        # Check that next task selection was called
        mock_handle_next.assert_called_once()
    
    def test_done_save_failure(self, temp_storage, plain_mode, capsys):
        """Test behavior when save fails after completing task."""
        # Setup active task
        data = {"2025-05-30": {"todo": "Test task", "done": []}, "backlog": []}
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        
        with patch('tasker.save', return_value=False) as mock_save, \
             patch('tasker.handle_next_task_selection') as mock_handle_next:
            cmd_done(args)
            
            # With the updated code, cmd_done returns early if save fails
            # so handle_next_task_selection should NOT be called
            mock_handle_next.assert_not_called()


class TestCompleteCurrentTask:
    """Test the complete_current_task helper function."""
    
    def test_complete_current_task(self, mock_datetime, capsys):
        """Test marking current task as complete."""
        today = {"todo": "Test task", "done": []}
        
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
             patch('tasker.cmd_status'):
            
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
        
        with patch('tasker.safe_input', return_value='5'):  # invalid index
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
             patch('tasker.cmd_status'):
            
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
        
        with patch('tasker.safe_input', return_value=''):  # empty = skip
            handle_next_task_selection(data, today)
        
        # Check nothing was changed
        assert today["todo"] is None
    
    def test_user_cancels_input(self, plain_mode):
        """Test user cancelling input (Ctrl+C)."""
        data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        today = data["2025-05-30"]
        
        with patch('tasker.safe_input', return_value=None):  # cancelled input
            handle_next_task_selection(data, today)
        
        # Check nothing was changed
        assert today["todo"] is None


class TestCmdStatus:
    """Test the cmd_status command function."""
    
    def test_status_no_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with no tasks."""
        args = MagicMock()
        
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
        
        cmd_status(args)
        
        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "Current task" in captured.out
    
    def test_status_with_completed_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with completed tasks."""
        data = {
            "2025-05-30": {
                "todo": "Active task",
                "done": [
                    {"id": "abc123", "task": "Completed task 1", "ts": "2025-05-30T09:00:00"},
                    {"id": "def456", "task": "Completed task 2", "ts": "2025-05-30T10:30:00"}
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        
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
        
        cmd_newday(args)
        
        captured = capsys.readouterr()
        assert "New day initialized" in captured.out
        assert "2025-05-30" in captured.out
        
        # Check data structure was created (should be in file since mocking was removed)
        data = tasker.load()
        assert "2025-05-30" in data
        assert "backlog" in data
    
    def test_newday_save_failure(self, temp_storage, plain_mode, capsys):
        """Test new day initialization when save fails."""
        args = MagicMock()
        
        with patch('tasker.save', return_value=False):
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
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog task added: Backlog task" in captured.out
        
        # Check data was saved - now expecting structured format
        data = tasker.load()
        backlog = tasker.get_backlog(data)
        assert len(backlog) == 1
        assert backlog[0]["task"] == "Backlog task"
        assert backlog[0]["categories"] == []
        assert backlog[0]["tags"] == []
    
    def test_backlog_add_invalid_task(self, temp_storage, plain_mode, capsys):
        """Test adding invalid task to backlog."""
        args = MagicMock()
        args.subcmd = "add"
        args.task = ""  # empty task
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        # The validation now properly works for empty tasks
        assert "Task name cannot be empty" in captured.out
    
    def test_backlog_list_empty(self, temp_storage, plain_mode, capsys):
        """Test listing empty backlog."""
        args = MagicMock()
        args.subcmd = "list"
        
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
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Active task already exists" in captured.out
    
    def test_backlog_pull_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test pulling from empty backlog."""
        args = MagicMock()
        args.subcmd = "pull"
        args.index = None
        
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
        
        with patch('tasker.save', return_value=True), \
             patch('tasker.cmd_status'):
            
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
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Invalid backlog index: 5" in captured.out
        # The current code doesn't show valid range, just the basic error message
    
    def test_backlog_remove_empty_backlog(self, temp_storage, plain_mode, capsys):
        """Test removing from empty backlog."""
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 1
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        # The updated code properly shows "No backlog items to remove" for empty backlog
        assert "No backlog items to remove" in captured.out
