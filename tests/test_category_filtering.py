"""Tests for category filtering functionality."""

import pytest
import json
from unittest.mock import MagicMock, patch
from tasker import (
    parse_filter_categories, filter_tasks_by_categories, filter_single_task_by_categories,
    cmd_status, cmd_backlog
)


class TestParseFilterCategories:
    """Test the parse_filter_categories function."""
    
    def test_empty_filter(self):
        """Test parsing empty filter string."""
        is_valid, categories, error = parse_filter_categories("")
        assert is_valid is True
        assert categories == []
        assert error == ""
    
    def test_none_filter(self):
        """Test parsing None filter."""
        is_valid, categories, error = parse_filter_categories(None)
        assert is_valid is True
        assert categories == []
        assert error == ""
    
    def test_single_category(self):
        """Test parsing single category."""
        is_valid, categories, error = parse_filter_categories("@work")
        assert is_valid is True
        assert categories == ["work"]
        assert error == ""
    
    def test_multiple_categories(self):
        """Test parsing multiple categories."""
        is_valid, categories, error = parse_filter_categories("@work,@personal")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert error == ""
    
    def test_categories_with_spaces(self):
        """Test parsing categories with spaces around commas."""
        is_valid, categories, error = parse_filter_categories("@work, @personal, @client")
        assert is_valid is True
        assert categories == ["work", "personal", "client"]
        assert error == ""
    
    def test_duplicate_categories(self):
        """Test parsing with duplicate categories."""
        is_valid, categories, error = parse_filter_categories("@work,@personal,@work")
        assert is_valid is True
        assert categories == ["work", "personal"]  # duplicates removed
        assert error == ""
    
    def test_case_normalization(self):
        """Test that categories are normalized to lowercase."""
        is_valid, categories, error = parse_filter_categories("@Work,@PERSONAL,@Client")
        assert is_valid is True
        assert categories == ["work", "personal", "client"]
        assert error == ""
    
    def test_categories_with_underscores_and_hyphens(self):
        """Test parsing categories with valid special characters."""
        is_valid, categories, error = parse_filter_categories("@work_project,@client-alpha")
        assert is_valid is True
        assert categories == ["work_project", "client-alpha"]
        assert error == ""
    
    def test_categories_with_numbers(self):
        """Test parsing categories with numbers."""
        is_valid, categories, error = parse_filter_categories("@project2024,@team1")
        assert is_valid is True
        assert categories == ["project2024", "team1"]
        assert error == ""
    
    def test_missing_at_symbol(self):
        """Test error when @ symbol is missing."""
        is_valid, categories, error = parse_filter_categories("work,personal")
        assert is_valid is False
        assert categories == []
        assert "Categories must start with @" in error
        assert "work" in error
    
    def test_mixed_valid_invalid(self):
        """Test error when mixing valid and invalid categories."""
        is_valid, categories, error = parse_filter_categories("@work,personal")
        assert is_valid is False
        assert categories == []
        assert "Categories must start with @" in error
        assert "personal" in error
    
    def test_invalid_characters(self):
        """Test error with invalid characters in category names."""
        is_valid, categories, error = parse_filter_categories("@work space")
        assert is_valid is False
        assert categories == []
        assert "Invalid category format" in error
    
    def test_empty_category_name(self):
        """Test error with empty category name after @."""
        is_valid, categories, error = parse_filter_categories("@")
        assert is_valid is False
        assert categories == []
        assert "Invalid category format" in error
    
    def test_special_characters_invalid(self):
        """Test error with special characters in category names."""
        is_valid, categories, error = parse_filter_categories("@work!")
        assert is_valid is False
        assert categories == []
        assert "Invalid category format" in error


class TestFilterTasksByCategories:
    """Test the filter_tasks_by_categories function."""
    
    def setup_method(self):
        """Set up test data."""
        self.tasks = [
            {
                "task": "Work meeting @work",
                "categories": ["work"],
                "tags": [],
                "ts": "2025-05-30T10:00:00"
            },
            {
                "task": "Personal task @personal", 
                "categories": ["personal"],
                "tags": [],
                "ts": "2025-05-30T11:00:00"
            },
            {
                "task": "Mixed task @work @personal",
                "categories": ["work", "personal"],
                "tags": [],
                "ts": "2025-05-30T12:00:00"
            },
            {
                "task": "Client work @client @work",
                "categories": ["client", "work"],
                "tags": ["urgent"],
                "ts": "2025-05-30T13:00:00"
            },
            {
                "task": "No category task",
                "categories": [],
                "tags": [],
                "ts": "2025-05-30T14:00:00"
            }
        ]
    
    def test_no_filter_returns_all(self):
        """Test that empty filter returns all tasks."""
        result = filter_tasks_by_categories(self.tasks, [])
        assert len(result) == 5
        assert result == self.tasks
    
    def test_single_category_filter(self):
        """Test filtering by single category."""
        result = filter_tasks_by_categories(self.tasks, ["work"])
        assert len(result) == 3  # 3 tasks have @work
        
        # Check that correct tasks are returned
        task_texts = [t["task"] for t in result]
        assert "Work meeting @work" in task_texts
        assert "Mixed task @work @personal" in task_texts
        assert "Client work @client @work" in task_texts
    
    def test_multiple_category_filter(self):
        """Test filtering by multiple categories (OR logic)."""
        result = filter_tasks_by_categories(self.tasks, ["work", "personal"])
        assert len(result) == 4  # Fixed: tasks with @work OR @personal
        # Should include: Work meeting @work, Personal task @personal, 
        # Mixed task @work @personal, Client work @client @work
        
        # Check that correct tasks are returned
        task_texts = [t["task"] for t in result]
        assert "Work meeting @work" in task_texts
        assert "Personal task @personal" in task_texts
        assert "Mixed task @work @personal" in task_texts
        assert "Client work @client @work" in task_texts
    
    def test_nonexistent_category(self):
        """Test filtering by category that doesn't exist."""
        result = filter_tasks_by_categories(self.tasks, ["nonexistent"])
        assert len(result) == 0
    
    def test_client_category_filter(self):
        """Test filtering by client category."""
        result = filter_tasks_by_categories(self.tasks, ["client"])
        assert len(result) == 1
        assert result[0]["task"] == "Client work @client @work"
    
    def test_case_insensitive_filtering(self):
        """Test that filtering is case insensitive."""
        # Add a task with mixed case categories
        mixed_case_task = {
            "task": "Mixed case @Work",
            "categories": ["work"],  # stored normalized
            "tags": [],
            "ts": "2025-05-30T15:00:00"
        }
        tasks_with_mixed = self.tasks + [mixed_case_task]
        
        result = filter_tasks_by_categories(tasks_with_mixed, ["work"])
        assert len(result) == 4  # should include mixed case task
    
    def test_legacy_format_tasks(self):
        """Test filtering tasks in legacy string format."""
        legacy_tasks = [
            {"task": "Legacy work task @work"},
            {"task": "Legacy personal @personal"},
            {"task": "Legacy no category"}
        ]
        
        result = filter_tasks_by_categories(legacy_tasks, ["work"])
        assert len(result) == 1
        assert result[0]["task"] == "Legacy work task @work"
    
    def test_very_old_format_tasks(self):
        """Test filtering very old format (just strings)."""
        old_tasks = [
            "Old work task @work",
            "Old personal @personal", 
            "Old no category"
        ]
        
        result = filter_tasks_by_categories(old_tasks, ["work"])
        assert len(result) == 1
        assert result[0] == "Old work task @work"
    
    def test_mixed_format_tasks(self):
        """Test filtering with mixed task formats."""
        mixed_tasks = [
            {  # New format
                "task": "New format @work",
                "categories": ["work"],
                "tags": [],
                "ts": "2025-05-30T10:00:00"
            },
            {"task": "Legacy format @personal"},  # Legacy format
            "Very old format @client"  # Very old format
        ]
        
        result = filter_tasks_by_categories(mixed_tasks, ["work"])
        assert len(result) == 1
        assert result[0]["task"] == "New format @work"
        
        result = filter_tasks_by_categories(mixed_tasks, ["personal"])
        assert len(result) == 1
        assert result[0]["task"] == "Legacy format @personal"
        
        result = filter_tasks_by_categories(mixed_tasks, ["client"])
        assert len(result) == 1
        assert result[0] == "Very old format @client"


class TestFilterSingleTaskByCategories:
    """Test the filter_single_task_by_categories function."""
    
    def test_no_filter_returns_true(self):
        """Test that no filter always returns True."""
        task = {"task": "Any task", "categories": ["work"]}
        assert filter_single_task_by_categories(task, []) is True
    
    def test_matching_category(self):
        """Test task matches filter category."""
        task = {"task": "Work task @work", "categories": ["work"]}
        assert filter_single_task_by_categories(task, ["work"]) is True
    
    def test_non_matching_category(self):
        """Test task doesn't match filter category."""
        task = {"task": "Work task @work", "categories": ["work"]}
        assert filter_single_task_by_categories(task, ["personal"]) is False
    
    def test_multiple_categories_task(self):
        """Test task with multiple categories."""
        task = {"task": "Mixed @work @personal", "categories": ["work", "personal"]}
        assert filter_single_task_by_categories(task, ["work"]) is True
        assert filter_single_task_by_categories(task, ["personal"]) is True
        assert filter_single_task_by_categories(task, ["client"]) is False
    
    def test_multiple_filter_categories(self):
        """Test filtering with multiple categories (OR logic)."""
        task = {"task": "Work task @work", "categories": ["work"]}
        assert filter_single_task_by_categories(task, ["work", "personal"]) is True
        assert filter_single_task_by_categories(task, ["personal", "client"]) is False
    
    def test_legacy_format_task(self):
        """Test filtering legacy format task."""
        task = {"task": "Legacy work @work"}
        assert filter_single_task_by_categories(task, ["work"]) is True
        assert filter_single_task_by_categories(task, ["personal"]) is False
    
    def test_string_format_task(self):
        """Test filtering string format task."""
        task = "String work task @work"
        assert filter_single_task_by_categories(task, ["work"]) is True
        assert filter_single_task_by_categories(task, ["personal"]) is False


class TestStatusCommandFiltering:
    """Test cmd_status with category filtering."""
    
    def test_status_with_filter(self, temp_storage, plain_mode, capsys):
        """Test status command with category filter."""
        # Setup test data with mixed categories
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Active work task @work",
                    "categories": ["work"],
                    "tags": [],
                    "ts": "2025-05-30T12:00:00"
                },
                "done": [
                    {
                        "id": "abc123",
                        "task": {
                            "task": "Completed work @work",
                            "categories": ["work"],
                            "tags": [],
                            "ts": "2025-05-30T10:00:00"
                        },
                        "ts": "2025-05-30T11:00:00"
                    },
                    {
                        "id": "def456", 
                        "task": {
                            "task": "Completed personal @personal",
                            "categories": ["personal"],
                            "tags": [],
                            "ts": "2025-05-30T09:00:00"
                        },
                        "ts": "2025-05-30T10:30:00"
                    }
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        # Test filtering by work category
        args = MagicMock()
        args.filter = "@work"
        
        cmd_status(args)
        
        captured = capsys.readouterr()
        assert "(filtered by: @work)" in captured.out
        assert "Active work task @work" in captured.out
        assert "Completed work @work" in captured.out
        assert "Completed personal @personal" not in captured.out
    
    def test_status_no_matches(self, temp_storage, plain_mode, capsys):
        """Test status when no tasks match filter."""
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Personal task @personal",
                    "categories": ["personal"],
                    "tags": [],
                    "ts": "2025-05-30T12:00:00"
                },
                "done": []
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.filter = "@work"
        
        cmd_status(args)
        
        captured = capsys.readouterr()
        assert "No active task matches filter" in captured.out
        assert "No completed tasks match the filter" in captured.out
    
    def test_status_invalid_filter(self, temp_storage, plain_mode, capsys):
        """Test status with invalid filter."""
        args = MagicMock()
        args.filter = "work"  # missing @
        
        cmd_status(args)
        
        captured = capsys.readouterr()
        assert "Categories must start with @" in captured.out
    
    def test_status_multiple_categories(self, temp_storage, plain_mode, capsys):
        """Test status with multiple category filter."""
        data = {
            "2025-05-30": {
                "todo": {
                    "task": "Work task @work",
                    "categories": ["work"],
                    "tags": [],
                    "ts": "2025-05-30T12:00:00"
                },
                "done": [
                    {
                        "id": "abc123",
                        "task": {
                            "task": "Personal task @personal",
                            "categories": ["personal"],
                            "tags": [],
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
        args.filter = "@work,@personal"
        
        cmd_status(args)
        
        captured = capsys.readouterr()
        assert "(filtered by: @work, @personal)" in captured.out
        assert "Work task @work" in captured.out
        assert "Personal task @personal" in captured.out


class TestBacklogCommandFiltering:
    """Test cmd_backlog with category filtering."""
    
    def test_backlog_list_with_filter(self, temp_storage, plain_mode, capsys):
        """Test backlog list command with category filter."""
        data = {
            "backlog": [
                {
                    "task": "Work backlog @work",
                    "categories": ["work"],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00"
                },
                {
                    "task": "Personal backlog @personal",
                    "categories": ["personal"],
                    "tags": [],
                    "ts": "2025-05-30T11:00:00"
                },
                {
                    "task": "Client work @client @work",
                    "categories": ["client", "work"],
                    "tags": [],
                    "ts": "2025-05-30T12:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog (filtered by: @work):" in captured.out
        assert "Work backlog @work" in captured.out
        assert "Client work @client @work" in captured.out
        assert "Personal backlog @personal" not in captured.out
    
    def test_backlog_list_no_matches(self, temp_storage, plain_mode, capsys):
        """Test backlog list when no items match filter."""
        data = {
            "backlog": [
                {
                    "task": "Personal task @personal",
                    "categories": ["personal"],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "No backlog items match the filter." in captured.out
    
    def test_backlog_list_invalid_filter(self, temp_storage, plain_mode, capsys):
        """Test backlog list with invalid filter."""
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "work"  # missing @
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Categories must start with @" in captured.out
    
    def test_backlog_list_multiple_categories(self, temp_storage, plain_mode, capsys):
        """Test backlog list with multiple category filter."""
        data = {
            "backlog": [
                {
                    "task": "Work task @work",
                    "categories": ["work"],
                    "tags": [],
                    "ts": "2025-05-30T10:00:00"
                },
                {
                    "task": "Personal task @personal",
                    "categories": ["personal"], 
                    "tags": [],
                    "ts": "2025-05-30T11:00:00"
                },
                {
                    "task": "Client task @client",
                    "categories": ["client"],
                    "tags": [],
                    "ts": "2025-05-30T12:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work,@personal"
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog (filtered by: @work, @personal):" in captured.out
        assert "Work task @work" in captured.out
        assert "Personal task @personal" in captured.out
        assert "Client task @client" not in captured.out
    
    def test_backlog_list_legacy_format(self, temp_storage, plain_mode, capsys):
        """Test backlog list filtering with legacy format tasks."""
        data = {
            "backlog": [
                {"task": "Legacy work @work", "ts": "2025-05-30T10:00:00"},
                {"task": "Legacy personal @personal", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Legacy work @work" in captured.out
        assert "Legacy personal @personal" not in captured.out


class TestFilteringEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_backlog_with_filter(self, temp_storage, plain_mode, capsys):
        """Test filtering empty backlog."""
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        
        cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "No backlog items match the filter." in captured.out
    
    def test_whitespace_only_filter(self):
        """Test filter with only whitespace."""
        is_valid, categories, error = parse_filter_categories("   ")
        assert is_valid is True
        assert categories == []
        assert error == ""
    
    def test_comma_only_filter(self):
        """Test filter with only commas."""
        is_valid, categories, error = parse_filter_categories(",,,")
        assert is_valid is True
        assert categories == []
        assert error == ""
    
    def test_mixed_whitespace_and_commas(self):
        """Test filter with mixed whitespace and commas."""
        is_valid, categories, error = parse_filter_categories(" , @work , , @personal , ")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert error == ""
    
    def test_filter_with_at_but_no_name(self):
        """Test filter with @ but no category name."""
        is_valid, categories, error = parse_filter_categories("@,@work")
        assert is_valid is False
        assert categories == []
        assert "Invalid category format" in error
