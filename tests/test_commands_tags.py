"""Command tests for tagged task functionality."""

import json
from unittest.mock import MagicMock, patch
from tasker import cmd_add, cmd_status, cmd_backlog, create_task_data


class TestTaggedTaskCommands:
    """Test command functions with tagged tasks."""
    
    def test_cmd_add_tagged_task(self, temp_storage, plain_mode, capsys):
        """Test adding a tagged task through cmd_add."""
        args = MagicMock()
        args.task = "Deploy feature @work #urgent"
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_add(args)
        
        captured = capsys.readouterr()
        assert "Added:" in captured.out
        assert "Deploy feature @work #urgent" in captured.out
        
        # Verify data structure
        data = json.loads(temp_storage.read_text(encoding='utf-8'))
        today_key = [k for k in data.keys() if k.startswith("2025-")][0]
        todo = data[today_key]["todo"]
        
        assert isinstance(todo, dict)
        assert todo["task"] == "Deploy feature @work #urgent"
        assert todo["categories"] == ["work"]
        assert todo["tags"] == ["urgent"]
        assert "ts" in todo
    
    def test_cmd_add_tagged_task_to_backlog(self, temp_storage, plain_mode, capsys):
        """Test adding tagged task to backlog when active task exists."""
        # Setup existing active task
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
        args.task = "New tagged task @work #urgent"
        args.store = str(temp_storage)
        with patch('tasker.safe_input', return_value='y'), \
             patch('tasker.today_key', return_value='2025-05-30'):
            cmd_add(args)
        
        captured = capsys.readouterr()
        assert "Added to backlog:" in captured.out
        
        # Verify backlog structure
        updated_data = json.loads(temp_storage.read_text(encoding='utf-8'))
        backlog = updated_data["backlog"]
        
        assert len(backlog) == 1
        assert backlog[0]["task"] == "New tagged task @work #urgent"
        assert backlog[0]["categories"] == ["work"]
        assert backlog[0]["tags"] == ["urgent"]
    
    def test_cmd_status_with_tagged_tasks(self, temp_storage, plain_mode, capsys):
        """Test status display with tagged tasks."""
        # Setup data with tagged tasks
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Active task @work #urgent",
                    "categories": ["work"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T12:00:00"
                },
                "done": [
                    {
                        "id": "abc123",
                        "task": {
                            "task": "Completed task @personal #low",
                            "categories": ["personal"],
                            "tags": ["low"],
                            "ts": "2025-05-30T10:00:00"
                        },
                        "ts": "2025-05-30T11:00:00"
                    }
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_status(args)
        
        captured = capsys.readouterr()
        assert "=== TODAY: 2025-05-30 ===" in captured.out
        assert "Completed task @personal #low" in captured.out
        assert "Active task @work #urgent" in captured.out
    
    def test_cmd_status_legacy_compatibility(self, temp_storage, plain_mode, capsys):
        """Test status display with legacy (string) format tasks."""
        # Setup data with mixed legacy and new format
        data = {
            "2025-05-30": {
                "todo": "Legacy active @work #urgent",  # Old string format
                "done": [
                    {
                        "id": "abc123", 
                        "task": "Legacy completed @personal #low",  # Old string format
                        "ts": "2025-05-30T10:00:00"
                    }
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_status(args)
        
        captured = capsys.readouterr()
        assert "Legacy completed @personal #low" in captured.out
        assert "Legacy active @work #urgent" in captured.out
    
    def test_cmd_backlog_add_tagged_task(self, temp_storage, plain_mode, capsys):
        """Test adding tagged task to backlog."""
        args = MagicMock()
        args.subcmd = "add"
        args.task = "Review code @team #urgent"
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog task added: Review code @team #urgent" in captured.out
        
        # Verify data structure
        data = json.loads(temp_storage.read_text(encoding='utf-8'))
        backlog = data["backlog"]
        
        assert len(backlog) == 1
        assert backlog[0]["task"] == "Review code @team #urgent"
        assert backlog[0]["categories"] == ["team"]
        assert backlog[0]["tags"] == ["urgent"]
        assert "ts" in backlog[0]
    
    def test_cmd_backlog_list_tagged_tasks(self, temp_storage, plain_mode, capsys):
        """Test listing backlog with tagged tasks."""
        # Setup backlog with tagged tasks
        data = {
            "backlog": [
                {
                    "task": "First task @work #urgent",
                    "categories": ["work"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T10:00:00"
                },
                {
                    "task": "Second task @personal #low", 
                    "categories": ["personal"],
                    "tags": ["low"],
                    "ts": "2025-05-30T11:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog:" in captured.out
        assert "First task @work #urgent" in captured.out
        assert "Second task @personal #low" in captured.out
        assert "[05/30 10:00]" in captured.out
        assert "[05/30 11:00]" in captured.out
    
    def test_cmd_backlog_pull_tagged_task(self, temp_storage, plain_mode, capsys):
        """Test pulling tagged task from backlog."""
        # Setup backlog with tagged task
        data = {
            "backlog": [
                {
                    "task": "Backlog task @work #urgent",
                    "categories": ["work"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T10:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "pull"
        args.index = 1
        args.store = str(temp_storage)
        with patch('tasker.cmd_status'), \
             patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Pulled from backlog:" in captured.out
        assert "Backlog task @work #urgent" in captured.out
        
        # Verify task moved to active
        updated_data = json.loads(temp_storage.read_text(encoding='utf-8'))
        today_key = [k for k in updated_data.keys() if k.startswith("2025-")][0]
        todo = updated_data[today_key]["todo"]
        
        assert isinstance(todo, dict)
        assert todo["task"] == "Backlog task @work #urgent"
        assert todo["categories"] == ["work"]
        assert todo["tags"] == ["urgent"]
        
        # Backlog should be empty
        assert len(updated_data["backlog"]) == 0
    
    def test_cmd_backlog_remove_tagged_task(self, temp_storage, plain_mode, capsys):
        """Test removing tagged task from backlog."""
        # Setup backlog with tagged tasks
        data = {
            "backlog": [
                {
                    "task": "Keep this @work #urgent",
                    "categories": ["work"],
                    "tags": ["urgent"],
                    "ts": "2025-05-30T10:00:00"
                },
                {
                    "task": "Remove this @personal #low",
                    "categories": ["personal"], 
                    "tags": ["low"],
                    "ts": "2025-05-30T11:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "remove"
        args.index = 2  # Remove second item
        args.store = str(temp_storage)
        with patch('tasker.today_key', return_value='2025-05-30'):
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Removed from backlog:" in captured.out
        assert "Remove this @personal #low" in captured.out
        
        # Verify correct item was removed
        updated_data = json.loads(temp_storage.read_text(encoding='utf-8'))
        backlog = updated_data["backlog"]
        
        assert len(backlog) == 1
        assert backlog[0]["task"] == "Keep this @work #urgent"


class TestCreateTaskData:
    """Test the create_task_data function."""
    
    def test_create_task_data_with_tags(self):
        """Test creating task data with tags."""
        task_text = "Deploy feature @work #urgent"
        task_data = create_task_data(task_text)
        
        assert task_data["task"] == "Deploy feature @work #urgent"
        assert task_data["categories"] == ["work"]
        assert task_data["tags"] == ["urgent"]
        assert "ts" in task_data
        
        # Verify timestamp format
        from datetime import datetime
        ts = datetime.fromisoformat(task_data["ts"])
        assert ts is not None
    
    def test_create_task_data_no_tags(self):
        """Test creating task data without tags."""
        task_text = "Simple task"
        task_data = create_task_data(task_text)
        
        assert task_data["task"] == "Simple task"
        assert task_data["categories"] == []
        assert task_data["tags"] == []
        assert "ts" in task_data
    
    def test_create_task_data_multiple_tags(self):
        """Test creating task data with multiple categories and tags."""
        task_text = "Complex task @work @client #urgent #review #important"
        task_data = create_task_data(task_text)
        
        assert task_data["task"] == "Complex task @work @client #urgent #review #important"
        assert set(task_data["categories"]) == {"work", "client"}
        assert set(task_data["tags"]) == {"urgent", "review", "important"}
    
    def test_create_task_data_case_normalization(self):
        """Test that tags are normalized to lowercase."""
        task_text = "Task @Work @PERSONAL #Urgent #LOW"
        task_data = create_task_data(task_text)
        
        assert set(task_data["categories"]) == {"work", "personal"}
        assert set(task_data["tags"]) == {"urgent", "low"}
    
    def test_create_task_data_deduplication(self):
        """Test that duplicate tags are removed."""
        task_text = "Task @work @work #urgent #urgent"
        task_data = create_task_data(task_text)
        
        assert task_data["categories"] == ["work"]  # deduplicated
        assert task_data["tags"] == ["urgent"]  # deduplicated