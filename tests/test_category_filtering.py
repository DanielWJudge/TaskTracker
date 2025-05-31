"""Tests for category filtering functionality."""

import pytest
import json
from unittest.mock import MagicMock, patch
from tasker import (
    parse_filter_string, filter_tasks_by_tags_or_categories, filter_single_task_by_tags_or_categories,
    cmd_status, cmd_backlog
)


class TestParseFilterCategories:
    """Test the parse_filter_string function."""
    
    def test_empty_filter(self):
        """Test parsing empty filter string."""
        is_valid, categories, tags, error = parse_filter_string("")
        assert is_valid is True
        assert categories == []
        assert tags == []
        assert error == ""
    
    def test_none_filter(self):
        """Test parsing None filter."""
        is_valid, categories, tags, error = parse_filter_string(None)
        assert is_valid is True
        assert categories == []
        assert tags == []
        assert error == ""
    
    def test_single_category(self):
        """Test parsing single category."""
        is_valid, categories, tags, error = parse_filter_string("@work")
        assert is_valid is True
        assert categories == ["work"]
        assert tags == []
        assert error == ""
    
    def test_single_tag(self):
        """Test parsing single tag."""
        is_valid, categories, tags, error = parse_filter_string("#urgent")
        assert is_valid is True
        assert categories == []
        assert tags == ["urgent"]
        assert error == ""
    
    def test_multiple_categories(self):
        """Test parsing multiple categories."""
        is_valid, categories, tags, error = parse_filter_string("@work,@personal")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert tags == []
        assert error == ""
    
    def test_multiple_tags(self):
        """Test parsing multiple tags."""
        is_valid, categories, tags, error = parse_filter_string("#urgent,#low")
        assert is_valid is True
        assert categories == []
        assert tags == ["urgent", "low"]
        assert error == ""
    
    def test_mixed_categories_tags(self):
        """Test parsing mixed categories and tags."""
        is_valid, categories, tags, error = parse_filter_string("@work,#urgent,@personal,#low")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert tags == ["urgent", "low"]
        assert error == ""
    
    def test_categories_with_spaces(self):
        """Test parsing categories with spaces around commas."""
        is_valid, categories, tags, error = parse_filter_string("@work, @personal, @client")
        assert is_valid is True
        assert categories == ["work", "personal", "client"]
        assert tags == []
        assert error == ""
    
    def test_duplicate_categories(self):
        """Test parsing with duplicate categories."""
        is_valid, categories, tags, error = parse_filter_string("@work,@personal,@work")
        assert is_valid is True
        assert categories == ["work", "personal"]  # duplicates removed
        assert tags == []
        assert error == ""
    
    def test_duplicate_tags(self):
        """Test parsing with duplicate tags."""
        is_valid, categories, tags, error = parse_filter_string("#urgent,#low,#urgent")
        assert is_valid is True
        assert categories == []
        assert tags == ["urgent", "low"]
        assert error == ""
    
    def test_case_normalization(self):
        """Test that categories and tags are normalized to lowercase."""
        is_valid, categories, tags, error = parse_filter_string("@Work,@PERSONAL,#Urgent,#LOW")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert tags == ["urgent", "low"]
        assert error == ""
    
    def test_categories_with_underscores_and_hyphens(self):
        """Test parsing categories with valid special characters."""
        is_valid, categories, tags, error = parse_filter_string("@work_project,@client-alpha")
        assert is_valid is True
        assert categories == ["work_project", "client-alpha"]
        assert tags == []
        assert error == ""
    
    def test_tags_with_underscores_and_hyphens(self):
        """Test parsing tags with valid special characters."""
        is_valid, categories, tags, error = parse_filter_string("#high_priority,#task-1")
        assert is_valid is True
        assert categories == []
        assert tags == ["high_priority", "task-1"]
        assert error == ""
    
    def test_categories_with_numbers(self):
        """Test parsing categories with numbers."""
        is_valid, categories, tags, error = parse_filter_string("@project2024,@team1")
        assert is_valid is True
        assert categories == ["project2024", "team1"]
        assert tags == []
        assert error == ""
    
    def test_tags_with_numbers(self):
        """Test parsing tags with numbers."""
        is_valid, categories, tags, error = parse_filter_string("#sprint3,#rev2")
        assert is_valid is True
        assert categories == []
        assert tags == ["sprint3", "rev2"]
        assert error == ""
    
    def test_missing_at_symbol(self):
        """Test error when @ symbol is missing for category."""
        is_valid, categories, tags, error = parse_filter_string("work,@personal")
        assert is_valid is False
        assert categories == ["personal"] # Should still parse valid @personal
        assert tags == []
        assert "Invalid filter item: 'work'" in error
    
    def test_missing_hash_symbol(self):
        """Test error when # symbol is missing for tag."""
        is_valid, categories, tags, error = parse_filter_string("@work,urgent")
        assert is_valid is False
        assert categories == ["work"] # Should still parse valid @work
        assert tags == []
        assert "Invalid filter item: 'urgent'" in error
    
    def test_mixed_valid_invalid(self):
        """Test error when mixing valid and invalid items."""
        is_valid, categories, tags, error = parse_filter_string("@work,urgent,#low,invalid_cat,@home")
        assert is_valid is False
        assert categories == ["work", "home"]
        assert tags == ["low"]
        assert "Invalid filter item: 'urgent'" in error
        assert "Invalid filter item: 'invalid_cat'" in error
    
    def test_invalid_characters_category(self):
        """Test error with invalid characters in category names."""
        is_valid, categories, tags, error = parse_filter_string("@work space")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid category format" in error
    
    def test_invalid_characters_tag(self):
        """Test error with invalid characters in tag names."""
        is_valid, categories, tags, error = parse_filter_string("#urgent!")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid tag format" in error
    
    def test_empty_category_name(self):
        """Test error with empty category name after @."""
        is_valid, categories, tags, error = parse_filter_string("@")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid category format" in error
    
    def test_empty_tag_name(self):
        """Test error with empty tag name after #."""
        is_valid, categories, tags, error = parse_filter_string("#")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid tag format" in error
    
    def test_special_characters_invalid_category(self):
        """Test error with special characters in category names."""
        is_valid, categories, tags, error = parse_filter_string("@work!")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid category format" in error
    
    def test_special_characters_invalid_tag(self):
        """Test error with special characters in tag names."""
        is_valid, categories, tags, error = parse_filter_string("#urgent@home")
        assert is_valid is False
        assert categories == []
        assert tags == []
        assert "Invalid tag format" in error


class TestFilterTasksByCategories:
    """Test the filter_tasks_by_tags_or_categories function."""
    
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
        result = filter_tasks_by_tags_or_categories(self.tasks, [], [])
        assert len(result) == 5
        assert result == self.tasks
    
    def test_single_category_filter(self):
        """Test filtering by single category."""
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["work"])
        assert len(result) == 3  # 3 tasks have @work
        
        # Check that correct tasks are returned
        task_texts = [t["task"] for t in result]
        assert "Work meeting @work" in task_texts
        assert "Mixed task @work @personal" in task_texts
        assert "Client work @client @work" in task_texts
    
    def test_multiple_category_filter(self):
        """Test filtering by multiple categories (OR logic)."""
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["work", "personal"])
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
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["nonexistent"])
        assert len(result) == 0
    
    def test_client_category_filter(self):
        """Test filtering by client category."""
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["client"])
        assert len(result) == 1
        assert result[0]["task"] == "Client work @client @work"
    
    def test_single_tag_filter(self):
        """Test filtering by single tag."""
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_tags=["urgent"])
        assert len(result) == 1
        assert result[0]["task"] == "Client work @client @work" # This is the only urgent task in setup
    
    def test_multiple_tag_filter(self):
        """Test filtering by multiple tags (OR logic)."""
        # Add another task with a #low tag for this test
        low_priority_task = {
            "task": "Low priority @other #low",
            "categories": ["other"],
            "tags": ["low"],
            "ts": "2025-05-30T16:00:00"
        }
        tasks_with_low = self.tasks + [low_priority_task]
        result = filter_tasks_by_tags_or_categories(tasks_with_low, filter_tags=["urgent", "low"])
        assert len(result) == 2
        task_texts = [t["task"] for t in result]
        assert "Client work @client @work" in task_texts # Urgent
        assert "Low priority @other #low" in task_texts # Low
    
    def test_combined_category_and_tag_filter(self):
        """Test filtering by category AND tag."""
        # Filter for tasks with @work AND #urgent
        result = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["work"], filter_tags=["urgent"])
        assert len(result) == 1
        assert result[0]["task"] == "Client work @client @work" 

        # Filter for @personal AND #nonexistent_tag
        result_no_match = filter_tasks_by_tags_or_categories(self.tasks, filter_categories=["personal"], filter_tags=["nonexistent"])
        assert len(result_no_match) == 0
    
    def test_case_insensitive_filtering(self):
        """Test that filtering is case insensitive for both categories and tags."""
        mixed_case_task_cat = {
            "task": "Mixed case @Work",
            "categories": ["work"], 
            "tags": [], "ts": ""
        }
        mixed_case_task_tag = {
            "task": "Mixed case #URGENT",
            "categories": [], 
            "tags": ["urgent"], "ts": ""
        }
        tasks_with_mixed = self.tasks + [mixed_case_task_cat, mixed_case_task_tag]
        
        result_cat = filter_tasks_by_tags_or_categories(tasks_with_mixed, filter_categories=["work"])
        # Expected: "Work meeting @work", "Mixed task @work @personal", "Client work @client @work", "Mixed case @Work"
        assert len(result_cat) == 4 

        result_tag = filter_tasks_by_tags_or_categories(tasks_with_mixed, filter_tags=["URGENT"])
        # Expected: "Client work @client @work", "Mixed case #URGENT"
        assert len(result_tag) == 2 
    
    def test_legacy_format_tasks(self):
        """Test filtering tasks in legacy string format."""
        legacy_tasks = [
            {"task": "Legacy work task @work #important"},
            {"task": "Legacy personal @personal #low"},
            {"task": "Legacy no category #urgent"}
        ]
        
        result_cat = filter_tasks_by_tags_or_categories(legacy_tasks, filter_categories=["work"])
        assert len(result_cat) == 1
        assert result_cat[0]["task"] == "Legacy work task @work #important"

        result_tag = filter_tasks_by_tags_or_categories(legacy_tasks, filter_tags=["urgent"])
        assert len(result_tag) == 1
        assert result_tag[0]["task"] == "Legacy no category #urgent"

        result_combined = filter_tasks_by_tags_or_categories(legacy_tasks, filter_categories=["personal"], filter_tags=["low"])
        assert len(result_combined) == 1
        assert result_combined[0]["task"] == "Legacy personal @personal #low"
    
    def test_very_old_format_tasks(self):
        """Test filtering very old format (just strings)."""
        old_tasks = [
            "Old work task @work #projectA",
            "Old personal @personal #projectB", 
            "Old no category #projectC"
        ]
        
        result_cat = filter_tasks_by_tags_or_categories(old_tasks, filter_categories=["work"])
        assert len(result_cat) == 1
        assert result_cat[0] == "Old work task @work #projectA"

        result_tag = filter_tasks_by_tags_or_categories(old_tasks, filter_tags=["projectB"])
        assert len(result_tag) == 1
        assert result_tag[0] == "Old personal @personal #projectB"

        result_combined = filter_tasks_by_tags_or_categories(old_tasks, filter_categories=["work"], filter_tags=["projectA"])
        assert len(result_combined) == 1
        assert result_combined[0] == "Old work task @work #projectA"
    
    def test_mixed_format_tasks(self):
        """Test filtering with mixed task formats."""
        mixed_tasks = [
            { 
                "task": "New format @work #alpha",
                "categories": ["work"],
                "tags": ["alpha"],
                "ts": "2025-05-30T10:00:00"
            },
            {"task": "Legacy format @personal #beta"},  
            "Very old format @client #gamma"  
        ]
        
        result_cat = filter_tasks_by_tags_or_categories(mixed_tasks, filter_categories=["work"])
        assert len(result_cat) == 1
        assert result_cat[0]["task"] == "New format @work #alpha"

        result_tag = filter_tasks_by_tags_or_categories(mixed_tasks, filter_tags=["beta"])
        assert len(result_tag) == 1
        assert result_tag[0]["task"] == "Legacy format @personal #beta"

        result_combined = filter_tasks_by_tags_or_categories(mixed_tasks, filter_categories=["client"], filter_tags=["gamma"])
        assert len(result_combined) == 1
        assert result_combined[0] == "Very old format @client #gamma"


class TestFilterSingleTaskByCategories:
    """Test the filter_single_task_by_tags_or_categories function."""
    
    def test_no_filter_returns_true(self):
        """Test that empty filter returns True."""
        task = {"task": "Any task", "categories": [], "tags": []}
        assert filter_single_task_by_tags_or_categories(task, [], []) is True
    
    def test_matching_category(self):
        """Test matching by category."""
        task = {"task": "Task @work", "categories": ["work"], "tags": []}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["work"]) is True
    
    def test_matching_tag(self):
        """Test matching by tag."""
        task = {"task": "Task #urgent", "categories": [], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent"]) is True

    def test_non_matching_category(self):
        """Test non-matching category."""
        task = {"task": "Task @work", "categories": ["work"], "tags": []}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["personal"]) is False

    def test_non_matching_tag(self):
        """Test non-matching tag."""
        task = {"task": "Task #urgent", "categories": [], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["low"]) is False
    
    def test_multiple_categories_task(self):
        """Test task with multiple categories, filter by one."""
        task = {"task": "Task @work @personal", "categories": ["work", "personal"], "tags": []}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["work"]) is True
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["personal"]) is True

    def test_multiple_tags_task(self):
        """Test task with multiple tags, filter by one."""
        task = {"task": "Task #urgent #low", "categories": [], "tags": ["urgent", "low"]}
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent"]) is True
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["low"]) is True
    
    def test_multiple_filter_categories(self):
        """Test filtering by multiple categories (OR logic)."""
        task = {"task": "Task @work", "categories": ["work"], "tags": []}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["work", "personal"]) is True

    def test_multiple_filter_tags(self):
        """Test filtering by multiple tags (OR logic)."""
        task = {"task": "Task #urgent", "categories": [], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_tags=["urgent", "low"]) is True

    def test_combined_category_and_tag_match(self):
        """Test matching by both category AND tag."""
        task = {"task": "Task @work #urgent", "categories": ["work"], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["work"], filter_tags=["urgent"]) is True

    def test_combined_category_no_tag_match(self):
        """Test category match but tag mismatch."""
        task = {"task": "Task @work #urgent", "categories": ["work"], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["work"], filter_tags=["low"]) is False

    def test_combined_tag_no_category_match(self):
        """Test tag match but category mismatch."""
        task = {"task": "Task @work #urgent", "categories": ["work"], "tags": ["urgent"]}
        assert filter_single_task_by_tags_or_categories(task, filter_categories=["personal"], filter_tags=["urgent"]) is False
    
    def test_legacy_format_task(self):
        """Test legacy format task (dict with 'task' string)."""
        task_cat = {"task": "Legacy @work"}
        assert filter_single_task_by_tags_or_categories(task_cat, filter_categories=["work"]) is True
        task_tag = {"task": "Legacy #urgent"}
        assert filter_single_task_by_tags_or_categories(task_tag, filter_tags=["urgent"]) is True
        task_both = {"task": "Legacy @work #urgent"}
        assert filter_single_task_by_tags_or_categories(task_both, filter_categories=["work"], filter_tags=["urgent"]) is True
    
    def test_string_format_task(self):
        """Test string format task."""
        task_cat = "String task @work"
        assert filter_single_task_by_tags_or_categories(task_cat, filter_categories=["work"]) is True
        task_tag = "String task #urgent"
        assert filter_single_task_by_tags_or_categories(task_tag, filter_tags=["urgent"]) is True
        task_both = "String task @work #urgent"
        assert filter_single_task_by_tags_or_categories(task_both, filter_categories=["work"], filter_tags=["urgent"]) is True


class TestStatusCommandFiltering:
    """Test status command with filtering (mocked storage)."""
    
    def test_status_with_filter(self, temp_storage, plain_mode, capsys):
        """Test status output when filtering by category."""
        data = {
            "2025-05-30": {
                "todo": {"task": "Active task @work #important", "categories": ["work"], "tags": ["important"]},
                "done": [
                    {"id": "d1", "task": {"task": "Done task 1 @work", "categories": ["work"], "tags": []}, "ts": "2025-05-30T10:00:00"},
                    {"id": "d2", "task": {"task": "Done task 2 @personal", "categories": ["personal"], "tags": []}, "ts": "2025-05-30T11:00:00"}
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data))
        
        args = Args(filter="@work", store=str(temp_storage), plain=True, func=cmd_status)
        
        with patch("tasker.today_key", return_value="2025-05-30"):
            cmd_status(args)
        
        captured = capsys.readouterr()
        assert "(filtered by: @work)" in captured.out
        assert "Active task @work #important" in captured.out
        assert "Done task 1 @work" in captured.out
        assert "Done task 2 @personal" not in captured.out

    def test_status_with_tag_filter(self, temp_storage, plain_mode, capsys):
        """Test status output when filtering by tag."""
        data = {
            "2025-05-30": {
                "todo": {"task": "Active task @work #important", "categories": ["work"], "tags": ["important"]},
                "done": [
                    {"id": "d1", "task": {"task": "Done task 1 @work #urgent", "categories": ["work"], "tags": ["urgent"]}, "ts": "2025-05-30T10:00:00"},
                    {"id": "d2", "task": {"task": "Done task 2 @personal #low", "categories": ["personal"], "tags": ["low"]}, "ts": "2025-05-30T11:00:00"}
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data))
        
        args = Args(filter="#urgent", store=str(temp_storage), plain=True, func=cmd_status)
        
        with patch("tasker.today_key", return_value="2025-05-30"):
            cmd_status(args)
        
        captured = capsys.readouterr()
        assert "(filtered by: #urgent)" in captured.out
        assert "No active task matches filter" in captured.out # Active is #important
        assert "Done task 1 @work #urgent" in captured.out
        assert "Done task 2 @personal #low" not in captured.out

    def test_status_with_combined_filter(self, temp_storage, plain_mode, capsys):
        """Test status output when filtering by category and tag."""
        data = {
            "2025-05-30": {
                "todo": {"task": "Active task @work #important", "categories": ["work"], "tags": ["important"]},
                "done": [
                    {"id": "d1", "task": {"task": "Done task 1 @work #urgent", "categories": ["work"], "tags": ["urgent"]}, "ts": "2025-05-30T10:00:00"},
                    {"id": "d2", "task": {"task": "Done task 2 @personal #urgent", "categories": ["personal"], "tags": ["urgent"]}, "ts": "2025-05-30T11:00:00"},
                    {"id": "d3", "task": {"task": "Done task 3 @work #low", "categories": ["work"], "tags": ["low"]}, "ts": "2025-05-30T12:00:00"}
                ]
            },
            "backlog": []
        }
        temp_storage.write_text(json.dumps(data))
        
        args = Args(filter="@work,#urgent", store=str(temp_storage), plain=True, func=cmd_status)
        
        with patch("tasker.today_key", return_value="2025-05-30"):
            cmd_status(args)
        
        captured = capsys.readouterr()
        assert "(filtered by: @work, #urgent)" in captured.out
        assert "No active task matches filter" in captured.out # Active is @work #important
        assert "Done task 1 @work #urgent" in captured.out
        assert "Done task 2 @personal #urgent" not in captured.out
        assert "Done task 3 @work #low" not in captured.out
    
    def test_status_no_matches(self, temp_storage, plain_mode, capsys):
        """Test status output when no tasks match filter."""
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
        args.store = str(temp_storage) # Ensure temp_storage is used
        args.plain = True # Explicitly set for consistent output testing
        
        with patch('tasker.STORE', temp_storage), \
             patch('tasker.today_key', return_value='2025-05-30'): # Patch STORE and today_key
            cmd_status(args)
        
        captured = capsys.readouterr()
        # Check specific parts of the output
        assert "(filtered by: @work)" in captured.out
        assert "No active task matches filter" in captured.out
        assert "No completed tasks match the filter" in captured.out


class TestBacklogCommandFiltering:
    """Test cmd_backlog with category filtering."""
    
    def test_backlog_list_with_filter(self, temp_storage, plain_mode, capsys):
        """Test backlog list command with category filter."""
        data = {
            "backlog": [
                {
                    "task": "Work backlog @work",
                    "categories": ["work"],
                    "tags": ["projectA"], # Added a tag for more distinct testing
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
                    "tags": ["urgent"], # Added a tag
                    "ts": "2025-05-30T12:00:00"
                }
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        args.store = str(temp_storage) # Ensure temp_storage is used
        args.plain = True # Explicitly set
        
        with patch('tasker.STORE', temp_storage): # Patch STORE
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog (filtered by: @work):" in captured.out
        assert "Work backlog @work #projectA" in captured.out # Task includes its own tags/cats
        assert "Client work @client @work #urgent" in captured.out
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
        args.store = str(temp_storage) # Ensure temp_storage is used
        args.plain = True # Explicitly set
        
        with patch('tasker.STORE', temp_storage): # Patch STORE
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        # Expect header then message
        assert "Backlog (filtered by: @work):" in captured.out
        assert "No backlog items match the filter." in captured.out
    
    def test_backlog_list_invalid_filter(self, temp_storage, plain_mode, capsys):
        """Test backlog list with invalid filter."""
        # No data setup needed as it should error out before loading
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "work"  # missing @
        args.store = str(temp_storage) # Still provide store, though may not be used
        args.plain = True # Explicitly set
        
        # Initializing temp_storage to an empty state
        temp_storage.write_text(json.dumps({"backlog": [], "2025-05-30": {"todo": None, "done": []}}), encoding='utf-8')

        with patch('tasker.STORE', temp_storage): # Patch STORE
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        # Updated parse_filter_string provides a more specific error message
        assert "Invalid filter item: 'work'. Must start with @ (category) or # (tag)." in captured.out
    
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
        args.store = str(temp_storage) # Ensure temp_storage is used
        args.plain = True # Explicitly set

        with patch('tasker.STORE', temp_storage): # Patch STORE
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
                # Legacy tasks are just strings in the "task" field of the list item for backlog
                # The filter_tasks_by_tags_or_categories will parse these strings
                {"task": "Legacy work @work #projectX", "ts": "2025-05-30T10:00:00"},
                {"task": "Legacy personal @personal #projectY", "ts": "2025-05-30T11:00:00"}
            ],
            "2025-05-30": {"todo": None, "done": []}
        }
        temp_storage.write_text(json.dumps(data), encoding='utf-8')
        
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        args.store = str(temp_storage) # Ensure temp_storage is used
        args.plain = True # Explicitly set

        with patch('tasker.STORE', temp_storage): # Patch STORE
            cmd_backlog(args)
        
        captured = capsys.readouterr()
        assert "Backlog (filtered by: @work):" in captured.out
        assert "Legacy work @work #projectX" in captured.out
        assert "Legacy personal @personal #projectY" not in captured.out


class TestFilteringEdgeCases:
    """Test edge cases for filter string parsing."""

    def test_empty_backlog_with_filter(self, temp_storage, plain_mode, capsys):
        """Test filtering empty backlog."""
        args = MagicMock()
        args.subcmd = "list"
        args.filter = "@work"
        args.store = str(temp_storage) # Ensure cmd_backlog uses temp_storage


        # Ensure the temp_storage is initialized with an empty backlog for this test
        initial_data = {"backlog": [], "2025-05-30": {"todo": None, "done": []}}
        temp_storage.write_text(json.dumps(initial_data), encoding='utf-8')


        with patch('tasker.STORE', temp_storage): # Patch STORE for tasker.load()
            cmd_backlog(args)

        captured = capsys.readouterr()
        assert "Backlog (filtered by: @work):" in captured.out # Header should still show
        assert "No backlog items match the filter." in captured.out

    def test_whitespace_only_filter(self):
        """Test filter with only whitespace."""
        is_valid, categories, tags, error = parse_filter_string("   ")
        assert is_valid is True
        assert categories == []
        assert tags == []
        assert error == ""

    def test_comma_only_filter(self):
        """Test filter with only commas."""
        is_valid, categories, tags, error = parse_filter_string(",,,")
        assert is_valid is True # Commas only should result in no filters
        assert categories == []
        assert tags == []
        assert error == ""

    def test_mixed_whitespace_and_commas(self):
        """Test filter with mixed whitespace and commas."""
        is_valid, categories, tags, error = parse_filter_string(" , @work , , @personal , ")
        assert is_valid is True
        assert categories == ["work", "personal"]
        assert tags == []
        assert error == ""

    def test_filter_with_at_but_no_name(self):
        """Test filter with @ but no category name."""
        # Behavior of "bare" @ or # depends on parse_filter_string implementation.
        # Assuming it's treated as an invalid item.
        is_valid, categories, tags, error = parse_filter_string("@,@work")
        assert is_valid is False
        assert categories == ["work"] # Should still parse valid items
        assert tags == []
        assert "Invalid category format: '@'" in error

    def test_filter_with_hash_but_no_name(self):
        """Test filter with # but no tag name."""
        is_valid, categories, tags, error = parse_filter_string("#,#urgent")
        assert is_valid is False
        assert categories == []
        assert tags == ["urgent"] # Should still parse valid items
        assert "Invalid tag format: '#'" in error

    def test_filter_with_mixed_bare_symbols(self):
        """Test filter with mixed bare symbols and valid items."""
        is_valid, categories, tags, error = parse_filter_string("@,@work,#,#urgent")
        assert is_valid is False
        assert categories == ["work"]
        assert tags == ["urgent"]
        assert "Invalid category format: '@'" in error or "Invalid tag format: '#'" in error # Error for one of them


@pytest.fixture
def temp_storage(tmp_path):
    storage_file = tmp_path / "test_storage.json"
    storage_file.write_text("{}") # Initialize with empty JSON
    return storage_file

@pytest.fixture
def plain_mode(monkeypatch):
    monkeypatch.setattr("tasker.USE_PLAIN", True)

# Helper to create a mock args object
Args = lambda **kwargs: type("Args", (), kwargs)
